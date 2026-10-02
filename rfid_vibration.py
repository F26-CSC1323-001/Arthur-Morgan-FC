import time
import RPi.GPIO as GPIO
from mfrc522 import SimpleMFRC522

VIBRATION_PIN = None   

ALLOWED_CARDS = []     

reader = SimpleMFRC522()

def setup_rfid_vibration():
    GPIO.setwarnings(False)
    GPIO.setmode(GPIO.BOARD)
    GPIO.setup(VIBRATION_PIN, GPIO.IN)

def read_card():
    
    return reader.read_id_no_block()

def is_allowed(card_id):
    return card_id in ALLOWED_CARDS

def vibration_detected():
   
    return GPIO.input(VIBRATION_PIN) == 1


if __name__ == "__main__":
    if VIBRATION_PIN is None:
        print("Please set VIBRATION_PIN at the top of the file first.")
        exit()

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