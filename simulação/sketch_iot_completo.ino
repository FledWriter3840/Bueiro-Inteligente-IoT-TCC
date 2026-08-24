#include <WiFi.h>
#include <WiFiClientSecure.h>
#include <HTTPClient.h>
#include <ESP32Servo.h>

// Configuração Wi-Fi (Padrão do simulador Wokwi)
const char* ssid = "Wokwi-GUEST";
const char* password = "";

// URL da sua API no ngrok
const char* apiUrl = "https://around-figment-pelvis.ngrok-free.dev/sensores/leitura";

// Pinos dos Sensores e Atuadores
const int trigPin = 5;
const int echoPin = 18;
const int servoPin = 13;
const int ledVerde = 25;
const int ledVermelho = 26;

Servo servoMotor;
WiFiClientSecure client;

void setup() {
  Serial.begin(115200);
  Serial.println("\n--- Iniciando Bueiro Inteligente IoT ---");

  pinMode(trigPin, OUTPUT);
  pinMode(echoPin, INPUT);
  pinMode(ledVerde, OUTPUT);
  pinMode(ledVermelho, OUTPUT);

  servoMotor.attach(servoPin);
  servoMotor.write(0);

  // Conectando ao Wi-Fi virtual do Wokwi
  WiFi.begin(ssid, password);
  Serial.print("Conectando ao Wi-Fi");
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("\n[OK] Wi-Fi conectado com sucesso!");
  Serial.print("IP: ");
  Serial.println(WiFi.localIP());

  client.setInsecure(); // Pula validação SSL para testes
}

float lerDistancia() {
  digitalWrite(trigPin, LOW);
  delayMicroseconds(2);
  digitalWrite(trigPin, HIGH);
  delayMicroseconds(10);
  digitalWrite(trigPin, LOW);

  long duracao = pulseIn(echoPin, HIGH);
  float distancia = duracao * 0.034 / 2;
  return distancia;
}

void enviarLeituraParaAPI(float valor) {
  if (WiFi.status() == WL_CONNECTED) {
    HTTPClient http;
    http.begin(client, apiUrl);
    http.addHeader("Content-Type", "application/json");

    String jsonBody = "{\"valor_leitura\": " + String(valor) +
                       ", \"unidade_medida\": \"cm\", \"id_sensor\": 1}";

    Serial.println("\n>> Enviando dados para a API...");
    int httpCode = http.POST(jsonBody);

    Serial.print(">> Codigo HTTP: ");
    Serial.println(httpCode);
    if (httpCode > 0) {
      String payload = http.getString();
      Serial.print(">> Resposta: ");
      Serial.println(payload);
    } else {
      Serial.print(">> Erro HTTP: ");
      Serial.println(http.errorToString(httpCode));
    }

    http.end();
  }
}

void loop() {
  float distancia = lerDistancia();
  Serial.print("\nDistancia lida: ");
  Serial.print(distancia);
  Serial.println(" cm");

  // Envia leitura para o banco MySQL via API FastAPI
  enviarLeituraParaAPI(distancia);

  // Lógica de alerta e atuação mecânica
  if (distancia < 15.0) { // Nível crítico (água subindo / resíduo acumulado)
    digitalWrite(ledVerde, LOW);
    digitalWrite(ledVermelho, HIGH);
    Serial.println("[ALERTA] Nivel critico! Abrindo comporta...");
    servoMotor.write(90);
  } else {
    digitalWrite(ledVerde, HIGH);
    digitalWrite(ledVermelho, LOW);
    Serial.println("[STATUS] Nivel normal.");
    servoMotor.write(0);
  }

  delay(5000); // Aguarda 5 segundos para a próxima leitura
}
