
#include <Arduino.h>
#include <DHT.h>
#include <Keypad.h>
#include <ESP32Servo.h>


#define DHT_PIN 4
#define DHT_TYPE DHT11
#define SERVO_PIN 5


DHT dht(DHT_PIN, DHT_TYPE);
Servo servo;


const byte FILAS = 4;
const byte COLUMNAS = 4;

char teclas[FILAS][COLUMNAS] = {
  {'1', '2', '3', 'A'},
  {'4', '5', '6', 'B'},
  {'7', '8', '9', 'C'},
  {'*', '0', '#', 'D'}
};

byte pinesFilas[FILAS] = {13, 14, 23, 32};
byte pinesColumnas[COLUMNAS] = {18, 19, 21, 22};

Keypad teclado = Keypad(
  makeKeymap(teclas),
  pinesFilas,
  pinesColumnas,
  FILAS,
  COLUMNAS
);


float temperatura = 0.0;
float humedad = 0.0;

float setpoint = 40.0;
float Kp = 5.0;

float error = 0.0;
float salida = 0.0;

int anguloActual = 0;
int anguloObjetivo = 0;

bool modoAutomatico = false;
bool sensorValido = false;

unsigned long tiempoSensor = 0;
unsigned long tiempoDatos = 0;
unsigned long tiempoServo = 0;

const unsigned long INTERVALO_SENSOR = 2000;
const unsigned long INTERVALO_DATOS = 500;
const unsigned long INTERVALO_SERVO = 10;

String entrada = "";
char parametroEditando = '\0';


void calcularControl() {

  if (!modoAutomatico || !sensorValido) {
    error = 0;
    salida = 0;
    anguloObjetivo = 0;
    return;
  }

  
  error = setpoint - temperatura;

  
  salida = Kp * error;

 
  salida = constrain(salida, 0.0, 100.0);

 
  anguloObjetivo = (int)round(
    (salida / 100.0) * 180.0
  );

  anguloObjetivo = constrain(
    anguloObjetivo, 0, 180
  );
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


void leerSensor() {

  if (millis() - tiempoSensor >= INTERVALO_SENSOR) {
    tiempoSensor = millis();

    float nuevaTemperatura = dht.readTemperature();
    float nuevaHumedad = dht.readHumidity();

    if (!isnan(nuevaTemperatura) && !isnan(nuevaHumedad)) {
      temperatura = nuevaTemperatura;
      humedad = nuevaHumedad;
      sensorValido = true;
    } else {
      sensorValido = false;
    }
  }
}


void enviarDatos() {

  if (millis() - tiempoDatos >= INTERVALO_DATOS) {
    tiempoDatos = millis();

    Serial.print("DATA,");
    Serial.print(temperatura, 1);
    Serial.print(",");
    Serial.print(humedad, 1);
    Serial.print(",");
    Serial.print(setpoint, 1);
    Serial.print(",");
    Serial.print(Kp, 2);
    Serial.print(",");
    Serial.print(error, 1);
    Serial.print(",");
    Serial.print(salida, 1);
    Serial.print(",");
    Serial.print(anguloActual);
    Serial.print(",");
    Serial.println(modoAutomatico ? "AUTO" : "STOP");
  }
}


void procesarComando(String comando) {

  comando.trim();

  if (comando == "START") {
    modoAutomatico = true;
  }
  else if (comando == "STOP") {
    modoAutomatico = false;
    anguloObjetivo = 0;
  }
  else if (comando.startsWith("SP:")) {
    float valor = comando.substring(3).toFloat();

    if (valor >= 0 && valor <= 100) {
      setpoint = valor;
    }
  }
  else if (comando.startsWith("KP:")) {
    float valor = comando.substring(3).toFloat();

    if (valor >= 0 && valor <= 20) {
      Kp = valor;
    }
  }
}

void recibirPython() {

  while (Serial.available()) {
    String comando = Serial.readStringUntil('\n');
    procesarComando(comando);
  }
}


void procesarTeclado() {

  char tecla = teclado.getKey();

  if (!tecla) return;

  if (tecla == 'A' && parametroEditando == '\0') {
    parametroEditando = 'A';
    entrada = "";
    return;
  }

  if (tecla == 'B' && parametroEditando == '\0') {
    parametroEditando = 'B';
    entrada = "";
    return;
  }

  if (tecla == 'C') {
    if (parametroEditando != '\0') {
      entrada = "";
    } else {
      modoAutomatico = true;
    }
    return;
  }

  if (tecla == 'D') {
    if (parametroEditando != '\0') {
      parametroEditando = '\0';
      entrada = "";
    } else {
      modoAutomatico = false;
      anguloObjetivo = 0;
    }
    return;
  }

  if (tecla == '#') {

    if (parametroEditando != '\0' && entrada.length() > 0) {
      float valor = entrada.toFloat();

      if (parametroEditando == 'A' &&
          valor >= 0 && valor <= 100) {
        setpoint = valor;
      }

      if (parametroEditando == 'B' &&
          valor >= 0 && valor <= 20) {
        Kp = valor;
      }

      parametroEditando = '\0';
      entrada = "";
    }
    return;
  }

  if (tecla == '*') {

    if (parametroEditando != '\0' &&
        entrada.indexOf('.') == -1) {

      if (entrada.length() == 0) {
        entrada = "0";
      }

      entrada += ".";
    }
    return;
  }

  if (tecla >= '0' && tecla <= '9') {

    if (parametroEditando != '\0' &&
        entrada.length() < 7) {
      entrada += tecla;
    }
  }
}


void setup() {

  Serial.begin(115200);
  Serial.setTimeout(20);

  dht.begin();

  servo.setPeriodHertz(50);
  servo.attach(SERVO_PIN, 500, 2500);

  anguloActual = 0;
  anguloObjetivo = 0;

  servo.write(0);

  tiempoSensor = millis() - INTERVALO_SENSOR;

  Serial.println("SISTEMA INICIADO");
}


void loop() {

  recibirPython();
  leerSensor();
  procesarTeclado();

  calcularControl();
  moverServo();
  enviarDatos();
}
