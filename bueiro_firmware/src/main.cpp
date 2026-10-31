#include <WiFi.h>
#include <HTTPClient.h>
#include <ESP32Servo.h>
#include <WebServer.h>
#include <esp_camera.h>
#include <img_converters.h>
#include <esp32-hal-psram.h>

const char* ssid = "";
const char* password = "";
// Troque pelo IPv4 do computador que executa a API, na mesma rede Wi-Fi.
const char* apiBaseUrl = "";

constexpr bool ENABLE_API = true;
constexpr bool ENABLE_CLEANING = false;

WebServer cameraServer(80);
bool cameraReady = false;
bool cameraServerStarted = false;
unsigned long lastCameraStatusLog = 0;
unsigned long lastWiFiAttempt = 0;
unsigned long lastSensorRead = 0;
unsigned long lastPhotoUpload = 0;
int lastReadingId = 0;

constexpr unsigned long cameraStatusIntervalMs = 30000UL;
constexpr unsigned long wifiRetryIntervalMs = 30000UL;
constexpr unsigned long sensorReadIntervalMs = 5000UL;
constexpr unsigned long photoUploadIntervalMs = 60000UL;

// Camera pinout used by the common ESP32-CAM OV2640 layout.
constexpr int cameraPinPwdn = 32;
constexpr int cameraPinReset = -1;
constexpr int cameraPinXclk = 0;
constexpr int cameraPinSccbSda = 26;
constexpr int cameraPinSccbScl = 27;
constexpr int cameraPinY9 = 35;
constexpr int cameraPinY8 = 34;
constexpr int cameraPinY7 = 39;
constexpr int cameraPinY6 = 36;
constexpr int cameraPinY5 = 21;
constexpr int cameraPinY4 = 19;
constexpr int cameraPinY3 = 18;
constexpr int cameraPinY2 = 5;
constexpr int cameraPinVsync = 25;
constexpr int cameraPinHref = 23;
constexpr int cameraPinPclk = 22;
constexpr uint8_t cameraFlashPin = 4;
constexpr uint8_t cameraFlashBrightnessThreshold = 60;
constexpr unsigned long cameraFlashSettleMs = 150UL;

// GPIO 13/14 are available on this ESP32-CAM when the microSD interface is unused.
constexpr uint8_t trigPin = 14;
constexpr uint8_t echoPin = 13;
constexpr uint8_t servoPin = 12;

constexpr unsigned long echoTimeoutUs = 30000UL;
constexpr float minDistanceCm = 2.0F;
constexpr float maxDistanceCm = 450.0F;

Servo servoMotor;

bool iniciarCamera() {
  camera_config_t config = {};
  config.ledc_channel = LEDC_CHANNEL_0;
  config.ledc_timer = LEDC_TIMER_0;
  config.pin_d0 = cameraPinY2;
  config.pin_d1 = cameraPinY3;
  config.pin_d2 = cameraPinY4;
  config.pin_d3 = cameraPinY5;
  config.pin_d4 = cameraPinY6;
  config.pin_d5 = cameraPinY7;
  config.pin_d6 = cameraPinY8;
  config.pin_d7 = cameraPinY9;
  config.pin_xclk = cameraPinXclk;
  config.pin_pclk = cameraPinPclk;
  config.pin_vsync = cameraPinVsync;
  config.pin_href = cameraPinHref;
  config.pin_sccb_sda = cameraPinSccbSda;
  config.pin_sccb_scl = cameraPinSccbScl;
  config.pin_pwdn = cameraPinPwdn;
  config.pin_reset = cameraPinReset;
  config.xclk_freq_hz = 20000000;
  config.pixel_format = PIXFORMAT_JPEG;
  config.frame_size = FRAMESIZE_VGA;
  config.jpeg_quality = 15;
  config.fb_count = 1;

  const esp_err_t resultado = esp_camera_init(&config);
  if (resultado != ESP_OK) {
    Serial.printf("[CAMERA] Falha ao iniciar: 0x%x\n", resultado);
    return false;
  }

  Serial.println("[CAMERA] Inicializada.");
  return true;
}

