import sys
import time

sys.path.append('./contrib')
import busio
from adafruit_motor.servo import Servo
from board import SCL, SDA
from adafruit_pca9685 import PCA9685


class InvertedServo(Servo):
    def __init__(self, pwm_out, actuation_range=180, min_pulse=750, max_pulse=2250):
        super().__init__(pwm_out, actuation_range=actuation_range, min_pulse=min_pulse, max_pulse=max_pulse)

    _angle = Servo.angle

    @property
    def angle(self):
        return 180 - self._angle

    @angle.setter
    def angle(self, value):
        self._angle = 180 - value


pca = PCA9685(busio.I2C(SCL, SDA))
pca.frequency = 50

servo0 = Servo(pca.channels[0], min_pulse=580, max_pulse=2480)
servo1 = InvertedServo(pca.channels[1], min_pulse=750, max_pulse=2350)

servo0.angle = servo1.angle = 90

time.sleep(1)

for i in range(90, 180):
    servo0.angle = servo1.angle = i
    time.sleep(0.01)

for i in range(180, 0, -1):
    servo0.angle = servo1.angle = i
    time.sleep(0.01)

servo0.angle = servo1.angle = 0

time.sleep(1)

servo0.angle = servo1.angle = 180

pca.deinit()

