# Refatoracao do Backend da API

## Objetivo

Este documento resume as melhorias aplicadas à API FastAPI para separar responsabilidades, tornar as respostas de erro previsiveis, validar melhor as entradas e remover credenciais padrao do codigo.

## Organizacao em camadas

As rotas HTTP deixam de executar diretamente a persistencia em alguns fluxos e delegam o trabalho a servicos e repositorios:

```text
app/
  routers/          Endpoints HTTP, parametros e codigos de resposta
  services/         Casos de uso e orquestracao da aplicacao
  repositories/     Leitura e gravacao de dados
  schemas.py        DTOs de entrada e saida
  dependencies.py   Construcao e injecao das dependencias
  errors.py         Tratamento global das excecoes HTTP
```

O cadastro de bueiros usa `BueiroService` e `BueiroJsonRepository`, mantendo a persistencia no arquivo JSON fora da rota. Os CRUDs de alertas, limpeza, compactacao e historico usam `RecordService` e `SQLAlchemyRecordRepository`, compartilhando o fluxo de criacao, consulta ordenada e transacao.

Na criacao de registros SQL, o repositorio executa `add`, `commit` e `refresh`. Se a transacao falhar, executa `rollback` e propaga o erro para o tratamento HTTP.

## Contratos da API

### Respostas de sucesso

As rotas do inventario de bueiros agora declaram DTOs de entrada e saida. As rotas CRUD existentes continuam retornando seus objetos ou listas diretamente, sem adicionar um envelope comum; isso preserva o formato dos campos consumidos pelo dashboard e pelo firmware.

Os endpoints de criacao de alertas, limpeza, compactacao e historico agora respondem com `201 Created` em vez do status padrao anterior, `200 OK`. Clientes que verificam exatamente o status HTTP devem aceitar `201`.

### Respostas de erro

Os erros HTTP, de validacao e inesperados usam `application/problem+json`, com campos padronizados:

```json
{
  "type": "about:blank",
  "title": "Unprocessable Content",
  "status": 422,
  "detail": "Um ou mais campos sao invalidos.",
  "instance": "/bueiros/",
  "errors": [
    {
      "location": ["body", "latitude_montante"],
      "message": "Input should be less than or equal to 90",
      "code": "less_than_equal"
    }
  ]
}
```

O campo `errors` aparece em falhas de validacao. Erros inesperados retornam uma mensagem generica ao cliente; o detalhe tecnico fica somente no log do servidor.

## Validacao de entrada

Os DTOs agora aplicam limites e regras por campo, incluindo textos obrigatorios com limite de tamanho, IDs positivos, coordenadas dentro dos limites geograficos, valores numericos finitos e valores nao negativos quando aplicavel. Alguns DTOs tambem removem espacos no inicio/fim e rejeitam propriedades desconhecidas.

Essas regras podem rejeitar entradas que antes eram aceitas, como campos extras, textos em branco ou valores fora dos limites. Respostas de validacao mantem o status HTTP `422`.

## Configuracao do banco

O valor de conexao com fallback para `root:1234` foi removido de `app/database.py`. A API exige `DATABASE_URL` no ambiente ou no arquivo `.env`. O arquivo `.env.example` contem apenas um exemplo com placeholders; substitua-os por valores reais antes de iniciar a API. Nao compartilhe nem versione credenciais do `.env`.

Exemplo de formato:

```env
DATABASE_URL=mysql+pymysql://USUARIO:SENHA@HOST:3306/bueiro_inteligente
```

## Como iniciar

Com as dependencias instaladas, execute a partir da pasta `bueiro_inteligente_api`:

```powershell
python -m uvicorn app.main:app --reload
```

A documentacao interativa da API fica em `http://127.0.0.1:8000/docs`. O painel React e iniciado em outro terminal:

```powershell
cd frontend
npm install
npm run dev
```

Execute os comandos na pasta `bueiro_inteligente_api`. O painel fica normalmente em `http://localhost:5173` e precisa da API em execucao na porta 8000. O Vite encaminha as chamadas `/api/*` ao FastAPI.

## Testes e validacao

Foram executados 14 testes unitarios dos fluxos de bueiros, tratamento de erros e service/repository SQL com sessao simulada. Tambem foi verificada a geracao do OpenAPI, incluindo o status `201` nos quatro endpoints CRUD, e os diagnosticos estaticos dos arquivos alterados.

Os testes de integracao com MySQL nao foram executados; e necessario validar as operacoes contra um banco acessivel no ambiente de execucao.

## Escopo ainda nao migrado

Os routers de sensores e IA continuam contendo consultas e orquestracao diretamente relacionadas aos modelos de predicao. A separacao dessas rotas requer testes com banco e substitutos para os componentes de IA, por isso ficou fora desta etapa. O formato dos sucessos tambem nao foi convertido para um envelope global, para evitar uma quebra maior nos consumidores atuais.