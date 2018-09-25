from adafruit_motor.servo import Servo

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

