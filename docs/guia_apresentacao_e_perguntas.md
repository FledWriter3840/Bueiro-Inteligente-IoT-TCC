# Guia de apresentação — Bueiro Inteligente IoT TCC

## 1. Objetivo da apresentação

O projeto mostra como um sistema de monitoramento e limpeza preventiva de bueiros pode combinar sensores, Internet das Coisas, dados externos, Machine Learning e um painel web.

A mensagem central para estudantes do ensino médio é:

> Um projeto de faculdade não é só escrever código. Ele envolve problema, requisitos, desenho, banco de dados, testes, implementação, simulação, análise e validação.

## 2. Resumo do projeto

O sistema possui quatro níveis principais:

1. **Sensoramento:** HC-SR04 mede a distância do nível de resíduos, e o ESP32 coleta a leitura.
2. **Comunicação:** o ESP32 envia a leitura para a API por HTTP.
3. **Integração e decisão:** a API persiste no MySQL, executa IA multivariada e Machine Learning, e escolhe o risco final.
4. **Ação e visualização:** o firmware pode acionar um servo e LEDs; o painel mostra leituras, riscos, gráficos, mapas e dados geográficos.

O sistema não só “detecta água”; ele tenta prever quando o bueiro vai entupir, avaliar o risco e recomendar uma limpeza preventiva.

## 3. Arquitetura do fluxo

```text
HC-SR04 / sensor virtual
             |
             v
ESP32 + Wokwi
             |
             | HTTP POST /sensores/leitura
             v
API FastAPI
  |-- MySQL: leituras, alertas, limpezas
  |-- IA multivariada: sensor, clima, tempo, alagamento, topografia, uso do solo
  |-- ML: DecisionTreeClassifier com(features: distância, taxa de subida e média)
  |--Resposta JSON ao ESP32
             |
             v
Servo/LED no Wokwi e painel web
```

## 4. Componentes e responsabilidades

### ESP32 e sensor ultrassônico

- Mede a distância com o HC-SR04.
- Envia o valor em centímetros.
- A cada 5 segundos, realiza uma nova leitura no protótipo.
- Interpreta a resposta da API.
- Ação do servo: 5, 10 ou 15 segundos conforme o risco.
- O servo permanece em 90 graus durante o ciclo e volta para 0 graus.
- O LED vermelho indica risco crítico ou ciclo de limpeza.

### API FastAPI

- Expõe endpoints REST.
- Valida o payload recebido.
- Persiste a leitura no banco.
-Executa as duas famílias de IA.
- Escolhe o maior risco.
- Implementa a proteção de cinco minutos entre ciclos automáticos.

### Banco de dados

- MySQL armazena leituras de sensor.
- Armazena alertas e registros de limpeza.
- O histórico de leituras é usado para calcular tendência e para o modelo ML.
- O banco fornece os dados do sensor e da compactação para a IA multivariada.

### IA multivariada

A IA pondera seis dimensões:

| Dimensão | Peso |
|---|---:|
| Sensor IoT | 30% |
| Clima | 25% |
| Dados temporais | 10% |
| Histórico de alagamentos | 15% |
| Topografia | 10% |
| Uso do solo | 10% |

O resultado é classificado em:

- Baixo
- Médio
- Alto
- Crítico

A categoria é definida a partir da probabilidade ponderada e da distância atual.

### Machine Learning

O modelo usa:

- distância atual;
- taxa de subida;
- média móvel das três leituras mais recentes.

O modelo disponível está treinado sobre um dataset sintético. Ele não é um modelo treinado com dados reais do bueiro físico. Por isso, o desempenho depende do representatividade do dataset e deve ser melhorado com dados reais.

### Decisão conjunta

A API compara os dois resultados e usa o risco mais alto:

```text
Baixo < Médio < Alto < Crítico
```

Exemplo:

```text
Multivariada: Médio
ML: Alto
Risco final: Alto
```

## 5. Endpoint principal

### POST /sensores/leitura

Payload:

```json
{
  "id_sensor": 1,
  "valor_leitura": 60.0,
  "unidade_medida": "cm"
}
```

Resposta relevante:

```json
{
  "id_sensor": 1,
  "valor_leitura": 60.0,
  "id_leitura": 63,
  "acionar_limpeza": false,
  "tempo_limpeza_segundos": 0,
  "nivel_risco": "Médio",
  "nivel_risco_multivariado": "Médio",
  "nivel_risco_ml": "Baixo",
  "modelo_decisao": "Multivariada + Machine Learning"
}
```

O firmware usa:

- `acionar_limpeza` para decidir se executa o servo;
- `tempo_limpeza_segundos` para definir a duração;
- `nivel_risco` para exibir o estado final.

### GET /sensores/leituras

