import time
import RPi.GPIO as GPIO

#GPIO Pin
PIN = 18

# Angles & time
LockedAngle = 0
UnlockedAngle = 90
OpenSeconds = 5

servo = None

# Defines servo
def setup_servo():
    global servo
    GPIO.setwarnings(False)
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(PIN, GPIO.OUT)
    servo = GPIO.PWM(PIN, 50)
    servo.start(0)
    lock()

# Turns servo
def move_servo(angle):
    duty = 2 + angle / 18
    servo.ChangeDutyCycle(duty)
    time.sleep(0.5)
    servo.ChangeDutyCycle(0)

# Puts lock in locked position
def lock():
    move_servo(LockedAngle)

# Puts lock in unlocked position
def unlock():
    move_servo(UnlockedAngle)

# stops servo
def stop_servo():
    servo.stop()

# Testing
if __name__ == "__main__":
    if PIN is None:
        print("please set SERVO_PIN.")
        exit()

    setup_servo()
    print("Testing servo: unlock, wait, lock (twice)...")

    for i in range(2):
        print("Unlocking")
        unlock()
        time.sleep(2)
        print("Locking")
        lock()
        time.sleep(2)

    stop_servo()
    GPIO.cleanup()
    print("Test done.")
