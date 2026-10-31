# Relatorio detalhado da refatoracao da API

**Projeto:** Bueiro Inteligente  
**Escopo:** `bueiro_inteligente_api/`  
**Data de consolidacao:** 15/10/2026

Este documento registra o trabalho realizado nas Etapas 0 a 5 da refatoracao. O objetivo foi organizar a API FastAPI, facilitar testes e manutencao e preservar os contratos consumidos pelo firmware ESP32 e pelo dashboard.

## Objetivos e limites preservados

- Manter os caminhos e metodos HTTP existentes.
- Preservar os nomes dos campos JSON e os formatos das respostas.
- Nao alterar os codigos de status publicados durante a refatoracao.
- Preservar os cinco testes de integracao existentes; eles nao foram removidos nem enfraquecidos.
- Nao adicionar dependencias ao projeto.
- Manter o fluxo operacional de risco conjunto: usar o maior risco entre a IA multivariada e o classificador ML, mapear risco para tempo de limpeza e respeitar a janela de cinco minutos.

## Etapa 0 — Diagnostico

**Resultado:** levantamento sem alteracoes de codigo.

### Processos realizados

1. **Mapeamento dos modulos**
   - `app/main.py` cria a aplicacao, registra handlers e inclui routers.
   - `app/config.py`, `app/database.py`, `app/models.py` e `app/schemas.py` reúnem configuracao, sessao SQLAlchemy, modelos ORM e DTOs.
   - `app/ai_predictor.py`, `app/ml/` e os servicos de dados externos sustentam a predicao multivariada, o classificador ML, o clima, a topografia e as fontes auxiliares.
   - `app/routers/` publica as rotas; `app/services/` concentra casos de uso e `app/repositories/` encapsula persistencia SQL/arquivos.
   - `tests/` contem testes unitarios e os testes de integracao dependentes da API e do MySQL.

2. **Identificacao dos pontos de manutencao**
   - Havia orquestracao de predicao e acesso a dados diretamente nos routers de sensores e IA.
   - O router de bueiros acumulava leitura/agregacao do inventario e das solicitacoes SAC.
   - Havia constantes de risco, tempos e configuracao ML distribuidas entre modulos.
   - Foram identificadas funcoes extensas nos motores de predicao e nos providers de dados externos, alem de logica de negocio que poderia ser testada sem HTTP.
   - O diagnostico apontou risco de regressao nos campos da resposta de leitura e no comando de limpeza enviado ao firmware.

3. **Levantamento de testes**
   - O comando de pytest solicitado inicialmente nao pode ser executado no ambiente naquele momento porque pytest ainda nao estava instalado.
   - Uma alternativa com `unittest` confirmou os 19 testes unitarios existentes.
   - A tentativa de descoberta ampla tambem alcançou testes de integracao, que falharam porque API/MySQL nao estavam ativos. Esses testes foram preservados.

## Etapa 1 — Configuracao e constantes

**Commit:** `5a0a9ef` — `Centralize API risk and ML configuration`

### Processos realizados

1. **Unificacao dos niveis de risco**
   - Criado `NivelRisco` em `app/enums.py`.
   - Os valores textuais mantidos nas respostas sao `Baixo`, `Médio`, `Alto` e `Crítico`.
   - Os modulos de predicao, simulacao e rotas passaram a reutilizar a mesma definicao onde aplicavel.

2. **Centralizacao das regras operacionais**
   - Limiar critico vigente centralizado em 15 cm.
   - Janela de supressao entre limpezas centralizada em cinco minutos.
   - Prioridade dos riscos e duracao operacional centralizadas: Baixo 0 s, Medio 5 s, Alto 10 s e Critico 15 s.

3. **Centralizacao dos parametros ML**
   - Seed `42`, divisao de teste `0.2` (80/20), profundidade maxima `5` e tamanho padrao do dataset sintetico `3000` reunidos em configuracao.
   - O conjunto usa divisao estratificada, preservando a reproducibilidade ja esperada.

