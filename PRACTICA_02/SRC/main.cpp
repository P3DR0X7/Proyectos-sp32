
#include <Wire.h>
#include <LiquidCrystal_I2C.h>

#define TRIG_PIN 5
#define ECHO_PIN 18
#define SDA_PIN 21
#define SCL_PIN 22
#define LCD_ADDRESS 0x27

#define MOTOR1 25
#define MOTOR2 26
#define BOTON_MODO 12

LiquidCrystal_I2C lcd(LCD_ADDRESS, 16, 2);

const float DISTANCIA_VACIO = 24.0;
const float DISTANCIA_LLENO = 4.0;
const float CAPACIDAD_LITROS = 2.0;

int nivelHIGH = 80;
int nivelLOW = 20;

float distancia = 24.0;
float porcentaje = 0.0;
float litros = 0.0;

bool sensorValido = false;
bool cicloActivo = true;
bool botonAnterior = HIGH;

enum Estado { LLENANDO, VACIANDO };
Estado estado = LLENANDO;

unsigned long tiempoBoton = 0;
unsigned long ultimaActualizacion = 0;
const unsigned long ANTIRREBOTE = 250;

void actualizarNivel() {
  digitalWrite(TRIG_PIN, LOW);
  delayMicroseconds(3);
  digitalWrite(TRIG_PIN, HIGH);
  delayMicroseconds(10);
  digitalWrite(TRIG_PIN, LOW);

  unsigned long duracion = pulseIn(ECHO_PIN, HIGH, 30000);

  if (duracion == 0) {
    sensorValido = false;
    return;
  }

  distancia = duracion * 0.0343 / 2.0;

  if (distancia < 2.0 || distancia > 400.0) {
    sensorValido = false;
    return;
  }

  sensorValido = true;
  porcentaje = (DISTANCIA_VACIO - distancia) /
               (DISTANCIA_VACIO - DISTANCIA_LLENO) * 100.0;
  porcentaje = constrain(porcentaje, 0.0, 100.0);
  litros = porcentaje / 100.0 * CAPACIDAD_LITROS;
}

void apagarBombas() {
  digitalWrite(MOTOR1, LOW);
  digitalWrite(MOTOR2, LOW);
}

void controlarCiclo() {
  if (!sensorValido || !cicloActivo) {
    apagarBombas();
    return;
  }

  if (estado == LLENANDO && porcentaje >= nivelHIGH) {
    estado = VACIANDO;
  } else if (estado == VACIANDO && porcentaje <= nivelLOW) {
    estado = LLENANDO;
  }

  if (estado == LLENANDO) {
    digitalWrite(MOTOR1, HIGH);
    digitalWrite(MOTOR2, LOW);
  } else {
    digitalWrite(MOTOR1, LOW);
    digitalWrite(MOTOR2, HIGH);
  }
}

void procesarSerial() {
  if (!Serial.available()) return;

  String comando = Serial.readStringUntil('\n');
  comando.trim();

  if (comando.startsWith("HIGH=")) {
    int valor = comando.substring(5).toInt();
    nivelHIGH = constrain(valor, 5, 100);

    if (nivelLOW >= nivelHIGH) {
      nivelLOW = max(0, nivelHIGH - 5);
    }
  } else if (comando.startsWith("LOW=")) {
    int valor = comando.substring(4).toInt();
    nivelLOW = constrain(valor, 0, 95);

    if (nivelLOW >= nivelHIGH) {
      nivelHIGH = min(100, nivelLOW + 5);
    }
  } else if (comando == "AUTO=1") {
    cicloActivo = true;
  } else if (comando == "AUTO=0") {
    cicloActivo = false;
    apagarBombas();
  }
}

void actualizarLCD() {
  lcd.setCursor(0, 0);

  if (!sensorValido) {
    lcd.print("Error del sensor");
    lcd.setCursor(0, 1);
    lcd.print("Bombas apagadas ");
    return;
  }

  lcd.print("Nivel:");
  lcd.print((int)porcentaje);
  lcd.print("% ");
  lcd.print(litros, 1);
  lcd.print("L   ");

  lcd.setCursor(0, 1);

  if (!cicloActivo) {
    lcd.print("CICLO PAUSADO   ");
  } else if (estado == LLENANDO) {
    lcd.print("Llenando H:");
    lcd.print(nivelHIGH);
    lcd.print("%    ");
  } else {
    lcd.print("Vaciando L:");
    lcd.print(nivelLOW);
    lcd.print("%    ");
  }
}

void enviarDatos() {
  Serial.print("DIST=");
  Serial.print(distancia, 1);
  Serial.print(",PCT=");
  Serial.print(porcentaje, 1);
  Serial.print(",LITROS=");
  Serial.print(litros, 2);
  Serial.print(",HIGH=");
  Serial.print(nivelHIGH);
  Serial.print(",LOW=");
  Serial.print(nivelLOW);
  Serial.print(",ESTADO=");

  if (!sensorValido) {
    Serial.print("ERROR");
  } else if (!cicloActivo) {
    Serial.print("PAUSADO");
  } else {
    Serial.print(estado == LLENANDO ? "LLENANDO" : "VACIANDO");
  }

  Serial.print(",M1=");
  Serial.print(digitalRead(MOTOR1) == HIGH ? 1 : 0);
  Serial.print(",M2=");
  Serial.println(digitalRead(MOTOR2) == HIGH ? 1 : 0);
}

void setup() {
  Serial.begin(115200);
  Serial.setTimeout(50);

  pinMode(TRIG_PIN, OUTPUT);
  pinMode(ECHO_PIN, INPUT);
  pinMode(MOTOR1, OUTPUT);
  pinMode(MOTOR2, OUTPUT);
  pinMode(BOTON_MODO, INPUT_PULLUP);

  apagarBombas();

  Wire.begin(SDA_PIN, SCL_PIN);
  lcd.init();
  lcd.backlight();

  lcd.setCursor(0, 0);
  lcd.print("Control de agua");
  lcd.setCursor(0, 1);
  lcd.print("Ciclo automatico");
  delay(1500);
}

void loop() {
  procesarSerial();

  bool botonActual = digitalRead(BOTON_MODO);

  if (botonAnterior == HIGH &&
      botonActual == LOW &&
      millis() - tiempoBoton >= ANTIRREBOTE) {
    cicloActivo = !cicloActivo;
    tiempoBoton = millis();

    if (!cicloActivo) {
      apagarBombas();
    }
  }

  botonAnterior = botonActual;

  if (millis() - ultimaActualizacion >= 500) {
    ultimaActualizacion = millis();

    actualizarNivel();
    controlarCiclo();
    actualizarLCD();
    enviarDatos();
  }
}
