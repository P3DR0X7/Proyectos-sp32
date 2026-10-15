#include <Arduino.h>

#define RELE 2
#define SW1 21
#define SW2 19


#define PRENDE_RELE digitalWrite(RELE, HIGH)
#define APAGA_RELE digitalWrite(RELE, LOW)

#define PRESSED(x) (digitalRead(x) == LOW)

void setup() {
  Serial.begin(115200);
  Serial.println("Control de rele con ESP32");

  pinMode(RELE, OUTPUT);
  pinMode(SW1, INPUT_PULLUP);
  pinMode(SW2, INPUT_PULLUP);

  APAGA_RELE;
}

void loop() {
  if (PRESSED(SW1)) {
    PRENDE_RELE;
    Serial.println("Boton 1 pulsado: RELE ENCENDIDO");
    delay(250);
  }

  if (PRESSED(SW2)) {
    APAGA_RELE;
    Serial.println("Boton 2 pulsado: RELE APAGADO");
    delay(250);
  }
}