4. **Preservacao das dimensoes multivariadas**
   - Os pesos configurados para sensor, clima, temporal, historico de alagamento, geografia e uso do solo foram mantidos em 0.30, 0.25, 0.10, 0.15, 0.10 e 0.10, respectivamente (soma 1.0).
   - O TTL climatico configuravel existente foi mantido.

5. **Registro da divergencia de limiar**
   - Foi mantido o valor que o codigo ja utilizava, 15 cm, sem adotar por conta propria valores diferentes citados no TCC1.
   - A documentacao registra a diferenca de fronteira: backend considera critico `<= 15 cm`; firmware considera `< 15 cm`.

### Validacao registrada

- 19 testes unitarios passaram.
- Treino sintetico manual manteve acuracia de `0.965`.

## Etapa 2 — Camada de servicos e repositorios

**Commits:**
- `f1996af` — `Extract sensor reading orchestration service`
- `b6a9d1a` — `Move remaining route logic into services`

### Processo 2.1 — Orquestracao de leitura do sensor

- Criado `app/services/leituras.py` para coordenar gravacao da leitura, execucao dos motores, combinacao dos riscos, decisao de acionamento e montagem da resposta.
- A regra de combinacao escolhe o risco de maior prioridade entre multivariado e ML.
- A decisao de acionamento mapeia risco para duracao e zera o acionamento quando houve limpeza recente.
- O router `POST /sensores/leitura` passou a delegar o caso de uso ao servico.
- A rota de listagem de leituras tambem delega a composicao dos dados ao servico.

### Processo 2.2 — Acesso a dados de leituras e previsoes

- Criados `LeituraRepository` e `PrevisaoRepository`.
- Consultas SQL, gravacao de leitura/limpeza e associacao de previsoes foram retiradas dos routers e colocadas nos repositorios.
- Operacoes de escrita fazem `commit`; em excecao, executam `rollback` e propagam a falha.
- Os motores de predicao passaram a reutilizar o repositorio de previsoes para suas consultas e gravacoes.

### Processo 2.3 — Simulacao, comparacao e fontes de IA

- Criado `app/services/ia.py` para simulacao de cenario, comparacao dos motores, exposicao da topografia e resumo das fontes disponiveis.
- O router `app/routers/ia.py` passou a encaminhar essas operacoes ao servico.
- A rota de historico de previsoes consulta o repositorio em vez de fazer a consulta diretamente no router.

### Processo 2.4 — Inventario de bueiros e dados SAC

- Criado `InventarioBueirosRepository` para leitura, parsing e cache dos arquivos CSV.
- Criado `CatalogoBueirosService` para combinar inventario, cadastros locais, filtros e agregacoes dos chamados SAC.
- O router de bueiros passou a delegar essas operacoes aos servicos/repositorios.
- O fluxo de cadastro e persistencia JSON continuou usando seu servico e repositorio dedicados.

### Processo 2.5 — Salvaguarda do acionamento e falhas dos motores

- O servico verifica a janela de limpeza antes de executar os motores para evitar que uma limpeza registrada durante a analise altere retroativamente a decisao destinada ao ESP32.
- Se o preditor multivariado registrar a limpeza correspondente, o servico evita gravar duplicadamente o mesmo evento, sem suprimir o comando de limpeza da resposta.
- Falhas dos preditores sao registradas em log, provocam rollback do trabalho ainda pendente e sao propagadas, em vez de serem convertidas em resposta de sucesso com risco padrao. Esse comportamento diz respeito ao caminho de erro; os contratos de sucesso permanecem inalterados.

### Validacao registrada

- 26 testes passaram, junto com 4 subtests.
- O OpenAPI foi conferido: 20 caminhos e os metodos/status verificados foram preservados.
- Os testes de integracao nao foram executados por falta de API/MySQL ativos.

## Etapa 3 — Modulo de IA e provedores externos

**Commit:** `cc1edae` — `Separate lazy ML storage and external clients`

### Processo 3.1 — Separacao de features, treino e armazenamento do modelo

