#include <WiFi.h>
#include <WiFiClientSecure.h>
#include <HTTPClient.h>
#include <ESP32Servo.h>

const char* ssid = "Wokwi-GUEST";
const char* password = "";

const char* apiUrl = "https://around-figment-pelvis.ngrok-free.dev/sensores/leitura";

const int trigPin = 5;
const int echoPin = 18;
const int servoPin = 15;
const int ledPin = 2;

Servo grade;
WiFiClientSecure client;

void setup() {
  Serial.begin(115200);
  pinMode(trigPin, OUTPUT);
  pinMode(echoPin, INPUT);
  pinMode(ledPin, OUTPUT);
  grade.attach(servoPin);

  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.println("Conectando ao Wi-Fi...");
  }
  Serial.println("Wi-Fi conectado!");

  client.setInsecure(); // pula validação do certificado SSL (ok para testes)
}

float lerDistancia() {
  digitalWrite(trigPin, LOW);
  delayMicroseconds(2);
  digitalWrite(trigPin, HIGH);
  delayMicroseconds(10);
  digitalWrite(trigPin, LOW);

  long duracao = pulseIn(echoPin, HIGH);
  float distancia = duracao * 0.0343 / 2;
  return distancia;
}

void enviarLeitura(float valor) {
  if (WiFi.status() == WL_CONNECTED) {
    HTTPClient http;
    http.begin(client, apiUrl);  // usa o client seguro configurado
    http.addHeader("Content-Type", "application/json");

    String jsonBody = "{\"valor_leitura\": " + String(valor) +
                       ", \"unidade_medida\": \"cm\", \"id_sensor\": 1}";

    int httpCode = http.POST(jsonBody);
    Serial.print("Resposta da API: ");
    Serial.println(httpCode);
    if (httpCode > 0) {
      Serial.println(http.getString());
    }

    http.end();
  }
}

void loop() {
  float distancia = lerDistancia();
  Serial.print("Distancia: ");
  Serial.println(distancia);

  enviarLeitura(distancia);

  if (distancia < 5.0) {
    digitalWrite(ledPin, HIGH);
    grade.write(90);
  } else {
    digitalWrite(ledPin, LOW);
    grade.write(0);
  }

  delay(5000);
}