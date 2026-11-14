
#define RELE1 25
#define RELE2 26
#define RELE3 27
#define LM35_PIN 34

#define RELE_ON LOW
#define RELE_OFF HIGH

bool estado1 = false;
bool estado2 = false;
bool estado3 = false;

bool modoAutomatico = false;
bool faseAlta = false;

float limiteLow = 20.0;
float limiteHigh = 30.0;
float temperatura = 0.0;

unsigned long tiempoLectura = 0;

void actualizarReles() {
  digitalWrite(RELE1, estado1 ? RELE_ON : RELE_OFF);
  digitalWrite(RELE2, estado2 ? RELE_ON : RELE_OFF);
  digitalWrite(RELE3, estado3 ? RELE_ON : RELE_OFF);
}

void aplicarCiclo() {
  if (!modoAutomatico) return;

  
  if (!faseAlta && temperatura >= limiteHigh) {
    faseAlta = true;
    Serial.println("CAMBIO A HIGH");
  }
  
  else if (faseAlta && temperatura <= limiteLow) {
    faseAlta = false;
    Serial.println("CAMBIO A LOW");
  }

  if (faseAlta) {
    
    estado1 = true;
    estado2 = false;
    estado3 = false;
  } else {
    
    estado1 = false;
    estado2 = true;
    estado3 = true;
  }

  actualizarReles();
}

void procesarComando(String comando) {
  comando.trim();

  if (comando.startsWith("SET:")) {
    int coma = comando.indexOf(',');

    if (coma > 4) {
      float lowNuevo =
          comando.substring(4, coma).toFloat();
      float highNuevo =
          comando.substring(coma + 1).toFloat();

      if (lowNuevo >= 0 &&
          lowNuevo < highNuevo &&
          highNuevo <= 150) {
        limiteLow = lowNuevo;
        limiteHigh = highNuevo;
        Serial.println("LIMITES_OK");
      } else {
        Serial.println("ERROR_LIMITES");
      }
    }
  }
  else if (comando == "AUTO") {
    modoAutomatico = true;

    
    faseAlta = (temperatura >= limiteHigh);

    Serial.println("MODO_AUTO");
    aplicarCiclo();
  }
  else if (comando == "STOPAUTO") {
    modoAutomatico = false;

    estado1 = false;
    estado2 = false;
    estado3 = false;

    actualizarReles();
    Serial.println("MODO_MANUAL");
  }
  else if (!modoAutomatico) {
    if (comando == "1ON") estado1 = true;
    else if (comando == "1OFF") estado1 = false;
    else if (comando == "2ON") estado2 = true;
    else if (comando == "2OFF") estado2 = false;
    else if (comando == "3ON") estado3 = true;
    else if (comando == "3OFF") estado3 = false;

    actualizarReles();
  }

  Serial.printf("RELES:%d,%d,%d\n",
                estado1, estado2, estado3);
}

void setup() {
  Serial.begin(115200);
  Serial.setTimeout(30);

  pinMode(RELE1, OUTPUT);
  pinMode(RELE2, OUTPUT);
  pinMode(RELE3, OUTPUT);

  estado1 = false;
  estado2 = false;
  estado3 = false;
  actualizarReles();

  analogReadResolution(12);
  analogSetPinAttenuation(LM35_PIN, ADC_11db);

  Serial.println("ESP32_LISTO");
}

void loop() {
  while (Serial.available()) {
    String comando = Serial.readStringUntil('\n');
    procesarComando(comando);
  }

  if (millis() - tiempoLectura >= 500) {
    tiempoLectura = millis();

    uint32_t milivoltios =
        analogReadMilliVolts(LM35_PIN);

    temperatura = milivoltios / 10.0;

    aplicarCiclo();

    Serial.printf("TEMP:%.1f\n", temperatura);
    Serial.printf("RELES:%d,%d,%d\n",
                  estado1, estado2, estado3);
  }
}
