# Joystick access methods sourced heavily from https://gist.github.com/rdb/8864666 (Public Domain per the Unilicense)

import array
import struct
from fcntl import ioctl


axis_names = {
    0x00 : 'x',
    0x01 : 'y',
    0x02 : 'z',
    0x03 : 'rx',
    0x04 : 'ry',
    0x05 : 'rz',
    0x06 : 'trottle',
    0x07 : 'rudder',
    0x08 : 'wheel',
    0x09 : 'gas',
    0x0a : 'brake',
    0x10 : 'hat0x',
    0x11 : 'hat0y',
    0x12 : 'hat1x',
    0x13 : 'hat1y',
    0x14 : 'hat2x',
    0x15 : 'hat2y',
    0x16 : 'hat3x',
    0x17 : 'hat3y',
    0x18 : 'pressure',
    0x19 : 'distance',
    0x1a : 'tilt_x',
    0x1b : 'tilt_y',
    0x1c : 'tool_width',
    0x20 : 'volume',
    0x28 : 'misc',
}

button_names = {
    0x120 : 'trigger',
    0x121 : 'thumb',
    0x122 : 'thumb2',
    0x123 : 'top',
    0x124 : 'top2',
    0x125 : 'pinkie',
    0x126 : 'base',
    0x127 : 'base2',
    0x128 : 'base3',
    0x129 : 'base4',
    0x12a : 'base5',
    0x12b : 'base6',
    0x12f : 'dead',
    0x130 : 'b1',  # a
    0x131 : 'b2',  # b
    0x132 : 'b3',  # c
    0x133 : 'b4',  # x
    0x134 : 'lb',  # y
    0x135 : 'rb',  # z
    0x136 : 'lt',  # tl
    0x137 : 'rt',  # tr
    0x138 : 'start',  # tl2
    0x139 : 'select',  # tr2
    0x13a : 'ls',  # select
    0x13b : 'rs',  # start
    0x13c : 'mode',
    0x13d : 'thumbl',
    0x13e : 'thumbr',

    0x220 : 'dpad_up',
    0x221 : 'dpad_down',
    0x222 : 'dpad_left',
    0x223 : 'dpad_right',

    # XBox 360 controller uses these codes.
    0x2c0 : 'dpad_left',
    0x2c1 : 'dpad_right',
    0x2c2 : 'dpad_up',
    0x2c3 : 'dpad_down',
}

class Joystick(object):
    def __init__(self, device='/dev/input/js0'):
        self.dev = open(device, 'rb')

        # Device name
        buf = array.array('B', [0] * 64)
        ioctl(self.dev, 0x80006a13 + (0x10000 * len(buf)), buf)  # JSIOCGNAME(len)
        self.name = buf.tobytes().decode('ascii')

        # Number of axes
        buf = array.array('B', [0])
        ioctl(self.dev, 0x80016a11, buf)  # JSIOCGAXES
        self.num_axes = buf[0]

        # Number of buttons
        buf = array.array('B', [0])
        ioctl(self.dev, 0x80016a12, buf)  # JSIOCGBUTTONS
        self.num_buttons = buf[0]

        # Axis map
        self.axis_map = []
        self.axis_states = {}
        buf = array.array('B', [0] * 0x40)
        ioctl(self.dev, 0x80406a32, buf)  # JSIOCGAXMAP
        for axis in buf[:self.num_axes]:
            axis_name = axis_names.get(axis, 'unknown(0x%02x)' % axis)
            self.axis_map.append(axis_name)
            self.axis_states[axis_name] = 0.0

        # Button map
        self.button_map = []
        self.button_states = {}
        buf = array.array('H', [0] * 200)
        ioctl(self.dev, 0x80406a34, buf)  # JSIOCGBTNMAP
        for btn in buf[:self.num_buttons]:
            btn_name = button_names.get(btn, 'unknown(0x%03x)' % btn)
            self.button_map.append(btn_name)
            self.button_states[btn_name] = 0

