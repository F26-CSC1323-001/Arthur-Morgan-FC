import time
import RPi.GPIO as GPIO
from mfrc522 import MFRC522

VIBRATION_PIN = 27    
RFID_RST_PIN = 25      

ALLOWED_CARDS = []    

GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)                 
reader = MFRC522(pin_rst=RFID_RST_PIN)


def setup_rfid_vibration():
    GPIO.setup(VIBRATION_PIN, GPIO.IN)


def read_card():
    
    status, _ = reader.MFRC522_Request(reader.PICC_REQIDL)  
    if status != reader.MI_OK:
        return None

    status, uid = reader.MFRC522_Anticoll()                  
    if status != reader.MI_OK:
        return None

    card_id = 0
    for byte in uid:                    
        card_id = card_id * 256 + byte
    return card_id


def is_allowed(card_id):
    return card_id in ALLOWED_CARDS


def vibration_detected():
    return GPIO.input(VIBRATION_PIN) == 1

if __name__ == "__main__":
    setup_rfid_vibration()
    print("Testing RFID + vibration. Tap a card or shake the sensor...")

    try:
        while True:
            if vibration_detected():
                print("Vibration detected!")
                time.sleep(1)

            card_id = read_card()
            if card_id is not None:
                print("Card ID:", card_id, "| Allowed:", is_allowed(card_id))
                time.sleep(1)

            time.sleep(0.1)

    except KeyboardInterrupt:
        print("Stopped.")

    GPIO.cleanup()