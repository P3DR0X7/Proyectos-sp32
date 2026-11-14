#include <ESP32Servo.h>

Servo servo;
const int servoPin = 18;

void setup() {
  Serial.begin(115200);
  servo.setPeriodHertz(50);
  servo.attach(servoPin, 500, 2400);
  servo.write(0);
}

void loop() {
  if (Serial.available()) {
    int angulo = Serial.parseInt();
    angulo = constrain(angulo, 0, 180);
    servo.write(angulo);
  }
}