- As colunas usadas pelo classificador foram reunidas em `app/ml/features.py`.
- Criado `app/ml/model_storage.py` com operacoes especificas para salvar e carregar o artefato joblib.
- O salvamento cria o diretorio pai necessario; a tentativa de carregar um artefato ausente informa explicitamente `FileNotFoundError`.
- `app/ml/train.py` passou a usar a camada de armazenamento em vez de gravar o arquivo diretamente.

### Processo 3.2 — Carregamento preguiçoso

- O predictor carrega o artefato somente quando ocorre a primeira predicao, com protecao por `Lock`.
- Se o arquivo ainda nao existir, o treino e iniciado sob demanda e o modelo e carregado em seguida.
- A importacao dos modulos da API nao inicia treinamento.
- O caminho e configuravel por `ML_MODEL_PATH`; o padrao continua em `app/ml/modelo_risco.joblib`.

### Processo 3.3 — Interface HTTP para provedores

- Criado `app/external_http.py` como interface comum para requisicoes GET/POST JSON, verificacao de status HTTP e timeouts explicitos.
- OpenWeatherMap, OpenTopography e Overpass passaram a usar a interface comum.
- Timeouts configurados: OpenWeatherMap 8 s, OpenTopography 10 s e Overpass 20 s; a consulta Overpass informa ao servidor limite de 15 s.
- Nenhuma dependencia nova foi adicionada.

### Processo 3.4 — Fallbacks e caches preservados

- OpenWeatherMap continua usando cache em memoria por coordenadas (TTL padrao de 60 s) e resposta fallback com `disponivel=False` quando nao ha chave ou a consulta falha.
- OpenTopography continua usando cache persistente em `topografia_cache.json` e perfil conservador/indisponivel em falhas.
- Overpass continua usando cache em memoria por coordenadas e raio (TTL de 600 s); quando nao ha dados, usa o perfil local de uso do solo.
- Os fallbacks e limites foram documentados em `docs/funcionamento_bueiro_api.md`.

### Validacao registrada

- 30 testes passaram, junto com 4 subtests.
- Testes novos cobriram armazenamento/carregamento do modelo, ausencia de artefato e cliente HTTP.
- Acuracia do treino sintetico foi `0.965`, com 2.400 amostras de treino e 600 de teste.
- Foi verificado em execucao que importar o predictor nao carrega nem treina o modelo.

## Etapa 4 — Qualidade

**Commit:** `6c633b1` — `Improve API typing and quality conventions`

### Processo 4.1 — Tipagem

- Foram completados os tipos de parametros e retornos de funcoes e metodos no pacote `app/`, sem alterar nomes, ordem, defaults ou forma dos parametros.
- A verificacao AST final encontrou zero assinaturas de funcoes sem anotacao.
- Alguns payloads de dados externos permanecem com estruturas amplas quando o formato depende de CSV/JSON dinamico; nao foram inventados tipos restritivos para esses dados.

### Processo 4.2 — Schemas

- Os schemas de saida mantem heranca dos schemas de entrada, sem duplicacao de campos.
- A configuracao ORM dos modelos de saida foi atualizada para `ConfigDict(from_attributes=True)`.
- O formato de serializacao e os campos publicados foram verificados por testes e geracao do OpenAPI.

### Processo 4.3 — Imports e logging

- Removidos imports identificados como nao utilizados pelo Pylance.
- O comando de treino deixou de usar `print` e passou a registrar metricas por logging.
- Falhas externas continuam sendo registradas pelos servicos; os fallbacks nao ocultam o estado de indisponibilidade indicado ao consumidor.

### Processo 4.4 — Erros e documentacao

- Os handlers globais existentes em `app/errors.py` foram mantidos como ponto comum de tratamento; nao foram criados handlers equivalentes por router.
- Foram adicionadas docstrings curtas em portugues nos pontos publicos alterados nesta etapa, mantendo docstrings preexistentes.
- `docs/refatoracao_api_backend.md` foi atualizada com as convencoes e validacoes atuais.

