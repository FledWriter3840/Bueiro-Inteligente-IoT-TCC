# Funcionamento do Bueiro Inteligente e da API

## Visao geral

O sistema possui quatro partes principais:

```text
Sensor ultrassonico
        |
        v
ESP32 / Wokwi
        |
        | HTTP
        v
API FastAPI
        |
        v
Banco MySQL + modelos de previsao
        |
        v
Comando de limpeza para o ESP32
```

## 1. Medicao do bueiro

O sensor HC-SR04 mede a distancia entre ele e a agua ou os residuos.

- Distancia grande: bueiro mais vazio.
- Distancia pequena: nivel de agua ou residuos mais alto.
- Distancia menor que `15 cm`: situacao critica local.

O ESP32 realiza uma leitura a cada 5 segundos e envia os dados para:

```text
POST /sensores/leitura
```

Exemplo:

```json
{
  "id_sensor": 1,
  "valor_leitura": 60.0,
  "unidade_medida": "cm"
}
```

Como o bueiro e fixo, sua localizacao e configurada no `.env`:

```env
BUEIRO_LATITUDE=-23.5505
BUEIRO_LONGITUDE=-46.6333
```

Essas coordenadas sao utilizadas nas consultas de clima, topografia, historico de alagamentos e uso do solo. Nao e necessario instalar GPS em um bueiro fixo.

## 2. Processamento da leitura

Ao receber uma leitura, a API:

1. Salva o valor no MySQL.
2. Busca as leituras recentes do sensor.
3. Calcula a tendencia de subida ou descida.
4. Executa a IA multivariada.
5. Executa o modelo de Machine Learning.
6. Compara os dois resultados.
7. Define o risco final.
8. Decide se deve iniciar um ciclo de limpeza.
9. Retorna o comando para o ESP32.

Esse fluxo esta implementado principalmente em `app/routers/sensores.py` e `app/ai_predictor.py`.

## 3. IA multivariada

A IA multivariada calcula seis dimensoes de risco:

| Fonte | Peso |
|---|---:|
| Sensor IoT | 30% |
| Clima | 25% |
| Dados temporais | 10% |
| Historico de alagamentos | 15% |
| Topografia | 10% |
| Uso do solo | 10% |

### Sensor IoT

Analisa a distancia atual, a velocidade de subida do nivel e o nivel de residuos registrado na compactacao.

### Clima

A OpenWeatherMap fornece chuva atual, previsao de chuva para as proximas 3 horas, umidade e vento.

### Dados temporais

Considera estacao do ano, periodo chuvoso, horario de pico, fim de semana, feriados e madrugada.

### Historico de alagamentos

O arquivo `datasets_exemplo/alagamento_erosao_talude.csv` e usado para verificar ocorrencias proximas as coordenadas do bueiro.

### Topografia

A OpenTopography fornece altitude, declividade, identificacao de fundo de vale e classificacao de risco topografico.

### Uso do solo

A API OpenStreetMap/Overpass consulta areas comerciais, industriais e residenciais, vias, parques, lojas e mercados. Com esses dados, o sistema estima a impermeabilizacao e a intensidade comercial do entorno.

## 4. Machine Learning

O modelo ML e uma `DecisionTreeClassifier` treinada inicialmente com dados sinteticos. Ele usa:

- distancia atual;
- taxa de subida;
- media movel das tres ultimas leituras.

O modelo consegue processar leituras reais do sensor, mas seu treinamento inicial e baseado em cenarios simulados. Com o funcionamento do bueiro fisico, o historico real pode ser usado para treinar um modelo mais confiavel.

## 5. Decisao conjunta

Os dois modelos sao executados automaticamente quando uma nova leitura chega. A API compara os riscos usando a ordem:

```text
Baixo < Medio < Alto < Critico
```

O maior risco entre os dois modelos se torna a decisao operacional. Por exemplo:

```text
Multivariada: Medio
Machine Learning: Alto
Risco final: Alto
```

A resposta da API informa os resultados individuais e a decisao final:

```json
{
  "nivel_risco": "Critico",
  "nivel_risco_multivariado": "Critico",
  "nivel_risco_ml": "Critico",
  "modelo_decisao": "Multivariada + Machine Learning",
  "acionar_limpeza": true,
  "tempo_limpeza_segundos": 15
}
```

## 6. Ciclo automatico de limpeza

O tempo de acionamento do servo e proporcional ao risco final:

| Risco final | Tempo do servo |
|---|---:|
| Baixo/Normal | 0 segundos |
| Medio | 5 segundos |
| Alto | 10 segundos |
| Critico | 15 segundos |

O ESP32 recebe a resposta, abre o servo pelo tempo indicado e depois retorna a comporta para a posicao inicial.

Existe tambem uma protecao local no firmware: se a distancia for menor que `15 cm`, o servo sera acionado mesmo que a API ou a rede estejam indisponiveis.

A API aplica um intervalo de seguranca de 5 minutos entre ciclos automaticos para evitar acionamentos repetidos a cada leitura.

## 7. Funcionamento fisico

No prototipo:

- servo em `0 graus`: comporta fechada;
- servo em `90 graus`: comporta aberta;
- LED verde: operacao normal;
- LED vermelho: risco critico ou ciclo de limpeza.

O servo representa o mecanismo de limpeza. No bueiro fisico completo, ele deve estar conectado a uma comporta, raspador, esteira ou outro mecanismo capaz de deslocar os residuos.

## 8. Principais endpoints

### Registrar leitura

```text
POST /sensores/leitura
```

Salva a leitura e executa os dois modelos.

### Consultar leituras

```text
GET /sensores/leituras
```

Lista as leituras registradas.

### Previsao multivariada

```text
GET /ia/previsao
```

Executa somente a analise multivariada.

### Previsao ML

```text
GET /ia/previsao-ml
```

Executa somente o modelo de Machine Learning.

### Comparar os modelos

```text
GET /ia/comparativo
```

Executa os dois modelos e mostra a convergencia entre eles.

### Consultar fontes ativas

```text
GET /ia/fontes-dados
```

Mostra o estado das seis fontes de dados.

### Simular um cenario de chuva

```text
POST /ia/simular-cenario
```

Cria uma projecao matematica da subida da agua.

## 9. Execucao no Wokwi

O Wokwi precisa acessar a API por uma URL publica, como Ngrok ou LocalTunnel. O endereco `localhost` nao funciona diretamente dentro do simulador.

O fluxo da simulacao e:

```text
HC-SR04 virtual
        |
        v
ESP32 virtual
        |
        v
URL publica da API
        |
        v
FastAPI
        |
        v
Previsoes e decisao
        |
        v
Resposta JSON
        |
        v
Servo e LEDs virtuais
```

Para a demonstracao funcionar, a API, o banco MySQL e o tunel publico precisam estar ativos. A URL configurada no sketch deve corresponder ao tunel atualmente aberto.

## Resumo

O bueiro recebe dados do sensor, combina informacoes fisicas e externas, calcula o risco com a IA multivariada e o Machine Learning, escolhe o maior risco entre os dois e define a duracao da limpeza. O ESP32 executa o ciclo proporcional por meio do servo, enquanto os LEDs indicam o estado operacional.
