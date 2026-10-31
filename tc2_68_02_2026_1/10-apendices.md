# 10. APÊNDICES

Os apêndices têm a finalidade de complementar o trabalho, apresentando materiais suplementares que ajudam na compreensão do projeto, mas que não são essenciais para a narrativa principal do texto. Neste trabalho, os apêndices podem reunir informações técnicas, esquemas de arquitetura, tabelas de dados, diagramas e materiais de apoio que reforcem a proposta de monitoramento inteligente de bueiros urbanos.

## Apêndice A: Arquitetura do sistema

Neste apêndice, apresenta-se o esquema geral da arquitetura do protótipo, com destaque para os blocos funcionais do sistema.

- Sensores de monitoramento: responsáveis pela leitura de nível de água e outras variáveis relevantes;
- Microcontrolador: processa os dados captados e organiza a comunicação;
- Módulo de comunicação: responsável por transmitir as informações para o backend ou plataforma central;
- Backend: módulo que recebe, valida e armazena os dados;
- Banco de dados: estrutura para armazenamento de leituras, alertas e manutenção;
- Frontend: painel de visualização para acompanhamento em tempo real;
- Aplicação mobile: possível extensão para uso em campo por equipes de manutenção.

A arquitetura pode ser representada na seguinte forma:

```text
[Sensor de nível] --> [Microcontrolador] --> [Módulo de comunicação]
                                              |
                                              v
                                         [Backend/API]
                                              |
                                              v
                                        [Banco de Dados]
                                              |
                                              v
                                      [Dashboard / Frontend]
                                              |
                                              v
                                      [Alertas e manutenção]
```

Este esquema reforça a lógica do sistema, mostrando a sequência de coleta, processamento, armazenamento e disponibilização das informações para usuários e gestores.

## Apêndice B: Estrutura do banco de dados

Este apêndice apresenta a organização lógica das principais tabelas do sistema de monitoramento.

### Tabela 1: Usuario

| Campo | Tipo | Descrição |
|---|---|---|
| id_usuario | inteiro | Identificador único do usuário |
| nome | texto | Nome completo |
| email | texto | Email de acesso |
| senha | texto | Senha criptografada |
| perfil | texto | Papel do usuário no sistema |
| data_cadastro | data | Data de criação do registro |
| status | texto | Situação do usuário |

### Tabela 2: Municipio

| Campo | Tipo | Descrição |
|---|---|---|
| id_municipio | inteiro | Identificador do município |
| nome | texto | Nome do município |
| estado | texto | Unidade federativa |
| codigo_ibge | texto | Código oficial do município |
| data_cadastro | data | Data do cadastro |

### Tabela 3: Bueiro

| Campo | Tipo | Descrição |
|---|---|---|
| id_bueiro | inteiro | Identificador do bueiro |
| id_municipio | inteiro | Município relacionado |
| nome | texto | Nome ou identificação do bueiro |
| latitude | decimal | Coordenada geográfica |
| longitude | decimal | Coordenada geográfica |
| endereco | texto | Localização do ponto |
| status | texto | Situação operacional |
| data_instalacao | data | Data de instalação |

### Tabela 4: Sensor

| Campo | Tipo | Descrição |
|---|---|---|
| id_sensor | inteiro | Identificador do sensor |
| id_bueiro | inteiro | Bueiro associado |
| tipo_sensor | texto | Tipo de sensor |
| modelo | texto | Modelo do equipamento |
| data_instalacao | data | Data da instalação |
| status | texto | Estado operacional |

### Tabela 5: Leitura

| Campo | Tipo | Descrição |
|---|---|---|
| id_leitura | inteiro | Identificador da leitura |
| id_bueiro | inteiro | Bueiro monitorado |
| id_sensor | inteiro | Sensor relacionado |
| nivel_agua | decimal | Nível de água medido |
| temperatura | decimal | Temperatura ambiente |
| umidade | decimal | Umidade relativa |
| data_hora | datetime | Data e hora da leitura |
| valor_criticidade | texto | Classificação da leitura |

### Tabela 6: Alerta