float calcularBrilhoMedio(camera_fb_t* frame) {
  if (frame == nullptr || frame->format != PIXFORMAT_JPEG) {
    Serial.println("[CAMERA] Nao foi possivel analisar o brilho do quadro.");
    return -1.0F;
  }

  const size_t pixels = static_cast<size_t>(frame->width) * frame->height;
  if (pixels == 0 || pixels > SIZE_MAX / 3) {
    Serial.println("[CAMERA] Dimensoes invalidas no quadro de teste.");
    return -1.0F;
  }

  uint8_t* rgb = static_cast<uint8_t*>(ps_malloc(pixels * 3));
  if (rgb == nullptr) {
    Serial.println(
        "[CAMERA] Sem PSRAM para analisar o brilho; flash adaptativo ignorado.");
    return -1.0F;
  }

  const bool convertido = fmt2rgb888(frame->buf, frame->len, frame->format, rgb);
  if (!convertido) {
    free(rgb);
    Serial.println("[CAMERA] Falha ao converter quadro para RGB.");
    return -1.0F;
  }

  uint64_t somaLuminosidade = 0;
  for (size_t indice = 0; indice < pixels; ++indice) {
    const size_t inicio = indice * 3;
    const uint8_t vermelho = rgb[inicio];
    const uint8_t verde = rgb[inicio + 1];
    const uint8_t azul = rgb[inicio + 2];
    somaLuminosidade +=
        (299U * vermelho + 587U * verde + 114U * azul) / 1000U;
  }
  free(rgb);
  return static_cast<float>(somaLuminosidade) / static_cast<float>(pixels);
}

camera_fb_t* capturarFotoComFlash() {
  digitalWrite(cameraFlashPin, LOW);
  camera_fb_t* quadroTeste = esp_camera_fb_get();
  if (quadroTeste == nullptr) {
    Serial.println("[CAMERA] Falha ao capturar quadro para medir luminosidade.");
    return nullptr;
  }

  const float brilhoMedio = calcularBrilhoMedio(quadroTeste);
  esp_camera_fb_return(quadroTeste);

  if (brilhoMedio < 0.0F) {
    Serial.println(
        "[CAMERA] Brilho indisponivel; captura definitiva sem flash.");
  } else {
    Serial.printf("[CAMERA] Luminosidade media: %.1f/255\n", brilhoMedio);
    if (brilhoMedio < cameraFlashBrightnessThreshold) {
      digitalWrite(cameraFlashPin, HIGH);
      Serial.println("[CAMERA] Ambiente escuro; flash ligado.");
      delay(cameraFlashSettleMs);
    } else {
      Serial.println("[CAMERA] Iluminacao suficiente; flash desligado.");
    }
  }

  camera_fb_t* foto = esp_camera_fb_get();
  digitalWrite(cameraFlashPin, LOW);
  if (foto == nullptr) {
    Serial.println("[CAMERA] Falha ao capturar foto definitiva.");
  }
  return foto;
}

