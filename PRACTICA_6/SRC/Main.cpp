#include <DHT.h>
#include <Keypad.h>
#include <ESP32Servo.h>


#define DHTPIN 4
#define DHTTYPE DHT11

DHT dht(DHTPIN, DHTTYPE);


#define SERVO_PIN 5
Servo servo;


#define RELE2 26
#define RELE3 27

// Relés activos en LOW
#define RELE_ON LOW
#define RELE_OFF HIGH

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


float limiteLOW = 20;
float limiteHIGH = 30;
float temperatura = NAN;
float humedad = NAN;

bool modoAutomatico = true;
bool estadoHIGH = false;

int anguloActual = 180;
int anguloObjetivo = 180;

String entrada = "";
char configurando = ' ';


unsigned long tiempoSensor = 0;
unsigned long tiempoServo = 0;

const unsigned long INTERVALO_SENSOR = 2000;
const unsigned long INTERVALO_SERVO = 15;


void imprimirLimites() {
  Serial.print("LIMITES:");
  Serial.print(limiteLOW);
  Serial.print(",");
  Serial.println(limiteHIGH);
}


void actualizarRelevadores() {
  if (estadoHIGH) {
    digitalWrite(RELE2, RELE_ON);
    digitalWrite(RELE3, RELE_ON);
    Serial.println("RELES:ON,ON");
  } else {
    digitalWrite(RELE2, RELE_OFF);
    digitalWrite(RELE3, RELE_OFF);
    Serial.println("RELES:OFF,OFF");
  }
}


void aplicarEstado(bool alto) {
  estadoHIGH = alto;

  if (alto) {
    anguloObjetivo = 0;
    Serial.println("ESTADO:HIGH");
    Serial.println("ANGULO_OBJETIVO:0");
  } else {
    anguloObjetivo = 180;
    Serial.println("ESTADO:LOW");
    Serial.println("ANGULO_OBJETIVO:180");
  }

  actualizarRelevadores();
}


void actualizarServo() {
  if (millis() - tiempoServo >= INTERVALO_SERVO) {
    tiempoServo = millis();

    if (anguloActual < anguloObjetivo) {
      anguloActual++;
      servo.write(anguloActual);
    } else if (anguloActual > anguloObjetivo) {
      anguloActual--;
      servo.write(anguloActual);
    }
  }
}


void leerTemperatura() {
  if (millis() - tiempoSensor >= INTERVALO_SENSOR) {
    tiempoSensor = millis();

    humedad = dht.readHumidity();
    temperatura = dht.readTemperature();

    if (isnan(temperatura) || isnan(humedad)) {
      Serial.println("ERROR_SENSOR");
      return;
    }

    Serial.print("TEMP:");
    Serial.println(temperatura);

    Serial.print("HUM:");
    Serial.println(humedad);

    if (modoAutomatico) {
      if (temperatura >= limiteHIGH && !estadoHIGH) {
        aplicarEstado(true);
      }

      if (temperatura <= limiteLOW && estadoHIGH) {
        aplicarEstado(false);
      }
    }
  }
}


void guardarTemperatura() {
  if (entrada.length() == 0) {
    Serial.println("ERROR:ENTRADA_VACIA");
    return;
  }

  float valor = entrada.toFloat();

  if (valor < 0 || valor > 80) {
    Serial.println("ERROR:RANGO_0_80");
    entrada = "";
    return;
  }

  if (configurando == 'A') {
    if (valor >= limiteHIGH) {
      Serial.println("ERROR:LOW_DEBE_SER_MENOR");
    } else {
      limiteLOW = valor;
      Serial.println("LOW_ACTUALIZADO");
      imprimirLimites();
    }
  }

  if (configurando == 'B') {
    if (valor <= limiteLOW) {
      Serial.println("ERROR:HIGH_DEBE_SER_MAYOR");
    } else {
      limiteHIGH = valor;
      Serial.println("HIGH_ACTUALIZADO");
      imprimirLimites();
    }
  }

  entrada = "";
  configurando = ' ';
}


void procesarTeclado() {
  char tecla = teclado.getKey();

  if (!tecla) {
    return;
  }

  
  if (tecla == 'A') {
    configurando = 'A';
    entrada = "";
    Serial.println("CONFIGURANDO:LOW");
    return;
  }

  
  if (tecla == 'B') {
    configurando = 'B';
    entrada = "";
    Serial.println("CONFIGURANDO:HIGH");
    return;
  }

  
  if (tecla == 'C') {
    modoAutomatico = true;
    Serial.println("MODO_AUTO");

    
    if (!isnan(temperatura)) {
      if (temperatura >= limiteHIGH) {
        aplicarEstado(true);
      } else if (temperatura <= limiteLOW) {
        aplicarEstado(false);
      }
    }
    return;
  }

  
  if (tecla == 'D') {
    modoAutomatico = false;
    estadoHIGH = false;
    anguloObjetivo = 180;
    actualizarRelevadores();
    Serial.println("MODO_DETENIDO");
    Serial.println("ESTADO:DETENIDO");
    Serial.println("ANGULO_OBJETIVO:180");
    return;
  }

  
  if (tecla == '*') {
    entrada = "";
    Serial.println("ENTRADA_BORRADA");
    return;
  }

  
  if (tecla == '#') {
    guardarTemperatura();
    return;
  }

  
  if (tecla >= '0' && tecla <= '9' && configurando != ' ') {
    if (entrada.length() < 3) {
      entrada += tecla;
      Serial.print("ENTRADA:");
      Serial.println(entrada);
    }
  }
}


void setup() {
  Serial.begin(115200);

  pinMode(RELE2, OUTPUT);
  pinMode(RELE3, OUTPUT);

  digitalWrite(RELE2, RELE_OFF);
  digitalWrite(RELE3, RELE_OFF);

  dht.begin();

  servo.setPeriodHertz(50);
  servo.attach(SERVO_PIN, 500, 2400);
  servo.write(180);

  anguloActual = 180;
  anguloObjetivo = 180;

  Serial.println();
  Serial.println("SISTEMA_INICIADO");
  Serial.println("MODO_AUTO");

  imprimirLimites();

  
  tiempoSensor = millis() - INTERVALO_SENSOR;
}


void loop() {
  procesarTeclado();
  leerTemperatura();
  actualizarServo();
}