### Validacao registrada

- 30 testes passaram, junto com 4 subtests.
- O OpenAPI continuou apresentando 20 caminhos, os metodos existentes e os status previamente configurados.
- O Pylance nao apontou novos erros de tipo. Permaneceram avisos preexistentes de depreciacao do `datetime.utcnow`, parametros de coordenadas preservados por compatibilidade na rota ML, variavel de ciclo de vida do FastAPI e mocks de testes.

## Etapa 5 — Testes

**Commit:** `7ce4d53` — `Expand sensor risk decision tests`

### Processo 5.1 — Combinacao de riscos

- O teste de combinacao passou a cobrir os 16 pares ordenados dos quatro niveis de risco (4 × 4).
- Cada resultado e comparado com a prioridade definida para confirmar que o risco final e o maior dos dois motores.

### Processo 5.2 — Acionamento e duracao

- O mapeamento Baixo 0 s, Medio 5 s, Alto 10 s e Critico 15 s e exercitado para todos os niveis.
- Foi acrescentada verificacao de que uma limpeza recente suprime o acionamento e retorna duracao zero para todos os riscos.
- Os testes existentes continuam verificando que o comando ao firmware nao e suprimido quando o motor multivariado ja registra a limpeza durante a mesma analise.

### Processo 5.3 — Fronteira temporal real no repositorio

- Um teste com SQLite em memoria cria registros reais de limpeza e exercita `LeituraRepository.existe_limpeza_recente`.
- Confirma que um registro exatamente cinco minutos antes esta dentro da janela; apos removê-lo, um registro cinco minutos e um segundo antes fica fora.
- O teste verifica a implementacao SQLAlchemy, nao apenas um mock da regra.

### Processo 5.4 — Falhas transacionais

- Os testes anteriores de rollback em falha de gravacao e de propagacao de falha do preditor foram mantidos.
- Os testes de simulacao e as demais coberturas das etapas anteriores tambem continuam na suite.

### Validacao registrada

- Teste focado: 8 testes passaram e 24 subtests passaram.
- Suite unitária completa, excluindo somente `tests/test_integracao_api.py`: 32 testes passaram e 24 subtests passaram.
- Os testes de integracao foram preservados, mas nao executados por dependerem de API e MySQL ativos.

## Commits por etapa

| Etapa | Commit(s) |
|---|---|
| 1 — Configuracao e constantes | `5a0a9ef` |
| 2 — Servicos e repositorios | `f1996af`, `b6a9d1a` |
| 3 — IA e provedores externos | `cc1edae` |
| 4 — Qualidade | `6c633b1` |
| 5 — Testes | `7ce4d53` |

## Divergencias e validacoes pendentes

- **Limiar de nivel:** foi mantido o limiar atual de 15 cm. O TCC1 cita 10 cm como critico e 20 cm como alerta; firmware/backend tambem diferem na inclusao exata da fronteira de 15 cm (`<` no firmware, `<=` no backend). A decisao sobre harmonizar esses valores permanece pendente e nao foi aplicada.
- **Periodo de amostragem:** o TCC1 menciona amostragem a cada 2 s, enquanto o firmware observado opera em ciclo aproximado de 5 s. Nenhuma alteracao foi feita nessa configuracao.
- **Integracao:** os cinco testes de `tests/test_integracao_api.py` permanecem no repositorio. Eles precisam ser executados em ambiente com API e MySQL ativos.
- **Comportamento em falha dos preditores:** o caminho de sucesso e o contrato da resposta permanecem preservados; em falha, o erro agora e logado e propagado com rollback, em vez de se transformar em resposta de sucesso com risco fallback.

## Estado final

As cinco etapas foram concluidas e registradas em commits separados por etapa (a Etapa 2 possui dois commits). O worktree ao finalizar mantinha a pasta nao rastreada preexistente `tc2_68_02_2026_1/`; ela nao pertenceu a esta refatoracao e foi preservada.
