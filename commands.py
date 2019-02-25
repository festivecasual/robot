import asyncio
import re

import RPi.GPIO as GPIO


def resolve_angle(text):
    if text == 'up':
        return 0
    elif text == 'down':
        return 180
    elif text == 'out':
        return 90
    elif 0 <= int(text) <= 180:
        return int(text)
    else:
        raise SyntaxError('Angle must be between 0 and 180, inclusive.')


move_arm = re.compile('move (left|right) arm (up|down|out|\d+)')
move_arms = re.compile('move both arms (up|down|out|\d+)')

set_eye = re.compile('set (left|right) eye (on|off)')
set_both_eyes = re.compile('set both eyes (on|off)')
set_antenna = re.compile('set (left|right) (ear|antenna) (on|off)')
set_both_antennae = re.compile('set both (ears|antennas|antennae) (on|off)')

def parse(command, robot):
    match = move_arm.fullmatch(command)
    if match:
        return robot.move_arm(match.group(1), resolve_angle(match.group(2)))

    match = move_arms.fullmatch(command)
    if match:
        return asyncio.gather(
                robot.move_arm('left', resolve_angle(match.group(1))),
                robot.move_arm('right', resolve_angle(match.group(1)))
                )

    match = set_eye.fullmatch(command)
    if match:
        return robot.set_eye_state(match.group(1), GPIO.HIGH if match.group(2) == 'on' else GPIO.LOW)

    match = set_both_eyes.fullmatch(command)
    if match:
        return asyncio.gather(
                robot.set_eye_state('left', GPIO.HIGH if match.group(1) == 'on' else GPIO.LOW),
                robot.set_eye_state('right', GPIO.HIGH if match.group(1) == 'on' else GPIO.LOW)
                )

    match = set_antenna.fullmatch(command)
    if match:
        return robot.set_antenna_state(match.group(1), GPIO.HIGH if match.group(3) == 'on' else GPIO.LOW)

    match = set_both_antennae.fullmatch(command)
    if match:
        return asyncio.gather(
                robot.set_antenna_state('left', GPIO.HIGH if match.group(2) == 'on' else GPIO.LOW),
                robot.set_antenna_state('right', GPIO.HIGH if match.group(2) == 'on' else GPIO.LOW)
                )

    raise SyntaxError('Unable to parse command')

