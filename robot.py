import sys
import asyncio

import RPi.GPIO as GPIO
import serial

sys.path.append('./contrib')
import busio
from adafruit_motor.servo import Servo
from board import SCL, SDA
from adafruit_pca9685 import PCA9685

from joystick import Joystick
from servo import InvertedServo
from server import ControlServer


class Robot:
    def __init__(self):
        # Set up GPIO for BCM pin number references
        GPIO.setmode(GPIO.BCM)

        # Enable power to the motor driver board
        GPIO.setup(4, GPIO.OUT, initial=GPIO.LOW)
        GPIO.output(4, GPIO.HIGH)

        # Initialize serial port for motor driver
        self.driver = serial.Serial('/dev/ttyS0', 9600)

        # Initialize the PCA9685 servo controller
        self.pca = PCA9685(busio.I2C(SCL, SDA))
        self.pca.frequency = 50

        # Initialize the arm controls
        self.left_arm = Servo(self.pca.channels[0], min_pulse=580, max_pulse=2480)
        self.right_arm = InvertedServo(self.pca.channels[1], min_pulse=750, max_pulse=2350)
        self.left_arm.angle = 180
        self.right_arm.angle = 180

        # Initialize the master command queue
        self.cmd_queue = asyncio.Queue()

    def locomote(self, x_speed, y_speed):
        if x_speed or y_speed:
            # At least one of the x-y axes is active, let's send a motor speed command and enable the motors

            # Motor solutions taken from: http://home.kendra.com/mauser/joystick.html
            v = y_speed * (2 - abs(x_speed))
            w = x_speed * (2 - abs(y_speed))
            R = (v + w) / 2.0
            command = 'M0%s%d\r\nM1%s%d\r\nE\r\n' % (
                    'F' if R > 0 else 'R',
                    abs(int(100 * R)),
                    'F' if L > 0 else 'R',
                    abs(int(100 * L)))
            self.driver.write(command.encode('ascii'))
        else:
            # No movement axes are active, disable motors
            self.driver.write('D\r\n'.encode('ascii')) 

    def enqueue(self, command, reply_to):
        self.cmd_queue.put_nowait((command, reply_to))

    async def consume_queue(self):
        while True:
            command, reply_to = await self.cmd_queue.get()
            print('Consuming command:', command)

            verb, _, tail = command.partition(' ')
            if verb == 'move':
                rest = tail.split()
                if rest[2] == 'up':
                    angle = 0
                elif rest[2] == 'down':
                    angle = 180
                elif rest[2] == 'out':
                    angle = 90
                else:
                    reply_to.write(('Bad command: ' + command).encode('ascii'))
                    continue
                if rest[0] == 'left':
                    while abs(self.left_arm.angle - angle) > 1:
                        self.left_arm.angle += 1 if angle > self.left_arm.angle else -1
                        await asyncio.sleep(0.01)
                elif rest[0] == 'right':
                    while abs(self.right_arm.angle - angle) > 1:
                        self.right_arm.angle += 1 if angle > self.right_arm.angle else -1
                        await asyncio.sleep(0.01)
            else:
                reply_to.write(('Bad command: ' + command).encode('ascii'))

            self.cmd_queue.task_done()

    def shutdown(self):
        self.pca.deinit()
        GPIO.output(4, GPIO.LOW)
        GPIO.cleanup()


if __name__ == '__main__':
    # Get the main async event loop
    loop = asyncio.get_event_loop()

    # Initialize the robot
    robot = Robot()

    # Start the telnet command server
    control_server = ControlServer(robot)

    # Define the mechanism for attaching joystick axis events to robot motion
    def joystick_movement(js, axis, value):
        robot.locomote(js.axis_states['x'], js.axis_states['y'])

    # Initialize the joystick
    joystick = Joystick()
    joystick.register(loop)
    joystick.add_axis_callback('x', joystick_movement)
    joystick.add_axis_callback('y', joystick_movement)

    # Initialize the robot's main command processing loop
    consumer = asyncio.ensure_future(robot.consume_queue())
    try:
        loop.run_forever()
    except KeyboardInterrupt:
        print()
        print('Shutting down...')
        async def loop_shutdown():
            consumer.cancel()
        loop.run_until_complete(loop_shutdown())
    finally:
        loop.close()
        robot.shutdown()

