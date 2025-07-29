# ============= LIBRARIES =============
import board
import digitalio
import usb_hid
from adafruit_hid.keyboard import Keyboard
from adafruit_hid.keycode import Keycode
import time
import os
import adafruit_connection_manager
import wifi
import adafruit_requests

# COL1: ONAIR LIGHT GP13 (HASS CALL)  -  DESK LIGHTBAR GP15 (HASS CALL)
# COL2: MIC SELECT  GP16 (F13 & F14)  -  MUTE ALL GP11 (F15 & F16)
# COL4: DISCORD MODE GP18 & GP28 (F17 & F18) - DISCORD ACTION (F19)
# COL5: CLIP MOMENT GP22 (F20) - RECORD GP26 (F21)

# DISCORD_STATE: 0 - OK, 1 - MUTE, 2 - DEAFEN


print("Initializing...")

# =============== ENV CONFIG ==============
print("Reading config...")
ssid = os.getenv("CIRCUITPY_WIFI_SSID")
password = os.getenv("CIRCUITPY_WIFI_PASSWORD")
hass_token = os.getenv("HASS_TOKEN")
hass_ip = os.getenv("HASS_IP")

polling_rate_hz = 100


# =============== HASS CONSTANTS ==============

hass_url = f"http://{hass_ip}/api/services/switch/turn_"
hass_headers = {
    "Authorization": f"Bearer {hass_token}",
    "Content-Type": "application/json"
}
hass_payload_desk_lightbar = {
    "entity_id": "switch.desk_tuya_lightbar"
}

hass_payload_onair_light= {
    "entity_id": "switch.nonexistent"
}



# ========== GLOBAL VARIABLES =========
print("Creating global variables...")

counter = 0



# ================ PINS ===============
print("Setting up pins...")

kbd = Keyboard(usb_hid.devices)

led = digitalio.DigitalInOut(board.LED)
led.direction = digitalio.Direction.OUTPUT

# COL1:
desk_lightbar_switch = digitalio.DigitalInOut(board.GP15)
desk_lightbar_switch.direction = digitalio.Direction.INPUT
desk_lightbar_switch.pull = digitalio.Pull.UP

onair_light_switch = digitalio.DigitalInOut(board.GP13)
onair_light_switch.direction = digitalio.Direction.INPUT
onair_light_switch.pull = digitalio.Pull.UP


# COL2
mic_select_switch = digitalio.DigitalInOut(board.GP16)
mic_select_switch.direction = digitalio.Direction.INPUT
mic_select_switch.pull = digitalio.Pull.UP

mics_mute_switch = digitalio.DigitalInOut(board.GP11)
mics_mute_switch.direction = digitalio.Direction.INPUT
mics_mute_switch.pull = digitalio.Pull.UP

# COL4
discord_mute_switch = digitalio.DigitalInOut(board.GP28)
discord_mute_switch.direction = digitalio.Direction.INPUT
discord_mute_switch.pull = digitalio.Pull.UP

discord_deaf_switch = digitalio.DigitalInOut(board.GP18)
discord_deaf_switch.direction = digitalio.Direction.INPUT
discord_deaf_switch.pull = digitalio.Pull.UP

discord_action_button = digitalio.DigitalInOut(board.GP20)
discord_action_button.direction = digitalio.Direction.INPUT
discord_action_button.pull = digitalio.Pull.UP


# COL5
clip_button = digitalio.DigitalInOut(board.GP22)
clip_button.direction = digitalio.Direction.INPUT
clip_button.pull = digitalio.Pull.UP

# TODO recording button + light

# =============== STATES ==============
print("Setting input states...")


desk_lightbar_switch_state = desk_lightbar_switch.value
onair_light_switch_state = onair_light_switch.value


mic_select_switch_state = mic_select_switch.value
mics_mute_switch_state = mics_mute_switch.value

discord_action_button_state = discord_action_button.value

discord_mute_switch_state = discord_mute_switch.value
discord_deaf_switch_state = discord_deaf_switch.value
clip_button_state = clip_button.value

discord_state = 1

if discord_mute_switch_state:
    discord_state = 2
elif discord_deaf_switch_state:
    discord_state = 0

print("Discord start state is", discord_state)

# =============== WIFI CONNECTION ==============
print(f"Connecting to {ssid}...")
wifi.radio.connect(ssid, password)
print("Connected to WiFi!")

