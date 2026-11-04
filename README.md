# 🌧️ Bueiro-Inteligente-IoT-TCC

Sistema inteligente automatizado para limpeza de bueiros urbanos utilizando Internet das Coisas (IoT), sensores e Inteligência Artificial.

---

## Trabalho de Sistemas Distribuídos: monitoramento de alagamentos

Este repositório contém a API, as migrações e o simulador que apoiam o trabalho
de Sistemas Distribuídos, reaproveitando o TCC **Bueiro Inteligente** para
monitorar sensores e receber **exclusivamente denúncias de alagamentos e
inundações**. O app React Native/Expo fica no repositório separado
[Bueiro-Inteligente-mobile--app](https://github.com/FledWriter3840/Bueiro-Inteligente-mobile--app).

### Executar a API

1. Instale e inicialize o MySQL, crie/importe o banco `bueiro_inteligente` e
   configure `bueiro_inteligente_api/.env` a partir de
   `bueiro_inteligente_api/.env.example`.
2. Execute uma vez a migração aditiva
   `bueiro_inteligente_api/migrations/001_app_mobile.sql` no banco existente.
   Ela adiciona coordenadas à tabela `sensor`, timestamps idempotentes em
   `leiturasensor` e a tabela `ocorrencias`, sem remover dados.
3. Na raiz do projeto, crie um ambiente Python e instale as dependências:

   ```powershell
   py -m venv .venv
   .\.venv\Scripts\Activate.ps1
   pip install -r requirements.txt
   ```

4. Inicie a API:

   ```powershell
   cd bueiro_inteligente_api
   python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

   A documentação interativa fica em `http://localhost:8000/docs`; o healthcheck
   está em `http://localhost:8000/saude`. Para demonstração com vários
   sensores, execute também, uma vez, a migração opcional
   `bueiro_inteligente_api/migrations/002_sensores_demo.sql`.

### Executar o simulador

Com a API em execução e pelo menos três sensores cadastrados:

```powershell
python simulador_bueiros.py --api-url http://localhost:8000 --intervalo 5 --ciclos 8
```

O simulador consulta `GET /bueiros` para obter IDs existentes e envia as
leituras para `POST /sensores/leitura`. Sem `--ciclos`, ele continua até ser
interrompido com `Ctrl+C`. Os níveis sobem até o estado crítico e depois variam.

### Executar o app no Expo Go

No clone do repositório mobile, entre em `bueiro-app`, copie `.env.example`
para `.env.local` e configure `EXPO_PUBLIC_API_URL` com o IPv4 do computador
na mesma rede Wi-Fi do celular (não use `localhost`). Instale e inicie:

   ```powershell
   cd bueiro-app
   npm install
   npx expo start --lan
   ```

Abra o QR code com Expo Go. Não é necessário Android Studio ou emulador. O mapa
usa Leaflet/OpenStreetMap sem chave paga e precisa de internet. Notificações
locais são usadas para transições a crítico; push remoto não é suportado no
Expo Go para Android.

Mais detalhes estão em [docs/arquitetura-distribuida-app.md](docs/arquitetura-distribuida-app.md),
[docs/conceitos-distribuidos-app.md](docs/conceitos-distribuidos-app.md) e
[docs/roteiro-demo-app.md](docs/roteiro-demo-app.md). Para executar os testes
da API, entre em `bueiro_inteligente_api` e rode
`python -m pytest tests/test_app_mobile.py tests/test_leitura_service.py`.

---

# 📖 Sobre o Projeto

O projeto tem como objetivo desenvolver um sistema inteligente capaz de monitorar, identificar e remover resíduos sólidos automaticamente de bueiros urbanos, ajudando na prevenção de enchentes e alagamentos em grandes centros urbanos.

A solução utiliza sensores, câmera, automação e Inteligência Artificial para detectar situações críticas e acionar mecanismos automáticos de limpeza.

---

# 🚀 Tecnologias Utilizadas

- ESP32
- Arduino
- IoT (Internet das Coisas)
- Inteligência Artificial
- Sensor Ultrassônico
- Banco de Dados MySQL
- GitHub
- Wokwi
- Figma
- C/C++
- Python
- JavaScript

---

# ⚙️ Funcionalidades

✅ Monitoramento do nível de resíduos  
✅ Captura de imagens do interior do bueiro  
✅ Acionamento automático da limpeza  
✅ Compactação de resíduos  
✅ Dashboard de monitoramento  
✅ Registro de dados operacionais  
✅ Emissão de alertas automáticos  
✅ Previsão de possíveis entupimentos com IA  

---

# 🧠 Objetivo da Solução

O sistema foi desenvolvido com foco em:

- prevenção de alagamentos;
- automação urbana;
- monitoramento inteligente;
- cidades inteligentes;
- sustentabilidade urbana.

---

# 🏗️ Estrutura do Projeto

```bash
Bueiro-Inteligente-IoT-TCC/
│
├── apresentacao/
├── banco de dados/
├── codigo/
├── diagramas/
├── docs/
├── imagens/
├── README.md
├── requirements.txt
└── Dump20260516.sql
```

---

# 📸 Simulações do Projeto

## FIGURA 6 - SIMULAÇÃO

![Simulação 6](imagens/FIGURA%206%20-%20SIMULAÇÃO.png)

---

## FIGURA 7 - SIMULAÇÃO

![Simulação 7](imagens/FIGURA%207%20-%20SIMULAÇÃO.png)

---

## FIGURA 8 - SIMULAÇÃO

![Simulação 8](imagens/FIGURA%208%20-%20SIMULAÇÃO.png)

---

# 📊 Diagramas do Sistema

## FIGURA 1 - DIAGRAMA DE CASO DE USO

![Caso de Uso](imagens/FIGURA%201%20-%20DIAGRAMAS%20DE%20CASO%20DE%20USO.png)

---

## FIGURA 2 - DIAGRAMA DE ATIVIDADE

![Diagrama de Atividade](imagens/FIGURA%202%20-%20DIAGRAMAS%20DE%20ATIVIDADE.png)

---

## FIGURA 3 - FLUXOGRAMA

![Fluxograma](imagens/FIGURA%203%20-%20FLUXOGRAMA.png)

---

## FIGURA 4 - MODELAGEM DA ARQUITETURA IOT

![Arquitetura IoT](imagens/FIGURA%204%20-%20MODELAGEM%20DA%20ARQUITETURA%20IOT.png)

---


## FIGURA 5 - DIAGRAMA ENTIDADE RELACIONAMENTO

![DER](imagens/FIGURA%205%20%E2%80%93%20Diagrama%20Entidade-Relacionamento%20do%20Sistema.png)

---

# 👨‍💻 Integrantes

- Alianny Rissato da Silva
- Giovanna Dias de Souza
- Leonardo Diogo Buzelin Julio
- Matheus de Souza Soares

---


# 👨‍🏫 Professor/Orientador

- Marco Gomes


---

# 🎓 Universidade

Universidade Paulista — UNIP  
Campus Paraíso  
Curso: Ciência da Computação

---

# 📚 Documentação

O projeto contém:

- Engenharia de Requisitos
- Casos de Uso
- Diagramas UML
- Arquitetura IoT
- Fluxogramas
- Banco de Dados
- Testes
- Prova de Conceito (POC)

---

# 🌎 Tema do Projeto

Sistema Inteligente de Limpeza Automática de Bueiros utilizando Internet das Coisas (IoT) e Inteligência Artificial.
