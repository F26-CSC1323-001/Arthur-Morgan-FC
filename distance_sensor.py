import time
import RPi.GPIO as GPIO

TRIG_PIN = 24
ECHO_PIN = 25


def setup_distance():
    GPIO.setup(TRIG_PIN, GPIO.OUT, initial=GPIO.LOW)
    GPIO.setup(ECHO_PIN, GPIO.IN)


def get_distance():
    
    GPIO.output(TRIG_PIN, GPIO.HIGH)
    time.sleep(0.00001)
    GPIO.output(TRIG_PIN, GPIO.LOW)

    
    timeout = time.time() + 0.04
    start = time.time()
    while GPIO.input(ECHO_PIN) == 0:
        start = time.time()
        if start > timeout:
            return None                 
    end = start
    while GPIO.input(ECHO_PIN) == 1:
        end = time.time()
        if end > timeout:
            return None

    
    distance = (end - start) * 34300 / 2
    return round(distance, 1)



if __name__ == "__main__":
    GPIO.setwarnings(False)
    GPIO.setmode(GPIO.BCM)
    setup_distance()
    print("Move your hand in front of the sensor... (Ctrl + C to stop)")
    try:
        while True:
            print("Distance:", get_distance(), "cm")
            time.sleep(0.5)
    except KeyboardInterrupt:
        print("Stopped.")
    GPIO.cleanup()
