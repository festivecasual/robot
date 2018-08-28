import array
from fcntl import ioctl


JOYSTICK = '/dev/input/js0'

jsdev = open(JOYSTICK, 'rb')

# Device name
buf = array.array('B', [0] * 64)
ioctl(jsdev, 0x80006a13 + (0x10000 * len(buf)), buf)  # JSIOCGNAME(len)
js_name = buf.tobytes().decode('ascii')
print('Device name: %s' % js_name)

