# Conceitos de Sistemas Distribuídos aplicados

O sistema distribui a coleta, o processamento e a visualização de informações
entre dispositivos IoT, API, MySQL, motor de IA e celulares. A comunicação
principal usa HTTP/REST com payloads JSON.

## Conceitos demonstrados

- **Heterogeneidade:** ESP32 com firmware C++, simulador Python, backend
  FastAPI/Python e app React Native/JavaScript ou TypeScript cooperam por
  contratos HTTP e JSON.
- **Escalabilidade:** vários sensores enviam leituras à mesma API; consultas
  agregadas em `/resumo` e filtros de ocorrências apoiam a visualização. A
  implementação atual usa uma instância da API e um banco MySQL, portanto não
  representa escalabilidade horizontal pronta para produção.
- **Concorrência:** diferentes sensores e cidadãos podem fazer requisições ao
  mesmo tempo. O banco persiste leituras e ocorrências; a chave de sensor e
  timestamp evita gravar novamente a mesma leitura reenviada.
- **Tolerância a falhas:** o app mantém o último dado válido em AsyncStorage e
  guarda denúncias pendentes para reenvio. O firmware retém até 50 leituras em
  uma fila de RAM enquanto tenta recuperar conexão. O healthcheck permite
  detectar indisponibilidade da API.
- **Transparência:** o app oferece mapa, lista, detalhe e resumo sem expor ao
  cidadão a distribuição interna entre sensores, serviço de IA e banco.
- **Protocolos e formatos:** HTTP/REST e JSON transportam telemetria, denúncias
  e consultas. O upload de imagens usa `multipart/form-data`; a API distribui
  os arquivos estáticos em `/uploads`.

## Pontos de falha e limitações

O MySQL e a instância da API são pontos centrais de falha. Sem conectividade, o
app pode consultar dados em cache e enfileirar uma denúncia, mas não consegue
atualizar o mapa em tempo real. A fila de telemetria do firmware é volátil e
pode ser perdida se o ESP32 desligar antes de reenviar; a fila de denúncias do
app persiste no armazenamento local, mas também depende de o aplicativo e o
arquivo de foto continuarem disponíveis. A escala percentual dos sensores é
demonstrativa até a calibração em campo. O mapa usa tiles públicos do
OpenStreetMap e exige conexão; os serviços externos de clima/topografia são
opcionais e não têm garantia de disponibilidade.

As notificações implementadas são locais e dependem da permissão do aparelho.
Push remoto não faz parte deste protótipo Expo Go. Também não há autenticação
ou autorização de operador nos endpoints demonstrativos; a implantação real
exige proteção dos dados, autenticação, backups e monitoração.