| Campo | Tipo | Descrição |
|---|---|---|
| id_alerta | inteiro | Identificador do alerta |
| id_bueiro | inteiro | Bueiro relacionado |
| tipo_alerta | texto | Tipo do evento |
| descricao | texto | Descrição do alerta |
| data_hora | datetime | Data e hora do evento |
| nivel_severidade | texto | Gravidade do alerta |
| status | texto | Situação do alerta |

### Tabela 7: Manutencao

| Campo | Tipo | Descrição |
|---|---|---|
| id_manutencao | inteiro | Identificador da manutenção |
| id_bueiro | inteiro | Bueiro atendido |
| id_usuario | inteiro | Responsável pela ação |
| tipo_manutencao | texto | Tipo de intervenção |
| descricao | texto | Descrição da atividade |
| data_inicio | datetime | Data de início |
| data_fim | datetime | Data de término |
| status | texto | Estado da manutenção |

Este conjunto de tabelas organiza os dados essenciais do sistema e permite a rastreabilidade das leituras, alertas e ações corretivas.

## Apêndice C: Critérios de teste do protótipo

Este apêndice apresenta os critérios usados para validação funcional do sistema proposto.

- Teste de leitura de sensor em condição normal;
- Teste de leitura com elevação do nível de água;
- Teste de envio dos dados para o backend;
- Teste de persistência no banco de dados;
- Teste de geração de alerta de risco;
- Teste de visualização em dashboard;
- Teste de autenticação e controle de acesso;
- Teste de integridade e consistência dos dados;
- Teste de disponibilidade da comunicação;
- Teste de operação em cenário crítico.

Esses critérios foram utilizados para verificar a funcionalidade do protótipo e a adequação do sistema aos requisitos previamente definidos.

## Apêndice D: Exemplo de relatório de operação

A tabela abaixo exemplifica como as informações podem ser apresentadas ao operador do sistema.

| Data e hora | Bueiro | Nível de água | Severidade | Status |
|---|---|---:|---|---|
| 2026-05-14 08:00 | Bueiro A | 0,45 m | Baixa | Normal |
| 2026-05-14 09:30 | Bueiro A | 0,82 m | Média | Atenção |
| 2026-05-14 10:15 | Bueiro A | 1,20 m | Alta | Alerta |
| 2026-05-14 11:00 | Bueiro B | 0,38 m | Baixa | Normal |

Esse relatório demonstra como o sistema pode ser utilizado para acompanhamento em tempo real e apoio à priorização de intervenções.

## Apêndice E: Observações técnicas complementares

Este apêndice reúne considerações técnicas adicionais relevantes para a implementação e evolução do sistema.

- O uso de sensores deve considerar condições externas, como umidade e presença de detritos;
- A comunicação sem fio deve ser robusta frente a falhas temporárias de rede;
- O armazenamento em banco de dados deve garantir integridade e histórico para análise;
- O frontend deve ser intuitivo e permitir acesso rápido à situação dos pontos monitorados;
- A aplicação pode evoluir para integração com mapas georreferenciados e alertas automáticos;
- A manutenção preventiva deve ser orientada pelos indicadores de nível de risco e por eventos registrados.

Essas observações complementares reforçam que o projeto é uma base funcional para futuras implementações e integrações em contextos reais de gestão urbana.

## Apêndice F: Materiais de apoio e referências complementares

Este apêndice reúne materiais de apoio, como figuras, esquemas e informações extraídas de fontes relacionadas ao tema. Esses materiais não substituem a bibliografia principal, mas servem como suporte visual e conceitual para a compreensão do problema e da solução proposta.

Em projetos acadêmicos, tais materiais podem incluir:

- desenhos técnicos do protótipo;
- diagramas de infraestrutura urbana;
- imagens de sensores e módulos de comunicação;
- tabelas de comparação de tecnologias de IoT;
- notas de engenharia de software e arquitetura de sistemas.

Os apêndices são, portanto, espaços para apresentar documentação técnica adicional que enriquece o trabalho sem alterar o núcleo da pesquisa.
