# ai cat deterrent

arduino uno + hc-sr04 ultrasonic sensor for proximity detection, then a
laptop running a webcam + yolov8 to confirm it's actually a cat before
firing. two servo motors squeeze a spray bottle's trigger to spray.

## how it works

1. hc-sr04 sensor detects something within ~2 feet
2. arduino sends "trigger" over usb serial to the laptop
3. laptop grabs a webcam frame and classifies it with yolov8
4. if a cat is detected, laptop sends "fire" back
5. arduino moves two servos to squeeze the spray bottle's trigger

## files

- laptop_classifier.py — runs on the laptop, handles camera + classification
- two_servo_sprayer_ai.ino — runs on the arduino, handles sensing + servos

## setup

pip install ultralytics opencv-python pyserial

update serial_port in laptop_classifier.py to match your arduino's port,
upload the .ino file via the arduino ide, then run:

python laptop_classifier.py
