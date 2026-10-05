import time
import RPi.GPIO as GPIO
 
GREEN_LED = None       
RED_LED = None         
BUZZER_PIN = None      
 
 
def setup_leds_buzzer():
    GPIO.setwarnings(False)
    GPIO.setmode(GPIO.BCM)             
    GPIO.setup(GREEN_LED, GPIO.OUT)
    GPIO.setup(RED_LED, GPIO.OUT)
    GPIO.setup(BUZZER_PIN, GPIO.OUT)
 
 
def green_on():
    GPIO.output(GREEN_LED, GPIO.HIGH)
 
 
def green_off():
    GPIO.output(GREEN_LED, GPIO.LOW)
 
 
def beep(seconds):
    GPIO.output(BUZZER_PIN, GPIO.HIGH)
    time.sleep(seconds)
    GPIO.output(BUZZER_PIN, GPIO.LOW)
 
 
def denied_signal():
    GPIO.output(RED_LED, GPIO.HIGH)
    beep(1)
    GPIO.output(RED_LED, GPIO.LOW)
 
 
def alarm_signal():
   
    for i in range(5):
        GPIO.output(RED_LED, GPIO.HIGH)
        GPIO.output(BUZZER_PIN, GPIO.HIGH)
        time.sleep(0.2)
        GPIO.output(RED_LED, GPIO.LOW)
        GPIO.output(BUZZER_PIN, GPIO.LOW)
        time.sleep(0.2)
 
 

if __name__ == "__main__":
    if None in [GREEN_LED, RED_LED, BUZZER_PIN]:
        print("Please fill in all the pin numbers at the top of the file first.")
        exit()
 
    setup_leds_buzzer()
 
    print("Green LED + short beep")
    green_on()
    beep(0.2)
    time.sleep(1)
    green_off()
    time.sleep(1)
 
    print("Denied signal")
    denied_signal()
    time.sleep(1)
 
    print("Alarm signal")
    alarm_signal()
 
    GPIO.cleanup()
    print("Test done.")