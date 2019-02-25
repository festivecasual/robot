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


GPIO_MOTOR = 4
GPIO_LEFT_EYE = 24
GPIO_RIGHT_EYE = 23
GPIO_LEFT_ANTENNA = 5
GPIO_RIGHT_ANTENNA = 6

class Robot:
    def __init__(self):
        # Set up GPIO for BCM pin number references
        GPIO.setmode(GPIO.BCM)

        # Enable power to the motor driver board
        GPIO.setup(GPIO_MOTOR, GPIO.OUT, initial=GPIO.LOW)
        GPIO.output(GPIO_MOTOR, GPIO.HIGH)

        # Initialize "head lights" (antennae and eyes)
        GPIO.setup(GPIO_LEFT_EYE, GPIO.OUT, initial=GPIO.LOW)
        GPIO.setup(GPIO_RIGHT_EYE, GPIO.OUT, initial=GPIO.LOW)
        GPIO.setup(GPIO_LEFT_ANTENNA, GPIO.OUT, initial=GPIO.LOW)
        GPIO.setup(GPIO_RIGHT_ANTENNA, GPIO.OUT, initial=GPIO.LOW)

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

        # Initialize the master action queue
        self.action_queue = asyncio.Queue()

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

    def enqueue(self, action):
        self.action_queue.put_nowait(action)

    async def consume_queue(self):
        while True:
            action = await self.action_queue.get()
            await action
            self.action_queue.task_done()

    async def move_arm(self, arm_name, angle):
        arm = self.left_arm if arm_name == 'left' else self.right_arm
        while abs(arm.angle - angle) > 1:
            arm.angle += 1 if angle > arm.angle else -1
            await asyncio.sleep(0.01)

    async def set_eye_state(self, eye, state):
        GPIO.output(GPIO_RIGHT_EYE if eye == 'right' else GPIO_LEFT_EYE, state)

    async def set_antenna_state(self, antenna, state):
        GPIO.output(GPIO_RIGHT_ANTENNA if antenna == 'right' else GPIO_LEFT_ANTENNA, state)

    def shutdown(self):
        self.pca.deinit()
        GPIO.output(GPIO_MOTOR, GPIO.LOW)
        GPIO.cleanup()


if __name__ == '__main__':
    # Get the main async event loop
    loop = asyncio.get_event_loop()

    # Initialize the robot
    robot = Robot()

    # Start the telnet control server
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

