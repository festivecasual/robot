# Joystick access methods sourced heavily from https://gist.github.com/rdb/8864666 (Public Domain per the Unilicense)

import array
import struct
from fcntl import ioctl
import sys

import serial

import joystick


# Initialize serial port for motor driver
driver = serial.Serial('/dev/ttyS0', 9600)
driver.write(b'E\r\n')

# Initialize joystick connection
jsdev = open('/dev/input/js0', 'rb')

# Device name
buf = array.array('B', [0] * 64)
ioctl(jsdev, 0x80006a13 + (0x10000 * len(buf)), buf)  # JSIOCGNAME(len)
js_name = buf.tobytes().decode('ascii')

# Number of axes
buf = array.array('B', [0])
ioctl(jsdev, 0x80016a11, buf)  # JSIOCGAXES
num_axes = buf[0]

# Number of buttons
buf = array.array('B', [0])
ioctl(jsdev, 0x80016a12, buf)  # JSIOCGBUTTONS
num_buttons = buf[0]

print('Connected to joystick: %s (%d axes, %d buttons)' % (js_name, num_axes, num_buttons))

# Axis map
axis_map = []
axis_states = {}
buf = array.array('B', [0] * 0x40)
ioctl(jsdev, 0x80406a32, buf)  # JSIOCGAXMAP
for axis in buf[:num_axes]:
    axis_name = joystick.axis_names.get(axis, 'unknown(0x%02x)' % axis)
    axis_map.append(axis_name)
    axis_states[axis_name] = 0.0

# Button map
button_map = []
button_states = {}
buf = array.array('H', [0] * 200)
ioctl(jsdev, 0x80406a34, buf)  # JSIOCGBTNMAP
for btn in buf[:num_buttons]:
    btn_name = joystick.button_names.get(btn, 'unknown(0x%03x)' % btn)
    button_map.append(btn_name)
    button_states[btn_name] = 0

while True:
    evbuf = jsdev.read(8)
    if evbuf:
        time, value, type, number = struct.unpack('IhBB', evbuf)
        if type & 0x80:
            pass
        if type & 0x01:
            button = button_map[number]
            if button:
                button_states[button] = value
        if type & 0x02:
            axis = axis_map[number]
            if axis:
                fvalue = value / 32767.0
                axis_states[axis] = fvalue
            if axis == 'x' or axis == 'y':
                # Motor solutions taken from: http://home.kendra.com/mauser/joystick.html
                jx = -1 * axis_states['x']
                jy = -1 * axis_states['y']
                v = jy * (2 - abs(jx))
                w = jx * (2 - abs(jy))
                R = (v + w) / 2.0
                L = (v - w) / 2.0
                command = 'M1%s%d\r\nM0%s%d\r\n' % ('F' if R > 0 else 'R', abs(int(100 * R)), 'F' if L > 0 else 'R', abs(int(100 * L)))
                driver.write(command.encode('ascii'))

