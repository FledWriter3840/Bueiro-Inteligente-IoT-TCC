# Integração da ESP32-CAM com sensor e API

O firmware integrado envia uma leitura válida do sensor ultrassônico a cada 5
segundos e uma foto JPEG a cada 60 segundos. A foto é associada à leitura mais
recente aceita pela API.

## Preparar o banco existente

O arquivo `banco de dados/bueiro_db.sql` já contém o esquema atualizado e um
registro inicial do sensor de ID 1. Se o banco já foi criado com a versão
anterior desse SQL, aplique uma vez:

```sql
ALTER TABLE leiturasensor
  ADD COLUMN unidade_medida VARCHAR(20) NOT NULL DEFAULT 'cm';

ALTER TABLE registroimagem
  ADD COLUMN id_leitura INT NULL,
  ADD COLUMN tipo_residuo VARCHAR(50) NULL,
  ADD COLUMN confianca_ia FLOAT NULL,
  ADD COLUMN status_analise VARCHAR(30) NULL,
  ADD INDEX fk_imagem_leitura (id_leitura),
  ADD CONSTRAINT fk_imagem_leitura
    FOREIGN KEY (id_leitura) REFERENCES leiturasensor (id_leitura);

INSERT INTO sensor (id_sensor, tipo_sensor, status_sensor)
SELECT 1, 'Ultrassonico', 'Ativo'
WHERE NOT EXISTS (SELECT 1 FROM sensor WHERE id_sensor = 1);
```

Não execute o `ALTER TABLE` se essas colunas já existirem. A API usa a
`DATABASE_URL` configurada no `.env` para persistir leituras e metadados das
imagens no MySQL.

## Executar a API

Na pasta `bueiro_inteligente_api`, inicie o servidor acessível pela rede local:

```powershell
.\venv\Scripts\python.exe -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Se o Firewall do Windows perguntar, permita o acesso à rede privada. A API
recebe leituras em `POST /sensores/leitura` e fotos JPEG em
`POST /camera/imagens`. Os arquivos de imagem ficam no servidor em
`app/storage/images`; o MySQL guarda o caminho, a câmera e, quando disponível,
o ID da leitura associada. As fotos podem ser listadas em
`GET /camera/imagens` e abertas em `GET /camera/imagens/{id_imagem}`.

## Configurar o ESP32

No `bueiro_firmware/src/main.cpp`:

1. Configure `apiBaseUrl` com o IPv4 do computador que executa a API, por
   exemplo `http://192.168.1.20:8000` (use o endereço real da sua rede).
2. Configure `ssid` e `password` com a rede Wi-Fi à qual o computador também
   está conectado.
3. Grave o firmware na placa e reinicie-a.

O endereço usado pelo ESP32 é HTTP na rede local; não use `localhost`, pois
nesse caso ele apontaria para o próprio ESP32. O monitor serial, em 115200
baud, informa o resultado das leituras/envios e o IP da página local da câmera.

## Flash automático da ESP32-CAM

Antes de cada foto enviada à API ou exibida em `/capture`, o firmware captura
um quadro JPEG de teste, converte os pixels para RGB888 e calcula a média de
luminosidade em escala de cinza. Se a média for inferior a `60/255`, acende o
LED de flash no GPIO 4, aguarda 150 ms e captura a foto definitiva. Em
ambientes mais claros, mantém o flash apagado. O LED é desligado logo após a
captura definitiva.

A análise do quadro VGA usa PSRAM. Se não houver PSRAM disponível, o quadro
falhar na conversão ou não puder ser analisado, o firmware registra o motivo e
faz a captura definitiva sem flash. O limite pode ser ajustado pela constante
`cameraFlashBrightnessThreshold` em `bueiro_firmware/src/main.cpp`; teste esse
valor na iluminação e montagem reais. O GPIO 4 também é ligado ao sinal SD
DATA1 em placas ESP32-CAM comuns, portanto não use a interface microSD enquanto
o flash estiver habilitado.

O endpoint da API grava o JPEG no disco do servidor e registra seus metadados
no MySQL; o arquivo binário não é armazenado como BLOB no banco. Se a rede ou a
API estiver indisponível durante o envio, o firmware registra o erro no Monitor
Serial e não mantém uma fila local para reenvio posterior.

## Treinar a identificação visual de resíduos

A API classifica cada imagem recebida usando um modelo local supervisionado.
Para habilitar a classificação, prepare fotos reais do bueiro organizadas por
classe com estes nomes exatos:

```text
dataset_residuos/
  plastico/
  papel_papelao/
  metal/
  vidro/
  organico/
  sem_residuo/
```

Coloque pelo menos dez imagens JPEG ou PNG em cada pasta para permitir o
treinamento e a avaliação inicial. Esse mínimo não garante precisão para uso
real: reúna idealmente 50 a 100 ou mais imagens representativas por classe,
em diferentes posições, iluminação, condições de umidade e distâncias. Evite
que fotos quase idênticas apareçam tanto no treino quanto na avaliação. Cada
imagem deve conter principalmente a classe indicada.

Com o ambiente virtual da API ativo, execute a partir de
`bueiro_inteligente_api`:

```powershell
.\venv\Scripts\python.exe -m app.ml.train_residuos --dataset .\dataset_residuos
```

O modelo será salvo por padrão em
`app/ml/residuos_modelo.joblib`. Para outro caminho, use `--modelo` ou configure
`RESIDUOS_MODEL_PATH` no `.env`. Reinicie a API após o treinamento. A variável
`RESIDUOS_CONFIDENCE_THRESHOLD` ajusta o limiar de confiança (padrão `0.60`);
abaixo dele, o resultado fica como `Indefinido` e `Baixa confiança`.

As rotas `POST /camera/imagens` e `GET /camera/imagens` retornam a classe, a
confiança e o estado da análise. `possivel_interferencia_sensor` sinaliza que a
foto contém um resíduo reconhecido, mas **não altera nem corrige
automaticamente a distância ultrassônica**: a presença visual de um resíduo
não prova que ele está no campo de medição do sensor. Sem o arquivo do modelo,
a foto ainda é salva e a análise fica com o estado `Sem modelo`. Antes de usar
o resultado para decisões automáticas, valide o modelo com fotos de campo
separadas das usadas no treinamento e faça a calibração física do sensor.