Lista as leituras registradas no banco, ordenadas da mais recente para a mais antiga.

### GET /ia/fontes-dados

Informa as seis fontes e o estado de cada uma.

### GET /ia/previsao

Executa somente a análise multivariada.

### GET /ia/previsao-ml

Executa somente o modelo de Machine Learning.

### GET /ia/comparativo

Compara os resultados das duas famílias de IA.

### POST /ia/simular-cenario

Executa uma projeção matemática para simular o crescimento do nível de água.

## 6. Regras de classificação e ação

| Risco final | Ação da API | Tempo do servo |
|---|---|---:|
| Baixo | Sem ciclo de limpeza | 0 s |
| Médio | Ciclo curto | 5 s |
| Alto | Ciclo médio | 10 s |
| Crítico | Ciclo longo | 15 s |

O fabricante do protótipo usa o servo como substituto do mecanismo real de limpeza. No protótipo físico, o mecanismo deve ser um compactador, raspador, esteira ou outro sistema capaz de remover os resíduos.

O firmware também contém uma proteção local:

- Se a distância for menor que 15 cm, o servo é aberto mesmo sem resposta da API.
- O valor de 15 cm é uma condição de emergência do protótipo e não substitui a análise da API.

## 7. Segurança e limitações

1. **Intervalo de segurança:** a API impede novos ciclos de limpeza durante cinco minutos.
2. **Dados sintéticos:** o ML usa um dataset sintético; isso não garante que o modelo funcione bem em uma cidade real.
3. **Câmera:** a câmera é uma próxima etapa e ainda não está implementada no fluxo completo.
4. **Compactação:** o código considera o nível de resíduos e possui estrutura para compactação, mas o mecanismo physical ainda precisa ser ligado ao protótipo.
5. **URL pública:** o Wokwi não pode acessar localhost. A URL do sketch precisa apontar para o LocalTunnel.
6. **HTTPS:** o sketch atual usa uma URL pública do LocalTunnel e desativa a validação do certificado no ESP32. Para uma versão de produção, é recomendado validar o certificado e usar uma configuração segura.
7. **Credenciais:** chaves e senhas devem permanecer fora de apresentações públicas e devem ser configuradas no ambiente local.

## 8. Como executar para a apresentação

### Requisitos

- Python 3.13 ou versão compatível com as dependências.
- Node.js 20.19+ ou 22.12+.
- MySQL ativo.
- API FastAPI em execução.
- Túnel público com a porta 8000 disponible.
- O sketch do Wokwi apontando para a URL pública atual.

### Iniciar API

