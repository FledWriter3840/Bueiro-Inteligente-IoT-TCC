#include <WiFi.h>
#include <HTTPClient.h>
#include <ESP32Servo.h>
#include <WiFiClientSecure.h>

const char* ssid = "Wokwi-GUEST";
const char* password = "";

// URL HTTP direta compatível com o simulador Wokwi
const char* apiUrl = "https://true-gifts-begin.loca.lt/sensores/leitura";

const int trigPin = 5;
const int echoPin = 18;
const int servoPin = 13;
const int ledVerde = 25;
const int ledVermelho = 26;

Servo servoMotor;

bool comandoLimpezaNaResposta(const String& resposta) {
  return resposta.indexOf("\"acionar_limpeza\":true") >= 0 ||
         resposta.indexOf("\"acionar_limpeza\": true") >= 0;
}

int duracaoLimpezaNaResposta(const String& resposta) {
  int inicio = resposta.indexOf("\"tempo_limpeza_segundos\":");
  if (inicio < 0) {
    inicio = resposta.indexOf("\"tempo_limpeza_segundos\": ");
  }
  if (inicio < 0) return 0;
  inicio = resposta.indexOf(":", inicio) + 1;
  return resposta.substring(inicio).toInt();
}

void setup() {
  Serial.begin(115200);
  Serial.println("\n--- Iniciando Bueiro Inteligente IoT ---");

  pinMode(trigPin, OUTPUT);
  pinMode(echoPin, INPUT);
  pinMode(ledVerde, OUTPUT);
  pinMode(ledVermelho, OUTPUT);

  servoMotor.attach(servoPin);
  servoMotor.write(0);

  WiFi.begin(ssid, password);
  Serial.print("Conectando ao Wi-Fi");
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("\n[OK] Wi-Fi conectado com sucesso!");
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
    WiFiClientSecure client;
    client.setInsecure(); // Pula a verificação estrita de certificado SSL

    HTTPClient http;
    http.setTimeout(10000);

    if (http.begin(client, apiUrl)) {
      http.addHeader("Content-Type", "application/json");
      
      // Cabeçalhos para evitar as telas de aviso dos túneis
      http.addHeader("bypass-tunnel-reminder", "true");  // Para LocalTunnel
      http.addHeader("ngrok-skip-browser-warning", "true"); // Para Ngrok
      http.addHeader("User-Agent", "ESP32-Bueiro");

      String jsonBody = "{\"valor_leitura\": " + String(valor, 2) +
                        ", \"unidade_medida\": \"cm\", \"id_sensor\": 1}";

      Serial.println(">> Enviando dados para a API...");
      int httpCode = http.POST(jsonBody);

      Serial.print(">> Codigo HTTP: ");
      Serial.println(httpCode);
      
      if (httpCode > 0) {
        String payload = http.getString();
        Serial.print(">> Resposta API: ");
        Serial.println(payload);
        int duracao = duracaoLimpezaNaResposta(payload);
        if (comandoLimpezaNaResposta(payload) && duracao > 0) {
          Serial.print("[IA] Iniciando ciclo proporcional de ");
          Serial.print(duracao);
          Serial.println(" segundos.");
          digitalWrite(ledVerde, LOW);
          digitalWrite(ledVermelho, HIGH);
          servoMotor.write(90);
          delay(duracao * 1000);
          servoMotor.write(0);
          digitalWrite(ledVermelho, LOW);
          digitalWrite(ledVerde, HIGH);
        }
      } else {
        Serial.print(">> Erro HTTP: ");
        Serial.println(http.errorToString(httpCode));
      }

      http.end();
    } else {
      Serial.println(">> Falha ao inicializar conexao");
    }
  }
}

void loop() {
  float distancia = lerDistancia();
  Serial.print("\nDistancia lida: ");
  Serial.print(distancia);
  Serial.println(" cm");

  enviarLeituraParaAPI(distancia);

  if (distancia < 15.0) {
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

  delay(5000);
}