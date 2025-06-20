#include <ESP32Servo.h>


// Primary Ultrasonic Sensor (Front Scanning)
#define TRIG_PIN 18
#define ECHO_PIN 19

// Secondary Ultrasonic Sensor (Cover Mechanism)
#define TRIG_PIN2 22
#define ECHO_PIN2 23

// Servo Pins
#define SERVO_PIN 21          // Scanning Servo
#define SERVO_COVER_PIN 27    // Cover Servo

// Motor Driver Pins
#define IN1 25
#define IN2 26
#define IN3 33
#define IN4 32

#define MOTOR_SPEED_DELAY 1000   // Time to move forward (in ms)
#define DETECTION_DISTANCE 60    // Trigger distance (in cm)

Servo myServo;
Servo coverServo;

bool coverOpen = false;
unsigned long coverOpenTime = 0;
const unsigned long coverDuration = 10000;  // Cover open time (10 sec)

void setup() {
  Serial.begin(115200);

  pinMode(IN1, OUTPUT);
  pinMode(IN2, OUTPUT);
  pinMode(IN3, OUTPUT);
  pinMode(IN4, OUTPUT);

  pinMode(TRIG_PIN, OUTPUT);
  pinMode(ECHO_PIN, INPUT);
  pinMode(TRIG_PIN2, OUTPUT);
  pinMode(ECHO_PIN2, INPUT);

  myServo.setPeriodHertz(50);
  coverServo.setPeriodHertz(50);
  myServo.attach(SERVO_PIN, 500, 2500);
  coverServo.attach(SERVO_COVER_PIN, 500, 2500);

  myServo.write(90);       // Center scanning
  coverServo.write(180);   // Cover starts closed
  delay(1000);
}

// Read distance with filtering and timeout
long readDistanceCM(int trigPin, int echoPin) {
  digitalWrite(trigPin, LOW);
  delayMicroseconds(2);
  digitalWrite(trigPin, HIGH);
  delayMicroseconds(10);
  digitalWrite(trigPin, LOW);

  long duration = pulseIn(echoPin, HIGH, 50000);  // 50ms timeout

  if (duration == 0) return -1;

  long distance = duration * 0.034 / 2;

  // Return -1 for out-of-range values
  if (distance < 2 || distance > 400) return -1;
  return distance;
}

void moveForward() {
  digitalWrite(IN1, HIGH);
  digitalWrite(IN2, LOW);
  digitalWrite(IN3, HIGH);
  digitalWrite(IN4, LOW);
}

void stopMotors() {
  digitalWrite(IN1, LOW);
  digitalWrite(IN2, LOW);
  digitalWrite(IN3, LOW);
  digitalWrite(IN4, LOW);
}

void loop() {
  int bestAngle = 90;
  long minDistance = 400;

  Serial.println("🔍 Scanning...");
  for (int angle = 10; angle <= 200; angle += 20) {
    myServo.write(angle);
    delay(400);

    long dist = readDistanceCM(TRIG_PIN, ECHO_PIN);
    Serial.print("Angle ");
    Serial.print(angle);
    Serial.print(": ");
    Serial.print(dist);
    Serial.println(" cm");

    if (dist > 0 && dist < minDistance) {
      minDistance = dist;
      bestAngle = angle;
    }
  }

  myServo.write(bestAngle);
  delay(300);

  if (minDistance > 0 && minDistance < DETECTION_DISTANCE) {
    Serial.println(" Object detected – moving forward");
    moveForward();
    delay(MOTOR_SPEED_DELAY);
    stopMotors();
  } else {
    Serial.println(" No object in range");
    stopMotors();
  }

  // Cover control logic (Secondary sensor)
  long coverDist = readDistanceCM(TRIG_PIN2, ECHO_PIN2);
  Serial.print("📡 Cover Sensor Distance: ");
  Serial.print(coverDist);
  Serial.println(" cm");

  if (!coverOpen && coverDist > 0 && coverDist < DETECTION_DISTANCE) {
    Serial.println(" Object detected by cover sensor – opening cover");
    coverServo.write(-15);  // Open cover (adjust angle as needed)
    coverOpen = true;
    coverOpenTime = millis();
  }

  if (coverOpen && (millis() - coverOpenTime >= coverDuration)) {
    Serial.println(" Closing cover after 10 seconds");
    coverServo.write(220);  // Close cover
    coverOpen = false;
  }

  delay(100);
}
