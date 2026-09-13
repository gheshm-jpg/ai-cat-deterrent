# Cat Detection & Arduino Actuation Prototype

A computer-vision and embedded-systems project that combines an ultrasonic proximity sensor, a pretrained YOLOv8 detector, and an Arduino-controlled two-servo spray mechanism. The engineering focus is the sensor-to-inference-to-actuator pipeline.

**Stack:** Python · OpenCV · Ultralytics YOLOv8 · USB serial · Arduino C++

## How it works

1. An HC-SR04 sensor checks for an object within 60 cm, then confirms the reading after 50 ms.
2. The Arduino sends `TRIGGER` to the laptop at 9600 baud.
3. Python captures one webcam frame and keeps detections with confidence at least 0.7.
4. Normal detection requires a cat and no detected person. Dry-run and human demo modes always send `SKIP`.
5. When actuation is explicitly enabled and the detection passes, Python sends `FIRE`; the Arduino moves two mirrored servos for one second, then returns them to rest. A two-second cooldown follows.

This uses pretrained object detection; the repository does not train a custom model.

## Hardware and source

| Component | Role / sketch pin |
| --- | --- |
| Arduino Uno | Sensor input and servo control |
| HC-SR04 | TRIG: D3; ECHO: D2 |
| Servo 1 / Servo 2 | Signal: D9 / D10 |
| Laptop and webcam | Image capture and YOLO inference |
| USB connection | Newline-delimited serial messages |

See [Python controller](laptop_classifier.py) and [Arduino sketch](two_servo_sprayer_ai.ino). The pin table describes signal connections; select a suitable servo power supply and share ground with the Arduino. Calibrate servo travel with the spray mechanism disconnected.

## Run locally

```bash
python -m venv .venv
# macOS / Linux
source .venv/bin/activate
# Windows PowerShell: .venv\Scripts\Activate.ps1
python -m pip install ultralytics opencv-python pyserial
python laptop_classifier.py
```

Before running, upload the sketch using the Arduino IDE, close its Serial Monitor, and set `serial_port` and `camera_index` in Python to match your hardware. Allow camera access. The YOLO weights download on the first run. Dependency versions are not pinned.

## Operating modes

| Setting | Default | Behavior |
| --- | --- | --- |
| `dry_run` | `True` | Logs detections and sends `SKIP`; no commanded actuation |
| `test_mode_human_only` | `False` | When enabled, logs person detection only and never authorizes actuation |
| `avoid_label` | `person` | Blocks normal actuation when a person is detected |

To bench-test servo actuation, disconnect the spray mechanism, set `dry_run=False`, and keep `test_mode_human_only=False`. A qualifying cat detection is still required. The controller sends `SKIP` when frame capture fails.

## Validation and limitations

Software checks covered all 16 combinations of cat presence, person presence, human demo mode, and dry-run, plus camera-capture failure. These checks used simulated detections and serial output; they do not establish model accuracy or hardware reliability.

For a hardware check, start in dry-run, observe serial responses for empty, cat, person, and mixed frames, then bench-test servo travel with the spray mechanism disconnected. Record lighting, inference latency, false detections, and timeout behavior.

This remains a prototype. Single-frame detection can miss people or misclassify objects, and person exclusion is not a guarantee of safety. The serial protocol has no request IDs; delayed replies may be consumed by a later request. The Arduino timeout is two seconds, so inference latency matters. Use supervised bench testing; do not rely on this as an unattended animal-control system.
