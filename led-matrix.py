#!/usr/bin/env python3
# Script to generate the mapping of LEDs to the CS and SW registers of the
# IS31FL3741A controller.
#
# The output looks like:
# (0x00, 0), // x:1, y:1, sw:1, cs:1, id:1
# (0x1e, 0), // x:2, y:1, sw:2, cs:1, id:2
# [...]

import math

import serial

from pynput.keyboard import Key, Listener

from dataclasses import dataclass

WIDTH = 9
HEIGHT = 34


@dataclass
class Led:
    id: int
    x: int
    y: int
    # Values from 1 to 9
    sw: int
    # Values from 1 to 34
    cs: int

    def led_register(self):
        # See the IS31FL3741A for how the data pages are separated
        if self.cs <= 30 and self.sw >= 7:
            page = 1
            register = self.cs - 1 + (self.sw-7) * 30
        if self.cs <= 30 and self.sw <= 6:
            page = 0
            register = self.cs - 1 + (self.sw-1) * 30
        if self.cs >= 31:
            page = 1
            register = 0x5A + self.cs - 31 + (self.sw-1) * 9
        return (register, page)

    def __lt__(self, other):
        if self.y == other.y:
            return self.x < other.x
        else:
            return self.y < other.y


def get_leds():
    leds = []

    # Generate LED mapping as how they are mapped in the Framework Laptop 16 LED Matrix Module

    # First down and then right
    # CS1 through CS4
    for cs in range(1, 5):
        for sw in range(1, WIDTH):
            leds.append(Led(id=WIDTH * (cs-1) + sw, x=sw, y=cs, sw=sw, cs=cs))

    # First right and then down
    # CS5 through CS7
    base_cs = 4
    base_id = WIDTH * base_cs
    for cs in range(1, 5):
        for sw in range(1, WIDTH):
            leds.append(Led(id=base_id + 4 * (sw-1) + cs, x=sw,
                        y=cs+base_cs, sw=sw, cs=cs+base_cs))
    base_id+=5

    # First right and then down
    # CS9 through CS16
    base_cs = 8
    base_id = WIDTH * base_cs
    for cs in range(1, 9):
        for sw in range(1, WIDTH):
            leds.append(Led(id=base_id + 8 * (sw-1) + cs, x=sw,
                        y=cs+base_cs, sw=sw, cs=cs+base_cs))
    base_id+=9

    # First right and then down
    # CS17 through CS32
    base_cs = 16
    base_id = WIDTH * base_cs
    for cs in range(1, 17):
        for sw in range(1, WIDTH):
            leds.append(Led(id=base_id + 16 * (sw-1) + cs, x=sw,
                        y=cs+base_cs, sw=sw, cs=cs+base_cs))
    base_id+=17

    # First down and then right
    # CS33 through CS34
    base_cs = 32
    base_id = WIDTH * base_cs
    for cs in range(1, 3):
        for sw in range(1, WIDTH):
            leds.append(Led(id=base_id + 9 * (cs-1) + sw, x=sw,
                        y=cs+base_cs, sw=sw, cs=cs+base_cs))
    base_id+=3

    # DVT2 Last column
    five_cycle=[36, 37, 38, 39, 35]
    four_cycle=[36, 37, 38, 35]
    for y in range(1, HEIGHT+1):
        ledid = WIDTH*y
        if y >= 5:
            ledid = 69 + y%5
        if y >= 9:
            ledid = 137 + y%9
        if y >= 17:
            ledid = 273 + y%17
        if y >= 33:
            ledid = WIDTH*y

        if y <= 10:
            leds.append(Led(id=ledid, x=WIDTH, y=y, sw=math.ceil(y/5), cs=five_cycle[(y-1)%5]))
        else:
            sw = 2 + math.ceil((y-10)/4)
            cs = four_cycle[(y-10-1)%4]
            leds.append(Led(id=ledid, x=WIDTH, y=y, sw=sw, cs=cs))

    return leds


def main():
    leds = get_leds()
    # Needs to be sorted according to x and y
    leds.sort()


    debug = False

    for led in leds:
        (register, page) = led.led_register()
        if debug:
            print(led, "(0x{:02x}, {})".format(register, page))
        else:
            print("(0x{:02x}, {}), // x:{:2d}, y:{:2d}, sw:{:2d}, cs:{:2d}, id:{:3d}".format(
                register, page, led.x, led.y, led.sw, led.cs, led.id))
    # print_led(leds, 0, 30)

# For debugging


def get_led(leds, x, y):
    return leds[x + y * WIDTH]


# For debugging
def print_led(leds, x, y):
    led = get_led(leds, x, y)
    (register, page) = led.led_register()
    print(led, "(0x{:02x}, {})".format(register, page))

def send_command(command_id, parameters, with_response=False):
  with serial.Serial("/dev/ttyACM0", 115200) as s:
      s.write([0x32, 0xAC, command_id] + parameters)

      if with_response:
          res = s.read(32)
          return res

if __name__ == "__main__":
    main()


    send_command(0x03, [True])
    res = send_command(0x03, [], with_response=True)
    print(f"Is currently sleeping: {bool(res[0])}")

    
    print("Start snake")
    res = send_command(0x10, [0])
    print("Press arrow keys. Press 'esc' to quit.")


def on_press(key):
    print(f"Pressed key: {key}")
    try:
        if ( key.char.lower() == 'w'):
            send_command(0x11, [0])
        elif (  key.char.lower() == 's'):
            send_command(0x11, [1])
        elif ( key.char.lower() == 'a'):
            send_command(0x11, [2])
        elif ( key.char.lower() == 'd'):
            send_command(0x11, [3])
    except AttributeError:
        if ( key == Key.up) :
            send_command(0x11, [0])
        elif (key == Key.down) :
            send_command(0x11, [1])
        elif ( key == Key.left) :
            send_command(0x11, [2])
        elif (key == Key.right) :
            send_command(0x11, [3])
        pass

def on_release(key):
    if key == Key.esc:
        print("Exiting...")
        return False  # Stop the listener

# Start listening for key presses
with Listener(on_press=on_press, on_release=on_release) as listener:
    listener.join()