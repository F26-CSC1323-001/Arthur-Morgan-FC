

import time
import RPi.GPIO as GPIO

import rfid_vibration   
import servo_lock     
import leds_buzzer   
import display           
import safe_state        
import web_server        
import distance_sensor

TAP_COOLDOWN = 2       
MESSAGE_SECONDS = 6     
LEARN_SECONDS = 30       


safe_state.load(rfid_vibration.ALLOWED_CARDS)
settings = safe_state.settings        
live = safe_state.live                 

rfid_vibration.setup_rfid_vibration()
servo_lock.setup_servo()               
leds_buzzer.setup_leds_buzzer()
distance_sensor.setup_distance()
NEAR_CM = 50            # closer than this there is someone BOOOOOO
last_near = 0           

lcd_working = True
try:
    display.setup_display()
except Exception as error:              
    print("[display] LCD not working:", error)
    lcd_working = False

message_until = 0        



def lcd(line1, line2=""):
    live["lcd"] = [line1[:16], line2[:16]]
    if lcd_working:
        try:
            display.show(line1, line2)
        except Exception as error:
            print("[display] error:", error)


def lcd_home():
   
    if live["learning"]:
        lcd("Add new card", "Tap card now...")
    elif not live["locked"]:
        lcd("Safe is open", "Tap card to lock")
    elif not settings["card_access"]:
        lcd("Lockdown mode", "Use the website")
    else:
        lcd("Welcome!", "Tap your card")


def open_safe(who):
    print("Unlocking -", who)
    servo_lock.unlock()
    live["locked"] = False
    live["unlocked_at"] = time.time()
    leds_buzzer.green_on()
    leds_buzzer.beep(0.2)
    safe_state.add_event("unlock", "Unlocked by " + who)
    lcd_home()


def close_safe(who):
    print("Locking -", who)
    servo_lock.lock()
    live["locked"] = True
    leds_buzzer.green_off()
    leds_buzzer.beep(0.2)
    time.sleep(0.1)
    leds_buzzer.beep(0.2)              
    safe_state.add_event("lock", "Locked by " + who)
    lcd("Safe locked", "")
    time.sleep(1)
    lcd_home()


def access_denied(reason):
    print("Access DENIED -", reason)
    safe_state.add_event("denied", reason)
    lcd("Access denied", "Try again")
    leds_buzzer.denied_signal()
    time.sleep(1)
    lcd_home()


def tamper_alarm():
    print("ALARM! Someone is shaking the safe!")
    live["alarm_active"] = True
    live["last_alarm"] = time.strftime("%Y-%m-%d %H:%M:%S")
    safe_state.add_event("alarm", "Tamper alarm - the safe was shaken")
    lcd("!! ALARM !!", "Tamper detected")
    leds_buzzer.alarm_signal()
    lcd_home()


def handle_card(card_id):
  
    if live["learning"]:
        live["learning"] = False
        if safe_state.add_card(card_id):
            safe_state.add_event("card", "New card added (" + str(card_id) + ")")
            lcd("Card added!", "")
            leds_buzzer.beep(0.2)
        else:
            lcd("Card already", "saved")
        time.sleep(1.5)
        lcd_home()
        return

   
    if not settings["card_access"]:
        safe_state.add_event("denied", "Card tapped during lockdown")
        lcd("Lockdown mode", "Cards disabled")
        leds_buzzer.denied_signal()
        lcd_home()
        return

    
    if time.time() < live["lockout_end"]:
        seconds_left = int(live["lockout_end"] - time.time())
        lcd("Locked out", "Wait " + str(seconds_left) + " sec")
        time.sleep(2)
        lcd_home()
        return

    
    if safe_state.is_allowed(card_id):
        live["wrong_count"] = 0
        name = safe_state.card_name(card_id)
        if live["locked"]:
            open_safe(name)
        else:
            close_safe(name)
        return

  
    live["wrong_count"] = live["wrong_count"] + 1
    access_denied("Unknown card " + str(card_id))
    if live["wrong_count"] >= settings["max_wrong"]:
        live["lockout_end"] = time.time() + settings["lockout_seconds"]
        live["wrong_count"] = 0
        safe_state.add_event("alarm", "Too many wrong cards - locked out for "
                             + str(settings["lockout_seconds"]) + " sec")
        lcd("Too many tries", "Locked " + str(settings["lockout_seconds"]) + " sec")
        time.sleep(2)
        lcd_home()


def handle_command(name, value):
    
    global message_until
    if name == "unlock" and live["locked"]:
        open_safe("website")
    elif name == "lock" and not live["locked"]:
        close_safe("website")
    elif name == "beep":
        for i in range(3):
            leds_buzzer.beep(0.15)
            time.sleep(0.15)
    elif name == "test_alarm":
        safe_state.add_event("system", "Alarm test from website")
        lcd("Alarm test", "")
        leds_buzzer.alarm_signal()
        lcd_home()
    elif name == "message":
        lines = value.split("\n") + [""]
        lcd(lines[0], lines[1])
        message_until = time.time() + MESSAGE_SECONDS
    elif name == "learn_on":
        live["learning"] = True
        live["learning_until"] = time.time() + LEARN_SECONDS
        lcd_home()
    elif name == "learn_off":
        live["learning"] = False
        lcd_home()
    elif name == "refresh_lcd":
        lcd_home()



web_server.start_server()
live["hardware"] = "ok"
safe_state.add_event("system", "Safe started")
lcd_home()
print("Safe ready. Tap a card or open the website...")


try:
    while True:

        
        for name, value in safe_state.pop_commands():
            handle_command(name, value)

       
        if message_until and time.time() > message_until:
            message_until = 0
            lcd_home()
        if live["learning"] and time.time() > live["learning_until"]:
            live["learning"] = False
            lcd_home()

        
        if (not live["locked"] and settings["auto_lock_seconds"] > 0
                and time.time() - live["unlocked_at"] > settings["auto_lock_seconds"]):
            lcd("Auto locking", "Close the door!")
            leds_buzzer.alarm_signal()        # warning beeps (2 s)
            close_safe("auto-lock")

        
        if live["locked"] and settings["alarm_armed"] and rfid_vibration.vibration_detected():
            tamper_alarm()
            time.sleep(1)


        # 3b. Ultrasonic sensor: how close is someone?
        distance = distance_sensor.get_distance()
        live["distance"] = distance
        if distance is not None and distance < NEAR_CM and time.time() - last_near > 20:
            last_near = time.time()
            if live["locked"] and not settings["card_access"]:
                safe_state.add_event("alarm", "Someone near the safe during lockdown (" + str(distance) + " cm)")
                lcd("!! LOCKDOWN !!", "Step away")
                leds_buzzer.alarm_signal()
                lcd_home()
            elif live["locked"]:
                safe_state.add_event("system", "Someone at the safe (" + str(distance) + " cm)")
                lcd("Hello!", "Tap your card")
                message_until = time.time() + 6

        # 4. Check for a card
        card_id = rfid_vibration.read_card()
        if card_id is not None:
            print("Card ID:", card_id)
            handle_card(card_id)
            time.sleep(TAP_COOLDOWN)          

        time.sleep(0.1)

except KeyboardInterrupt:
    print("Stopped.")

safe_state.add_event("system", "Safe stopped")
if lcd_working:
    try:
        display.clear_display()
    except Exception:
        pass
servo_lock.stop_servo()
GPIO.cleanup()
