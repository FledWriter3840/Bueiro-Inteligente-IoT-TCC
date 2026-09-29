# Teste da simulacao Wokwi com a API

## Pre-requisitos

1. Inicie o MySQL.
2. Inicie a API na pasta `bueiro_inteligente_api`:

```powershell
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

3. Abra um tunel publico para a porta 8000, por exemplo:

```powershell
ngrok http 8000
```

4. Copie a URL HTTPS gerada pelo tunel para `apiUrl` no sketch do Wokwi.

## Teste da API antes do Wokwi

Na raiz do projeto, execute:

```powershell
python -m unittest bueiro_inteligente_api.tests.test_integracao_api -v
```

Ou, dentro de `bueiro_inteligente_api`:

```powershell
python -m unittest tests.test_integracao_api -v
```

O teste verifica:

- API acessivel;
- seis fontes de dados;
- execucao da IA multivariada;
- execucao do Machine Learning;
- decisao conjunta;
- duracao do ciclo de limpeza;
- compatibilidade da resposta com o firmware.

## Teste no Wokwi

1. Abra `simulacao/diagram.json` no Wokwi.
2. Use o sketch com a URL publica atualizada.
3. Inicie a simulacao.
4. Abra o Serial Monitor.
5. Confirme mensagens semelhantes a:

```text
>> Enviando dados para a API...
>> Codigo HTTP: 200
>> Resposta API: ...
[IA] Iniciando ciclo proporcional de 5 segundos.
```

6. Altere a distancia do HC-SR04 no simulador e observe:

| Distancia | Comportamento esperado |
|---:|---|
| acima de 150 cm | risco baixo ou normal, sem limpeza |
| entre 51 e 150 cm | possibilidade de limpeza media, conforme os dois modelos |
| entre 16 e 50 cm | limpeza maior, conforme o risco final |
| ate 15 cm | emergencia, servo em 90 graus e LED vermelho |

O sistema aplica um intervalo de seguranca de 5 minutos entre ciclos automaticos. Por isso, para repetir um teste de limpeza, aguarde o intervalo ou use um banco de testes limpo.

## Validacao no dashboard

Enquanto o Wokwi estiver enviando dados:

1. Na pasta `bueiro_inteligente_api/frontend`, execute `npm run dev`.
2. Abra `http://localhost:5173` e entre em `IA e previsão`.
3. Consulte as leituras recebidas.
4. Use `Rodar comparativo` para visualizar os dois modelos.
5. Confira os campos `nivel_risco_multivariado`, `nivel_risco_ml`, `nivel_risco` e `tempo_limpeza_segundos` na resposta da API.

O Wokwi nao acessa `localhost` diretamente. A URL do sketch deve apontar para o tunel publico ativo.