void configurarServidorCamera() {
  cameraServer.on("/", HTTP_GET, []() {
    cameraServer.send(200, "text/html", R"rawliteral(
<!doctype html>
<html lang="pt-BR">
<head>
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta charset="utf-8">
  <title>Teste da ESP32-CAM</title>
  <style>
    body { font-family: sans-serif; max-width: 720px; margin: 2rem auto; padding: 0 1rem; }
    img { width: 100%; height: auto; background: #222; }
    button { padding: .7rem 1rem; margin: 1rem 0; }
  </style>
</head>
<body>
  <h1>Teste da ESP32-CAM</h1>
  <img id="foto" src="/capture" alt="Captura da camera">
  <br>
  <button onclick="document.getElementById('foto').src='/capture?t='+Date.now()">Nova captura</button>
</body>
</html>
)rawliteral");
  });

  cameraServer.on("/capture", HTTP_GET, []() {
    camera_fb_t* frame = capturarFotoComFlash();
    if (frame == nullptr) {
      cameraServer.send(500, "text/plain", "Falha ao capturar imagem.");
      Serial.println("[CAMERA] Falha ao capturar imagem.");
      return;
    }

    WiFiClient client = cameraServer.client();
    client.printf(
        "HTTP/1.1 200 OK\r\n"
        "Content-Type: image/jpeg\r\n"
        "Content-Length: %u\r\n"
        "Cache-Control: no-store\r\n"
        "Connection: close\r\n\r\n",
        static_cast<unsigned int>(frame->len));
    client.write(frame->buf, frame->len);
    esp_camera_fb_return(frame);
  });

  cameraServer.onNotFound([]() {
    cameraServer.send(404, "text/plain", "Pagina nao encontrada.");
  });

  cameraServer.begin();
  cameraServerStarted = true;
  Serial.println("[CAMERA] Servidor iniciado na porta 80.");
  Serial.print("[CAMERA] Abra no navegador: http://");
  Serial.println(WiFi.localIP());
}

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

void executarLimpeza(int duracaoSegundos) {
  if (!ENABLE_CLEANING || duracaoSegundos <= 0) return;

  const int duracaoSegura = min(duracaoSegundos, 60);
  Serial.printf("[LIMPEZA] Acionando servo por %d segundos.\n", duracaoSegura);
  servoMotor.write(90);
  delay(static_cast<unsigned long>(duracaoSegura) * 1000UL);
  servoMotor.write(0);
}

bool lerDistancia(float& distanciaCm) {
  digitalWrite(trigPin, LOW);
  delayMicroseconds(3);
  digitalWrite(trigPin, HIGH);
  delayMicroseconds(10);
  digitalWrite(trigPin, LOW);

  const unsigned long duracao = pulseIn(echoPin, HIGH, echoTimeoutUs);
  if (duracao == 0) {
    return false;
  }

  distanciaCm = duracao * 0.0343F / 2.0F;
  return distanciaCm >= minDistanceCm && distanciaCm <= maxDistanceCm;
}

void enviarLeituraParaAPI(float valor) {
  if (!ENABLE_API) return;

  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("[API] Sem Wi-Fi; leitura nao enviada.");
    return;
  }

  WiFiClient client;

  HTTPClient http;
  http.setTimeout(30000);

  if (!http.begin(client, String(apiBaseUrl) + "/sensores/leitura")) {
    Serial.println("[API] Falha ao iniciar conexao.");
    return;
  }

  http.addHeader("Content-Type", "application/json");
  http.addHeader("User-Agent", "ESP32-Bueiro");

  const String jsonBody = "{\"valor_leitura\": " + String(valor, 2) +
                          ", \"unidade_medida\": \"cm\", \"id_sensor\": 1}";

  Serial.println("[API] Enviando leitura...");
  const int httpCode = http.POST(jsonBody);
  Serial.printf("[API] Codigo HTTP: %d\n", httpCode);

  if (httpCode >= 200 && httpCode < 300) {
    const String payload = http.getString();
    Serial.print("[API] Resposta: ");
    Serial.println(payload);

    const int campoId = payload.indexOf("\"id_leitura\"");
    if (campoId >= 0) {
      const int doisPontos = payload.indexOf(":", campoId);
      if (doisPontos >= 0) {
        lastReadingId = payload.substring(doisPontos + 1).toInt();
      }
    }

    if (ENABLE_CLEANING && comandoLimpezaNaResposta(payload)) {
      executarLimpeza(duracaoLimpezaNaResposta(payload));
    }
  } else {
    Serial.print("[API] Erro: ");
    Serial.println(http.errorToString(httpCode));
  }

  http.end();
}

void enviarFotoParaAPI() {
  if (!ENABLE_API) return;
  if (!cameraReady) {
    Serial.println("[CAMERA] Foto nao enviada: camera indisponivel.");
    return;
  }
  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("[API] Sem Wi-Fi; foto nao enviada.");
    return;
  }

  camera_fb_t* frame = capturarFotoComFlash();
  if (frame == nullptr) {
    Serial.println("[CAMERA] Falha ao capturar foto para a API.");
    return;
  }

  String imageUrl = String(apiBaseUrl) + "/camera/imagens?camera_id=1";
  if (lastReadingId > 0) {
    imageUrl += "&id_leitura=" + String(lastReadingId);
  }

  WiFiClient client;
  HTTPClient http;
  http.setTimeout(15000);

  if (!http.begin(client, imageUrl)) {
    Serial.println("[API] Falha ao iniciar envio da foto.");
    esp_camera_fb_return(frame);
    return;
  }

  http.addHeader("Content-Type", "image/jpeg");
  http.addHeader("User-Agent", "ESP32-Bueiro");
  Serial.printf("[API] Enviando foto JPEG (%u bytes)...\n",
                static_cast<unsigned int>(frame->len));
  const int httpCode = http.POST(frame->buf, frame->len);
  Serial.printf("[API] Resultado do envio da foto: HTTP %d\n", httpCode);

  if (httpCode >= 200 && httpCode < 300) {
    const String payload = http.getString();
    Serial.print("[API] Resultado da analise visual: ");
    Serial.println(payload);
    if (payload.indexOf("\"possivel_interferencia_sensor\":true") >= 0) {
      Serial.println(
          "[SENSOR] Residuo detectado na foto; confira a leitura ultrassonica.");
    }
  } else if (httpCode > 0) {
    Serial.println(http.getString());
  } else {
    Serial.print("[API] Erro no envio da foto: ");
    Serial.println(http.errorToString(httpCode));
  }

  http.end();
  esp_camera_fb_return(frame);
}

