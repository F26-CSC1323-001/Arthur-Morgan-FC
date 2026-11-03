
import threading
import time

import cv2

CAMERA_NUMBER = 0       
WIDTH = 640
HEIGHT = 480
FPS = 15                 

latest_frame = None      
camera_working = False


def camera_loop():
    
    global latest_frame, camera_working
    camera = cv2.VideoCapture(CAMERA_NUMBER)
    camera.set(cv2.CAP_PROP_FRAME_WIDTH, WIDTH)
    camera.set(cv2.CAP_PROP_FRAME_HEIGHT, HEIGHT)

    while True:
        ok, frame = camera.read()
        if not ok:                             
            camera_working = False
            camera.release()
            time.sleep(2)                      
            camera = cv2.VideoCapture(CAMERA_NUMBER)
            continue

        ok, jpeg = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 70])
        if ok:
            latest_frame = jpeg.tobytes()
            camera_working = True
        time.sleep(1 / FPS)


def start_camera():
    thread = threading.Thread(target=camera_loop, daemon=True)
    thread.start()
    print("[camera] started")


def video_stream():
    
    while True:
        if latest_frame is not None:
            yield (b"--frame\r\n"
                   b"Content-Type: image/jpeg\r\n\r\n" + latest_frame + b"\r\n")
        time.sleep(1 / FPS)
