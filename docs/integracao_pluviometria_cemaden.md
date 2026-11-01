# Integracao dos dados pluviometricos do CEMADEN

## Objetivo

O sistema utiliza os arquivos historicos do CEMADEN armazenados em
`bueiro_inteligente_api/datasets/dados_pluviometricos` para complementar a
analise climatica do Bueiro Inteligente. A integracao consulta a chuva observada
em uma estacao proxima ao bueiro e disponibiliza os totais historicos diarios.

Os dados do CEMADEN nao substituem a OpenWeatherMap: o CEMADEN fornece chuva
observada, enquanto a OpenWeatherMap continua sendo utilizada para condicoes
atuais, previsao, umidade e vento.

## O que foi adicionado

- Um servico para ler os CSVs mensais do CEMADEN, identificar a estacao mais
  proxima e gerar um indice local SQLite compacto.
- Uso da chuva observada pelo score climatico da IA, sem adicionar uma segunda
  dimensao ou alterar o peso total da dimensao climatica.
- O acumulado de chuva da ultima hora e os metadados da estacao na resposta da
  analise da IA.
- Os endpoints `GET /ia/pluviometria-cemaden` e
  `GET /ia/pluviometria-cemaden/historico`.
- Testes automatizados para indexacao, atualidade dos dados, consulta historica
  e integracao da chuva ao score.

## Como funciona

### 1. Criacao do indice

Na pasta `bueiro_inteligente_api`, execute:

```powershell
python -m app.cemaden_service --build-index
```

O processo percorre os arquivos CSV, escolhe a estacao mais proxima das
coordenadas do bueiro e armazena somente as leituras dessa estacao em SQLite.
Isso evita ler dezenas de megabytes de CSV a cada analise da API. O indice e
criado fora do repositorio, por padrao em:

```text
%TEMP%\bueiro-inteligente\cemaden.sqlite3
```

Para indexar em outra localizacao, informe as coordenadas:

```powershell
python -m app.cemaden_service --build-index --latitude -23.5505 --longitude -46.6333
```

Para selecionar uma estacao especifica:

```powershell
python -m app.cemaden_service --build-index --station 355030833A
```

### 2. Uso na analise de risco

Durante uma analise, o sistema consulta a estacao indexada e soma os valores de
precipitacao registrados na ultima hora. A medicao do CEMADEN substitui a chuva
atual da OpenWeatherMap no subscore de chuva quando:

- a ultima leitura da estacao tem no maximo 90 minutos;
- a estacao esta a no maximo 25 km das coordenadas analisadas.

Quando a observacao do CEMADEN nao esta atualizada ou disponivel, ela nao e
tratada como chuva atual. A OpenWeatherMap continua sendo usada conforme sua
disponibilidade. Um indice desatualizado tambem e detectado: se algum CSV for
adicionado ou modificado, o endpoint informa que a indexacao precisa ser refeita.

A resposta da analise multivariada inclui os metadados CEMADEN dentro de
`dados_climaticos_utilizados.cemaden`. Quando a observacao e elegivel, a lista de
fontes utilizadas inclui `CEMADEN (Pluviometria observada)`.

### 3. Consulta dos endpoints

Disponibilidade e observacao recente:

```text
GET /ia/pluviometria-cemaden
GET /ia/pluviometria-cemaden?lat=-23.5505&lon=-46.6333
```

O resultado informa se a observacao pode ser usada, codigo e nome da estacao,
distancia, horario da ultima leitura, idade da leitura e acumulado da ultima
hora. Se a leitura estiver antiga, a resposta explica o motivo e nao apresenta
um acumulado utilizavel como chuva atual.

Historico diario:

```text
GET /ia/pluviometria-cemaden/historico?data_inicio=2023-01-01&data_fim=2023-12-31
```

Tambem aceita `lat` e `lon`. O retorno agrega as leituras por dia e inclui a
quantidade de registros em cada dia. Dias sem registros nao aparecem na lista e
nao devem ser interpretados automaticamente como dias sem chuva.

## Configuracao

As variaveis de ambiente sao opcionais:

| Variavel | Finalidade | Padrao |
|---|---|---|
| `CEMADEN_DATASET_PATH` | Diretorio raiz dos CSVs | `bueiro_inteligente_api/datasets/dados_pluviometricos` |
| `CEMADEN_INDEX_PATH` | Caminho do indice SQLite | `%TEMP%/bueiro-inteligente/cemaden.sqlite3` |
| `CEMADEN_ESTACAO` | Codigo fixo da estacao para indexacao | Estacao mais proxima |
| `CEMADEN_RAIO_MAXIMO_KM` | Distancia maxima para aceitar a estacao | `25` |
| `CEMADEN_IDADE_MAXIMA_MINUTOS` | Idade maxima para considerar observacao atual | `90` |

O indice nao e versionado no Git. A base original de CSVs permanece no diretorio
de datasets.

## Atualizacao dos dados

Depois de adicionar novos meses, anos ou corrigir arquivos:

1. Execute novamente `python -m app.cemaden_service --build-index`.
2. Confirme o codigo da estacao, quantidade de arquivos e leituras no resumo
   impresso pelo comando.
3. Consulte `GET /ia/pluviometria-cemaden` para verificar se a ultima observacao
   esta dentro da janela de atualidade.

O indice e reconstruido a partir dos CSVs; novos arquivos nao sao incorporados
automaticamente enquanto o comando de indexacao nao for executado.

## Limites e cuidados com os dados

- A integracao assume que `valorMedida` representa milimetros de precipitacao.
  Essa unidade e o intervalo de acumulacao devem ser confirmados na
  documentacao da exportacao utilizada.
- O acumulado da ultima hora e a soma dos registros disponiveis nessa janela.
  Como os intervalos podem ser irregulares ou ter lacunas, o total nao garante
  cobertura completa da hora.
- Uma estacao proxima e uma aproximacao da chuva no bueiro; a precipitacao pode
  variar localmente.
- O historico e disponibilizado para analise, mas ainda nao e usado para treinar
  o modelo de Machine Learning. O treinamento inicial continua baseado em dados
  sinteticos.
