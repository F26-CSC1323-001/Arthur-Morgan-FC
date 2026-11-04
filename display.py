import time
from RPLCD.i2c import CharLCD

LCD_ADDRESS = 0x27     

lcd = None


def setup_display():
    global lcd         
    lcd = CharLCD("PCF8574", LCD_ADDRESS, cols=16, rows=2)
    lcd.clear()


def show(line1, line2=""):
   
    lcd.clear()
    lcd.write_string(line1[:16])     
    lcd.cursor_pos = (1, 0)          
    lcd.write_string(line2[:16])    


def show_welcome():
    show("Welcome!", "Tap your card")


def clear_display():
    lcd.clear()

if __name__ == "__main__":
    setup_display()

    print("Showing welcome")
    show_welcome()
    time.sleep(3)

    print("Showing granted")
    show("Access granted", "Opening...")
    time.sleep(3)

    print("Showing denied")
    show("Access denied", "Try again")
    time.sleep(3)

    clear_display()
    print("Test done.")
