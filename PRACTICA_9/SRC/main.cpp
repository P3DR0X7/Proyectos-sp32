
#include <Arduino.h>
#include <DHT.h>
#include <ESP32Servo.h>


#define DHT_PIN 4
#define DHT_TYPE DHT11
#define SERVO_PIN 5

DHT dht(DHT_PIN, DHT_TYPE);
Servo servo;


const int SERVO_MIN = 90;   
const int SERVO_MAX = 180;  

int anguloActual = SERVO_MIN;
int anguloObjetivo = SERVO_MIN;


float temperatura = NAN;
float humedad = NAN;
float setpoint = 40.0;

bool sensorValido = false;
bool modoAutomatico = false;


float Kp = 5.0;
float Ki = 0.05;
float Kd = 0.0;


float error = 0;
float P = 0;
float I = 0;
float D = 0;
float salidaPID = 0;

float temperaturaAnterior = 0;
float derivadaFiltrada = 0;

bool primeraLectura = true;


unsigned long tiempoSensor = 0;
unsigned long tiempoEnvio = 0;
unsigned long tiempoServo = 0;

const unsigned long INTERVALO_SENSOR = 2000;
const unsigned long INTERVALO_ENVIO = 500;
const unsigned long INTERVALO_SERVO = 10;


float limitar(float valor, float minimo, float maximo) {
  return constrain(valor, minimo, maximo);
}


int convertirAngulo(float salida) {
  salida = limitar(salida, 0, 100);

  return round(
    SERVO_MIN + (salida / 100.0) * (SERVO_MAX - SERVO_MIN)
  );
}


void calcularPID(float dt) {

  error = setpoint - temperatura;

  P = Kp * error;

  float derivada = 0;

  if (!primeraLectura && dt > 0) {
    derivada = -(temperatura - temperaturaAnterior) / dt;
  }

  
  const float alpha = 0.25;

  derivadaFiltrada =
    alpha * derivada +
    (1.0 - alpha) * derivadaFiltrada;

  D = Kd * derivadaFiltrada;

 
  float integralPropuesta = I + Ki * error * dt;

  integralPropuesta = limitar(integralPropuesta, -100, 100);

  float salidaPropuesta = P + integralPropuesta + D;

 
  if (!((salidaPropuesta > 100 && error > 0) ||
        (salidaPropuesta < 0 && error < 0))) {
    I = integralPropuesta;
  }

  salidaPID = limitar(P + I + D, 0, 100);

  temperaturaAnterior = temperatura;
  primeraLectura = false;

  anguloObjetivo = convertirAngulo(salidaPID);
}


void leerSensor() {

  float nuevaTemperatura = dht.readTemperature();
  float nuevaHumedad = dht.readHumidity();

  if (isnan(nuevaTemperatura) || isnan(nuevaHumedad)) {

    sensorValido = false;
    salidaPID = 0;
    P = 0;
    I = 0;
    D = 0;

    anguloObjetivo = SERVO_MIN;
    primeraLectura = true;
    derivadaFiltrada = 0;

    return;
  }

  temperatura = nuevaTemperatura;
  humedad = nuevaHumedad;
  sensorValido = true;

  if (modoAutomatico) {
    calcularPID(INTERVALO_SENSOR / 1000.0);
  } else {
    error = setpoint - temperatura;
    P = 0;
    I = 0;
    D = 0;
    salidaPID = 0;
    anguloObjetivo = SERVO_MIN;
  }
}


void moverServo() {

  if (millis() - tiempoServo >= INTERVALO_SERVO) {

    tiempoServo = millis();

    if (anguloActual < anguloObjetivo) {
      anguloActual++;
      servo.write(anguloActual);
    }
    else if (anguloActual > anguloObjetivo) {
      anguloActual--;
      servo.write(anguloActual);
    }
  }
}


void enviarDatos() {

  Serial.print("DATA,");

  Serial.print(temperatura);
  Serial.print(",");

  Serial.print(humedad);
  Serial.print(",");

  Serial.print(setpoint);
  Serial.print(",");

  Serial.print(Kp);
  Serial.print(",");

  Serial.print(Ki);
  Serial.print(",");

  Serial.print(Kd);
  Serial.print(",");

  Serial.print(error);
  Serial.print(",");

  Serial.print(P);
  Serial.print(",");

  Serial.print(I);
  Serial.print(",");

  Serial.print(D);
  Serial.print(",");

  Serial.print(salidaPID);
  Serial.print(",");

  Serial.print(anguloActual);
  Serial.print(",");

  Serial.println(modoAutomatico ? "AUTO" : "STOP");
}


void procesarComando(String comando) {

  comando.trim();

  if (comando == "START") {

    modoAutomatico = true;

    I = 0;
    D = 0;
    derivadaFiltrada = 0;
    primeraLectura = true;

    if (sensorValido) {
      calcularPID(INTERVALO_SENSOR / 1000.0);
    }
  }

  else if (comando == "STOP") {

    modoAutomatico = false;

    P = 0;
    I = 0;
    D = 0;
    salidaPID = 0;

    anguloObjetivo = SERVO_MIN;
  }

  else if (comando.startsWith("SP:")) {
    setpoint = limitar(comando.substring(3).toFloat(), 0, 100);
  }

  else if (comando.startsWith("KP:")) {
    Kp = limitar(comando.substring(3).toFloat(), 0, 100);
  }

  else if (comando.startsWith("KI:")) {
    Ki = limitar(comando.substring(3).toFloat(), 0, 20);
  }

  else if (comando.startsWith("KD:")) {
    Kd = limitar(comando.substring(3).toFloat(), 0, 100);
  }
}


void recibirPython() {

  static String comando = "";

  while (Serial.available()) {

    char caracter = Serial.read();

    if (caracter == '\n') {
      procesarComando(comando);
      comando = "";
    }
    else if (caracter != '\r') {
      comando += caracter;
    }
  }
}


void setup() {

  Serial.begin(115200);

  dht.begin();

  servo.setPeriodHertz(50);
  servo.attach(SERVO_PIN, 500, 2400);

  anguloActual = SERVO_MIN;
  anguloObjetivo = SERVO_MIN;

  servo.write(SERVO_MIN);

  delay(500);

  tiempoSensor = millis();
  tiempoEnvio = millis();
  tiempoServo = millis();
}


void loop() {

  recibirPython();

  if (millis() - tiempoSensor >= INTERVALO_SENSOR) {

    tiempoSensor = millis();

    leerSensor();
  }

  moverServo();

  if (millis() - tiempoEnvio >= INTERVALO_ENVIO) {

    tiempoEnvio = millis();

    enviarDatos();
  }
}
