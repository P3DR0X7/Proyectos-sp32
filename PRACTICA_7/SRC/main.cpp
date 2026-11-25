
#include <ESP32Servo.h>


#define TRIG_PIN 18
#define ECHO_PIN 17
#define BUZZER_PIN 23
#define SERVO_PIN 5


Servo miServo;


const float DISTANCIA_ALERTA = 30.0;

int posicionActual = 0;
bool objetoDetectado = false;


float medirDistancia() {
  digitalWrite(TRIG_PIN, LOW);
  delayMicroseconds(2);

  digitalWrite(TRIG_PIN, HIGH);
  delayMicroseconds(10);
  digitalWrite(TRIG_PIN, LOW);

  long duracion = pulseIn(ECHO_PIN, HIGH, 30000);

  if (duracion == 0) {
    return -1;
  }

  return duracion * 0.0343 / 2.0;
}


void moverServo(int destino) {
  if (destino > posicionActual) {
    for (int angulo = posicionActual; angulo <= destino; angulo++) {
      miServo.write(angulo);
      delay(10);
    }
  } 
  else {
    for (int angulo = posicionActual; angulo >= destino; angulo--) {
      miServo.write(angulo);
      delay(10);
    }
  }

  posicionActual = destino;
}

void setup() {
  Serial.begin(115200);

  pinMode(TRIG_PIN, OUTPUT);
  pinMode(ECHO_PIN, INPUT);
  pinMode(BUZZER_PIN, OUTPUT);

  miServo.setPeriodHertz(50);
  miServo.attach(SERVO_PIN, 500, 2400);

  miServo.write(0);
  digitalWrite(BUZZER_PIN, LOW);

  Serial.println("Sistema iniciado");
}

void loop() {
  float distancia = medirDistancia();

  if (distancia > 0) {

    Serial.print("Distancia: ");
    Serial.print(distancia);
    Serial.println(" cm");

    if (distancia <= DISTANCIA_ALERTA) {

      if (!objetoDetectado) {
        objetoDetectado = true;

        Serial.println("OBJETO DETECTADO");
        tone(BUZZER_PIN, 2000);

        moverServo(90);
      }

    } else {

      if (objetoDetectado) {
        objetoDetectado = false;

        Serial.println("OBJETO ALEJADO");
        noTone(BUZZER_PIN);

        moverServo(0);
      }
    }

  } else {
    Serial.println("Sin lectura del sensor");
  }

  delay(100);
}
