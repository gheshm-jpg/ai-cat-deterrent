"""
laptop-side cat classifier (laptop + arduino prototype version)

waits for a "trigger" message from the arduino over usb serial,
captures a frame from the laptop's webcam, classifies it using yolov8,
and sends "fire" back to the arduino if a cat is found.

install deps:
    pip install ultralytics opencv-python pyserial
"""

import time
import serial
import cv2
from ultralytics import YOLO

# config
CONFIG = {
    # serial connection to the arduino
    "serial_port": "/dev/tty.usbmodem1101",  # mac/linux: "/dev/tty.usbmodemXXXX" or "/dev/ttyACM0". windows: "COM3" etc.
    "baud_rate": 9600,
    "serial_timeout_sec": 2,

    # camera
    "camera_index": 0,  # 0 = default webcam

    # model
    "model_name": "yolov8n.pt",  # nano version, smallest/fastest yolov8 model

    # detection behavior
    "target_label": "cat",
    "avoid_label": "person",
    "confidence_threshold": 0.7,  # 0.0-1.0, higher = fewer false positives

    # testing mode: set to true to fire on a person instead of a cat, so you
    # can test the full pipeline (sensor -> camera -> model -> servo) on
    # yourself without needing an actual cat in frame. set false for real use.
    "test_mode_human_only": True,
}


def setup_serial(config):
    # open the serial connection to the arduino
    return serial.Serial(
        config["serial_port"],
        config["baud_rate"],
        timeout=config["serial_timeout_sec"],
    )


def setup_camera(config):
    # open the laptop's webcam
    return cv2.VideoCapture(config["camera_index"])


def load_model(config):
    # load the yolov8 model (downloads automatically on first run)
    return YOLO(config["model_name"])


def capture_frame(cam):
    # grab a single frame from the webcam
    ok, frame = cam.read()
    if not ok:
        return None
    return frame


def classify_frame(model, frame, config):
    # run the frame through yolov8, return the set of detected labels
    # above the confidence threshold
    results = model(frame, verbose=False)[0]
    detected_labels = set()

    for box in results.boxes:
        confidence = float(box.conf[0])
        if confidence >= config["confidence_threshold"]:
            class_id = int(box.cls[0])
            label = model.names[class_id]
            detected_labels.add(label)

    return detected_labels


def should_fire_pump(detected_labels, config):
    # decide whether to trigger the spray based on what was detected
    if config["test_mode_human_only"]:
        return "person" in detected_labels
    return config["target_label"] in detected_labels


def handle_trigger(cam, model, ser, config):
    # capture, classify, and respond to the arduino's trigger message
    frame = capture_frame(cam)
    if frame is None:
        print("camera capture failed, skipping.")
        ser.write(b"SKIP\n")
        return

    detected_labels = classify_frame(model, frame, config)
    print(f"detected: {detected_labels}")

    if should_fire_pump(detected_labels, config):
        print("cat detected -> sending fire")
        ser.write(b"FIRE\n")
    else:
        print("no cat (or human present) -> sending skip")
        ser.write(b"SKIP\n")


def main():
    config = CONFIG

    ser = setup_serial(config)
    cam = setup_camera(config)
    model = load_model(config)

    print("listening for triggers from arduino...")

    try:
        while True:
            if ser.in_waiting > 0:
                line = ser.readline().decode("utf-8").strip()
                if line == "TRIGGER":
                    handle_trigger(cam, model, ser, config)
            time.sleep(0.02)

    except KeyboardInterrupt:
        print("shutting down.")
    finally:
        cam.release()
        ser.close()


if __name__ == "__main__":
    main()
