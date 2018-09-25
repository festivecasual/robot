import sys
import asyncio
import serial
import RPi.GPIO as GPIO

sys.path.append('./contrib')
import busio
from adafruit_motor.servo import Servo
from board import SCL, SDA
from adafruit_pca9685 import PCA9685

from joystick import Joystick
from servo import InvertedServo


# Initialize the master command queue
cmd_queue = asyncio.Queue()


async def handle_socket(reader, writer):
    writer.write(b'>> ')

    while True:
        line = await reader.readline()
        if line == b'':
            break
        input = line.decode('ascii').strip()
        cmd_queue.put_nowait((input, writer))
        print('Queued:', input)
        writer.write(b'>> ')


# Set up GPIO for BCM pin number references
GPIO.setmode(GPIO.BCM)

# Enable power to the motor driver board
GPIO.setup(4, GPIO.OUT, initial=GPIO.LOW)
GPIO.output(4, GPIO.HIGH)

# Initialize serial port for motor driver
driver = serial.Serial('/dev/ttyS0', 9600)
driver.write(b'M0F0\r\nM1F0\r\n')
driver.write(b'E\r\n')

# Initialize the joystick
joystick = Joystick()

# Initialize the PCA9685 servo controller
pca = PCA9685(busio.I2C(SCL, SDA))
pca.frequency = 50

# Initialize the arm controls
left_arm = Servo(pca.channels[0], min_pulse=580, max_pulse=2480)
right_arm = InvertedServo(pca.channels[1], min_pulse=750, max_pulse=2350)
left_arm.angle = 180
right_arm.angle = 180

loop = asyncio.get_event_loop()

coro = asyncio.start_server(handle_socket, port=5656)
loop.run_until_complete(coro)


async def consume_queue():
    while True:
        cmd, reply = await cmd_queue.get()
        print('Consuming command:', cmd)

        verb, _, tail = cmd.partition(' ')
        if verb == 'move':
            rest = tail.split()
            if rest[2] == 'up':
                angle = 0
            elif rest[2] == 'down':
                angle = 180
            elif rest[2] == 'out':
                angle = 90
            else:
                reply.write(b'Bad command:', cmd)
                continue
            if rest[0] == 'left':
                while abs(left_arm.angle - angle) > 1:
                    left_arm.angle += 1 if angle > left_arm.angle else -1
                    await asyncio.sleep(0.01)
            elif rest[0] == 'right':
                while abs(right_arm.angle - angle) > 1:
                    right_arm.angle += 1 if angle > right_arm.angle else -1
                    await asyncio.sleep(0.01)
            else:
                reply.write(b'Bad command:', cmd)
                continue

        cmd_queue.task_done()


try:
    consumer = asyncio.ensure_future(consume_queue())
    loop.run_forever()
except KeyboardInterrupt:
    consumer.cancel()

pca.deinit()
GPIO.output(4, GPIO.LOW)
GPIO.cleanup()