```powershell
cd .\bueiro_inteligente_api
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Iniciar painel

```powershell
cd .\bueiro_inteligente_api\frontend
npm install
npm run dev
```

### Executar testes da API

```powershell
cd .\bueiro_inteligente_api
python -m unittest tests.test_integracao_api -v
```

### Executar testes do frontend

```powershell
cd .\bueiro_inteligente_api\frontend
npm run lint
npm run build
```

## 9. Configuração do Wokwi

1. Abra o arquivo da simulação.
2. Certifique-se de que o sketch usa o endereço HTTPS público da API.
3. Use o endereço que aponta para `/sensores/leitura`.
4. Inicie a simulação.
5. Abra o Serial Monitor.
6. Observe o HTTP status, o payload e a resposta da IA.
7. Altere a distância do sensor virtual.
8. Observe o nível de risco e o comportamento do servo.

O Wokwi não acessa `localhost`; ele precisa da URL pública.

## 10. Roteiro de apresentação

### Slide 1 — problema

- Bueiros preenchidos cause alagamentos.
- A detecção tardia transforma uma situação simples em grande problema.
- O projeto busca agir antes da enchente.

### Slide 2 — processo do projeto

- Requisitos e casos de uso.
- Diagramas e arquitetura.
- Simulação e código.
- Protótipo físico.

### Slide 3 — áreas de computação

- Python: API.
- C++: ESP32.
- TypeScript: painel.
- SQL: banco.
- IA: modelos.
- Redes: HTTP e serviços externos.

### Slide 4 — princípio do sensor

- Som chega ao objeto.
- Eco retorna.
- Distância calculada.
- Menor distância: maior nível de preenchimento.

### Slide 5 — fluxo de dados

- ESP32 coleta a leitura.
- API salva e analisa.
- IA determina risco.
-Resposta define ação.
- Painel mostra resultado.

### Slide 6 — dois motores de IA

- Motor multivariado: seis fontes e pesos.
- Machine Learning: árvore de decisão.
- A resposta considera o maior risco.
- O modelo do ML usa dados sintéticos.

### Slide 7 — ação

- Baixo: 0 segundos.
- Médio: 5 segundos.
- Alto: 10 segundos.
- Crítico: 15 segundos.
- O servo é representado no Wokwi.

### Slide 8 — demonstração ao vivo

1. Alterar a distância.
2. Observar a leitura no painel.
3. Observar o nível de risco.
4. Observar o servo no Wokwi.
5. Confirmar o HTTP 200 e a resposta JSON.

## 11. Perguntas frequentes

### O que é Machine Learning?

É uma área de IA que aprende padrões a partir de exemplos. No projeto, o modelo usa características numéricas de leituras e prevê uma classe de risco.

### Por que o ML e a IA multivariada são diferentes?

A IA multivariada agrega diversas fontes externas e internas com pesos. O ML aprende uma relação entre características e uma classe. A solução usa os dois para comparar opiniões e evitar depender de apenas um modelo.

### Por que o risco final usa o maior risco?

O método evita que um modelo mais conservador esconda uma situação crítica. Em caso de conflito, o sistema segue o risco mais elevado.

### O que é o Wokwi?

É uma plataforma de simulação de eletrônica e IoT. No projeto, ele está representando um ESP32, sensor ultrassônico, servo e LEDs, mantendo a mesma comunicação HTTP com a API.

### O Wokwi precisa da API pública?

Sim. O dispositivo virtual não é executado no mesmo processo do computador e não consegue usar localhost para acessar a API local.

### O que acontece no MySQL?

O banco recebe leituras, alertas, limpezas e registros de previsão. As leituras servem como histórico e como entrada para os modelos.

### Por que o servo é simulado?

O projeto atual é um protótipo. O servo está representado no Wokwi para demonstrar o fluxo, mas o mecanismo real precisa ser instalado no bueiro físico.

### Por que a câmera ainda não está implementada?

A câmera seria uma fonte adicional para confirmar o tipo de resíduo e o nível de preenchimento. O projeto atual ainda tem o sensor e o servo como base.

### O que significa “API funciona perfeitamente”? 

O fluxo HTTP, a resposta JSON, os modelos e o painel já foram implementados. A validação final depende de banco, URL pública, configuração do Wokwi, dados externos e uma execução real. O teste local confirmou o endpoint e o fluxo, mas não substitui a validação final do dispositivo virtual.

### O que acontece quando leio 8 cm?

O resultado real da execução mostrou que o motor multivariado retornou `Crítico`, enquanto o ML retornou `Baixo`. A resposta final foi `Crítico`, e o sistema destacou o risco maximo. O teste do projeto que espera `Crítico` no ML está desatualizado ou depende de um cenário diferente, pois o modelo está treinado com dataset sintético.

### Por que o ciclo não acionou em uma leitura crítica?

O sistema registra quando ocorreu a última limpeza e impede uma nova execução por cinco minutos. O valor do ciclo deve ser avaliado depois de aguardar o intervalo ou usando um banco de testes limpo.

### Como explicar o projeto para jovens do ensino médio?

Use uma analogia:

- Sensor = olhos;
- ESP32 = cérebro de pequena escala;
- API = mensageiro;
- banco = arquivo de histórico;
- IA = analista de risco;
- servo = braço;
- painel = tela de monitoramento.

## 12. Validação atual do ambiente

Os testes executados confirmaram:

- API disponível em http://localhost:8000 após o servidor iniciar.
- Cinco testes de integração executados.
- Quatro testes passaram.
- Um teste falhou porque o ML retornou `Baixo` para a leitura de 8 cm, enquanto o teste esperava `Crítico`.
- As seis fontes de dados foram retornadas como ativas.
- Leituras de 8, 15, 60 e 200 cm retornaram HTTP 200.
- O endpoint respondeu com `nivel_risco`, `nivel_risco_multivariado`, `nivel_risco_ml`, `acionar_limpeza` e `tempo_limpeza_segundos`.
- A porta 8000 estava fechada antes do início do servidor.

> A falha do teste não é uma falha do HTTP. É uma divergência entre a expectativa do teste e o comportamento do modelo sintético.

## 13. Checklist para a próxima validação ao vivo

- [ ] MySQL ativo e o banco correto.
- [ ] API iniciada na porta 8000.
- [ ] Túnel público ativo e URL atualizada no sketch.
- [ ] Endpoint `/sensores/leitura` respondendo com HTTP 200.
- [ ] Wokwi conectado ao Wi-Fi virtual.
- [ ] Serial Monitor mostrando a requisição e a resposta.
- [ ] Painel aberto com API local ou proxy.
- [ ] Leitura alterada e o risco observado.
- [ ] Servo e LEDs alterados no Wokwi.
- [ ] Última limpeza verificada para respeitar o intervalo de cinco minutos.
- [ ] Testes do frontend e backend executados antes da apresentação.
