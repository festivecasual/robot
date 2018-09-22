import busio
import sys
import time

sys.path.append('./contrib')
from adafruit_motor import servo
from board import SCL, SDA
from adafruit_pca9685 import PCA9685

pca = PCA9685(busio.I2C(SCL, SDA))
pca.frequency = 50

servo0 = servo.Servo(pca.channels[0], min_pulse=580, max_pulse=2480)
servo1 = servo.Servo(pca.channels[1], min_pulse=750, max_pulse=2350)

servo0.angle = 90
servo1.angle = 90

time.sleep(1)

for i in range(90, 180):
    servo0.angle = i
    servo1.angle = i
    time.sleep(0.01)

for i in range(180, 0, -1):
    servo0.angle = i
    servo1.angle = i
    time.sleep(0.01)

servo0.angle = 0
servo1.angle = 180

time.sleep(1)

servo0.angle = 180
servo1.angle = 0

pca.deinit()

