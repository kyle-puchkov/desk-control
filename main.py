# ============= LIBRARIES =============
import board
import digitalio
import usb_hid
from adafruit_hid.keyboard import Keyboard
from adafruit_hid.keycode import Keycode
import time

print("Initializing...")

# =============== File imports ==============
print("Reading config...")

polling_rate_hz = 100

# ========== GLOBAL VARIABLES =========
print("Creating global variables...")

counter = 0



# ================ PINS ===============
print("Setting up pins...")

kbd = Keyboard(usb_hid.devices)

led = digitalio.DigitalInOut(board.LED)
led.direction = digitalio.Direction.OUTPUT


mic_select_switch = digitalio.DigitalInOut(board.GP2)
mic_select_switch.direction = digitalio.Direction.INPUT
mic_select_switch.pull = digitalio.Pull.UP


mics_mute_switch = digitalio.DigitalInOut(board.GP3)
mics_mute_switch.direction = digitalio.Direction.INPUT
mics_mute_switch.pull = digitalio.Pull.UP



# =============== STATES ==============
print("Setting input states...")

mic_select_switch_state = mic_select_switch.value
mics_mute_switch_state = mics_mute_switch.value



# ============== FUNCTIONS ============
print("Defining functions...")

def blink_every_second():
    global counter
    counter += 1
    if counter % 100 == 0:
        led.value = True
    if counter % 200 == 0:
        led.value = False


def push_mic_select_state(force=False):
    if mics_mute_switch_state and not force:
        return
    if mic_select_switch.value:
        print("Mic switch sent F13!")
        kbd.send(Keycode.F13)
    else:
        print("Mic switch sent F14!")
        kbd.send(Keycode.F14)


def check_mic_select_switch():
    global mic_select_switch_state
    cur_mic_select_switch_state = mic_select_switch.value
    if cur_mic_select_switch_state != mic_select_switch_state:
        push_mic_select_state()
        
        mic_select_switch_state = cur_mic_select_switch_state


def push_mics_mute_state():
    if mics_mute_switch.value:
        print("Mics mute send F15!")
        kbd.send(Keycode.F15)
    else:
        print("Mics mute sent F16 and mic_select!")
        kbd.send(Keycode.F16)
        push_mic_select_state(force=True)


def check_mics_mute_switch():
    global mics_mute_switch_state
    cur_mics_mute_switch_state = mics_mute_switch.value
    if cur_mics_mute_switch_state != mics_mute_switch_state:
        push_mics_mute_state()
        
        mics_mute_switch_state = cur_mics_mute_switch_state

# ============== MAIN LOOP ============

print("Starting main loop...")

while True:
    check_mic_select_switch()
    check_mics_mute_switch()

    blink_every_second()

    time.sleep(1 / polling_rate_hz)
    