pool = adafruit_connection_manager.get_radio_socketpool(wifi.radio)
ssl_context = adafruit_connection_manager.get_radio_ssl_context(wifi.radio)
requests = adafruit_requests.Session(pool, ssl_context)


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
    if not mics_mute_switch_state and not force:
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
    if not mics_mute_switch.value:
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


def switch_desk_lightbar(state):
    print(f"Sending POST to {hass_url+state}")
    response = requests.post(hass_url+state, json=hass_payload_desk_lightbar, headers=hass_headers)


    print("Response status:", response.status_code)
    if response.status_code == 200:
        print(f"Switch desklight turned {state} successfully!")
    else:
        print("Failed. Response text:", response.text)
        

def switch_onair_light(state):
    return # for now unused
    print(f"Sending POST to {hass_url+state}")
    response = requests.post(hass_url+state, json=hass_payload_onair_light, headers=hass_headers)


    print("Response status:", response.status_code)
    if response.status_code == 200:
        print(f"Switch onair turned {state} successfully!")
    else:
        print("Failed. Response text:", response.text)
        

def check_desk_lightbar_switch():
    global desk_lightbar_switch_state
    cur_desk_lightbar_switch_state = desk_lightbar_switch.value
    if cur_desk_lightbar_switch_state != desk_lightbar_switch_state:
        if cur_desk_lightbar_switch_state:
            switch_desk_lightbar("on")
        else:
            switch_desk_lightbar("off")
        desk_lightbar_switch_state = cur_desk_lightbar_switch_state

def check_onair_light_switch():
    global onair_light_switch_state
    cur_onair_light_switch_state = onair_light_switch.value
    if cur_onair_light_switch_state != onair_light_switch_state:
        if cur_onair_light_switch_state:
            switch_onair_light("on")
        else:
            switch_onair_light("off")
        onair_light_switch_state = cur_onair_light_switch_state


def check_discord_action_button():
    global discord_action_button_state
    cur_discord_action_button_state = discord_action_button.value
    if cur_discord_action_button_state != discord_action_button_state:
        if not cur_discord_action_button_state:
            kbd.send(Keycode.F19)
            print("Sent discord action F19!")

        discord_action_button_state = cur_discord_action_button_state

def check_clip_button():
    global clip_button_state
    cur_clip_button_state = clip_button.value
    if cur_clip_button_state != clip_button_state:
        if not cur_clip_button_state:
            kbd.send(Keycode.F21)
            print("Sent clip F21!")

        clip_button_state = cur_clip_button_state


def check_discord_mute_switch():
    global discord_mute_switch_state, discord_state
    cur_discord_mute_switch_state = discord_mute_switch.value
    if cur_discord_mute_switch_state != discord_mute_switch_state:
        print("mute toggled", cur_discord_mute_switch_state)
        if cur_discord_mute_switch_state:
            kbd.send(Keycode.F17)
            discord_state = 1
            print("Sent discord mute F17!")
        if not cur_discord_mute_switch_state:
            kbd.send(Keycode.F17)
            discord_state = 0
            print("Sent discord unmute F17!")

        discord_mute_switch_state = cur_discord_mute_switch_state

def check_discord_deaf_switch():
    global discord_deaf_switch_state, discord_state
    cur_discord_deaf_switch_state = discord_deaf_switch.value
    if cur_discord_deaf_switch_state != discord_deaf_switch_state:
        print("deaf toggled", cur_discord_deaf_switch_state)

        if not cur_discord_deaf_switch_state:
            kbd.send(Keycode.F18)
            discord_state = 2
            print("Sent discord deafen F18!")

        if cur_discord_deaf_switch_state:
            kbd.send(Keycode.F18)
            discord_state = 1
            print("Sent discord undeafen (but still muted) F18")

        discord_deaf_switch_state = cur_discord_deaf_switch_state


# ============== MAIN LOOP ============
print("Starting main loop...")

while True:
    check_mic_select_switch()
    check_mics_mute_switch()
    check_desk_lightbar_switch()
    check_onair_light_switch()
    check_discord_action_button()
    check_clip_button()
    check_discord_mute_switch()
    check_discord_deaf_switch()

    blink_every_second()

    time.sleep(1 / polling_rate_hz)
    