void setupDispositivo() {
  Serial.println("\n--- Bueiro Inteligente: camera + sensor + API ---");

  pinMode(trigPin, OUTPUT);
  pinMode(echoPin, INPUT);
  digitalWrite(trigPin, LOW);
  pinMode(cameraFlashPin, OUTPUT);
  digitalWrite(cameraFlashPin, LOW);

  if (ENABLE_CLEANING) {
    servoMotor.attach(servoPin);
    servoMotor.write(0);
  }

  cameraReady = iniciarCamera();
  if (!cameraReady) {
    Serial.println("[CAMERA] Verifique o modelo da placa e o encaixe da camera.");
  }

  WiFi.mode(WIFI_STA);
  WiFi.setAutoReconnect(true);
  WiFi.begin(ssid, password);
  lastWiFiAttempt = millis();
  lastSensorRead = millis() - sensorReadIntervalMs;
  lastPhotoUpload = millis();
  Serial.printf("[Wi-Fi] Tentando conectar a rede \"%s\".\n", ssid);
  Serial.printf("[API] Destino configurado: %s\n", apiBaseUrl);
}

void loopDispositivo() {
  const unsigned long agora = millis();

  if (WiFi.status() == WL_CONNECTED) {
    if (!cameraServerStarted && cameraReady) {
      Serial.println("[Wi-Fi] Conectado.");
      configurarServidorCamera();
    }
  } else if (agora - lastWiFiAttempt >= wifiRetryIntervalMs) {
    lastWiFiAttempt = agora;
    Serial.printf("[Wi-Fi] Ainda desconectado (estado %d); tentando novamente.\n",
                  static_cast<int>(WiFi.status()));
    WiFi.disconnect();
    WiFi.begin(ssid, password);
  }

  if (cameraServerStarted) {
    cameraServer.handleClient();
  }

  if (agora - lastSensorRead >= sensorReadIntervalMs) {
    float distanciaCm = 0.0F;
    if (lerDistancia(distanciaCm)) {
      Serial.printf("[SENSOR] Distancia: %.2f cm\n", distanciaCm);
      enviarLeituraParaAPI(distanciaCm);
    } else {
      Serial.println("[SENSOR] Leitura invalida/sem eco; ignorada.");
    }
    lastSensorRead = millis();
  }

  if (agora - lastPhotoUpload >= photoUploadIntervalMs) {
    enviarFotoParaAPI();
    lastPhotoUpload = millis();
  }

  if (agora - lastCameraStatusLog >= cameraStatusIntervalMs) {
    lastCameraStatusLog = agora;
    Serial.printf("[STATUS] Camera: %s; Wi-Fi: %s (estado %d)",
                  cameraReady ? "OK" : "falha",
                  WiFi.status() == WL_CONNECTED ? "conectado" : "desconectado",
                  static_cast<int>(WiFi.status()));
    if (WiFi.status() == WL_CONNECTED) {
      Serial.printf("; pagina local: http://%s",
                    WiFi.localIP().toString().c_str());
    }
    Serial.println();
  }
}

void setup() {
  Serial.begin(115200);
  Serial.printf("[BOOT] Motivo do reset: %d\n", static_cast<int>(esp_reset_reason()));
  delay(500);

  setupDispositivo();
}

void loop() {
  loopDispositivo();
}
