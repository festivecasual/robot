import asyncio
import re
import sys

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


def interpret_float(text, ensure_positive=False):
    res = float(text)
    if ensure_positive and res < 0:
        raise ValueError('Negative values are not allowed')
    return res


move_arm = re.compile('move (left|right) arm (up|down|out|\d+)')
move_arms = re.compile('move both arms (up|down|out|\d+)')

set_eye = re.compile('set (left|right) eye (on|off)')
set_both_eyes = re.compile('set both eyes (on|off)')
set_antenna = re.compile('set (left|right) (ear|antenna) (on|off)')
set_both_antennae = re.compile('set both (ears|antennas|antennae) (on|off)')

say = re.compile('say (.+)')

go = re.compile('go')

wait = re.compile('wait (.+)')


def parse(command, robot):
    match = move_arm.fullmatch(command)
    if match:
        return [robot.move_arm(match.group(1), resolve_angle(match.group(2)))]

    match = move_arms.fullmatch(command)
    if match:
        return [
                robot.move_arm('left', resolve_angle(match.group(1))),
                robot.move_arm('right', resolve_angle(match.group(1)))
                ]

    match = set_eye.fullmatch(command)
    if match:
        return [robot.set_eye_state(match.group(1), GPIO.HIGH if match.group(2) == 'on' else GPIO.LOW)]

    match = set_both_eyes.fullmatch(command)
    if match:
        return [
                robot.set_eye_state('left', GPIO.HIGH if match.group(1) == 'on' else GPIO.LOW),
                robot.set_eye_state('right', GPIO.HIGH if match.group(1) == 'on' else GPIO.LOW)
                ]

    match = set_antenna.fullmatch(command)
    if match:
        return [robot.set_antenna_state(match.group(1), GPIO.HIGH if match.group(3) == 'on' else GPIO.LOW)]

    match = set_both_antennae.fullmatch(command)
    if match:
        return [
                robot.set_antenna_state('left', GPIO.HIGH if match.group(2) == 'on' else GPIO.LOW),
                robot.set_antenna_state('right', GPIO.HIGH if match.group(2) == 'on' else GPIO.LOW)
                ]

    match = say.fullmatch(command)
    if match:
        return [robot.say(match.group(1))]

    match = go.fullmatch(command)
    if match:
        return [robot.move(0, 1, 3)]

    match = wait.fullmatch(command)
    if match:
        try:
            return [asyncio.sleep(interpret_float(match.group(1), ensure_positive=True))]
        except ValueError:
            raise SyntaxError('Wait time is not valid')

    raise SyntaxError('Unable to parse command')


def process_program(lines, robot):
    action_list = []
    current_line = 0
    inside_group = False

    while lines:
        current_line += 1
        command = lines.pop(0)

        if command == '[':
            if inside_group:
                print('Error at line #%d: Nested groups are not allowed' % current_line)
                sys.exit(-1)
            inside_group = True
            action_list.append([])
        elif command == ']':
            if not inside_group:
                print('Error at line #%d: ] without matching [' % current_line)
                sys.exit(-1)
            inside_group = False
        elif command == '':
            pass
        else:
            try:
                action = parse(command, robot)
            except SyntaxError as e:
                print('Error at line #%d: %s' % (current_line, str(e)))
                sys.exit(-1)
            if not inside_group:
                action_list.append(action)
            else:
                action_list[-1].extend(action)

    if inside_group:
        print('Warning: Unclosed group')

    return action_list

