#include <Servo.h>

// arduino sketch: waits for ai confirmation from laptop before firing.
// sensor detects proximity -> sends "trigger" over serial -> laptop
// classifies the webcam frame -> replies "fire" or times out -> if
// "fire", both servos squeeze the spray bottle trigger.

// config
const int TRIG_PIN   = 3;
const int ECHO_PIN   = 2;
const int SERVO1_PIN  = 9;
const int SERVO2_PIN  = 10;

const int SERVO_REST_ANGLE  = 0;
const int SERVO_PRESS_ANGLE = 180;

const float DISTANCE_THRESHOLD_CM = 60.0;
const unsigned long DEBOUNCE_MS       = 50;
const unsigned long PRESS_DURATION_MS = 1000;
const unsigned long COOLDOWN_MS       = 2000;
const unsigned long SERIAL_TIMEOUT_MS = 2000;

const long BAUD_RATE = 9600;

// state
Servo triggerServo1;
Servo triggerServo2;
unsigned long lastFiredTime = 0;

void setup() {
  pinMode(TRIG_PIN, OUTPUT);
  pinMode(ECHO_PIN, INPUT);

  triggerServo1.attach(SERVO1_PIN);
  triggerServo1.write(SERVO_REST_ANGLE);

  triggerServo2.attach(SERVO2_PIN);
  triggerServo2.write(180 - SERVO_REST_ANGLE);

  Serial.begin(BAUD_RATE);
  Serial.setTimeout(SERIAL_TIMEOUT_MS);
}

float readDistanceCm() {
  digitalWrite(TRIG_PIN, LOW);
  delayMicroseconds(2);
  digitalWrite(TRIG_PIN, HIGH);
  delayMicroseconds(10);
  digitalWrite(TRIG_PIN, LOW);

  long duration = pulseIn(ECHO_PIN, HIGH, 30000);
  if (duration == 0) return -1;
  return (duration * 0.0343) / 2.0;
}

bool sensorTriggered() {
  // debounce: confirm the reading twice before treating it as real
  float distance = readDistanceCm();
  if (distance < 0) return false;

  if (distance <= DISTANCE_THRESHOLD_CM) {
    delay(DEBOUNCE_MS);
    float confirmDistance = readDistanceCm();
    return confirmDistance > 0 && confirmDistance <= DISTANCE_THRESHOLD_CM;
  }
  return false;
}

bool inCooldown() {
  return (millis() - lastFiredTime) < COOLDOWN_MS;
}

bool waitForFireCommand() {
  // blocks until the laptop responds or the serial timeout hits
  String response = Serial.readStringUntil('\n');
  response.trim();
  return response == "FIRE";
}

void fireServos() {
  // servo2 mirrors servo1's angle so both arms squeeze inward together
  triggerServo1.write(SERVO_PRESS_ANGLE);
  triggerServo2.write(180 - SERVO_PRESS_ANGLE);
  delay(PRESS_DURATION_MS);
  triggerServo1.write(SERVO_REST_ANGLE);
  triggerServo2.write(180 - SERVO_REST_ANGLE);
  lastFiredTime = millis();
}

void loop() {
  if (!inCooldown() && sensorTriggered()) {
    Serial.println("TRIGGER");

    if (waitForFireCommand()) {
      fireServos();
    }
    // no "fire" response (timeout or "skip") -> do nothing, loop again
  }

  delay(50);
}
