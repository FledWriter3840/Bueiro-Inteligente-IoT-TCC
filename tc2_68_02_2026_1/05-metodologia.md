# 5. METODOLOGIA

A metodologia adotada neste trabalho foi definida com o objetivo de orientar, de forma rigorosa e sistemática, o desenvolvimento do protótipo de um sistema inteligente de monitoramento para bueiros urbanos. A pesquisa foi estruturada como um estudo aplicado, com enfoque em engenharia de software e em desenvolvimento tecnológico, buscando integrar aspectos teóricos, de projeto, de implementação e de validação. A escolha dessa abordagem se justifica pela necessidade de conectar a fundamentação acadêmica com a construção de uma solução prática, passível de uso em cenários reais de gestão urbana.

A metodologia contempla, portanto, a elicitação de requisitos, a definição da arquitetura do sistema, a modelagem de banco de dados, o planejamento das atividades de desenvolvimento, a implementação do protótipo e a execução de testes de validação. Nesse sentido, a pesquisa não se limita à análise conceitual do problema, mas também busca demonstrar a viabilidade de uma solução tecnológica para monitoramento em tempo real de redes de drenagem, com foco na prevenção de enchentes e na manutenção preventiva.

A fundamentação metodológica também considera referências da área de engenharia de software e de pesquisa aplicada, especialmente no que diz respeito à análise de requisitos, ao desenvolvimento incremental e à validação por testes. Segundo PRESSMAN e MAXIM (2016), a correta elicitação de requisitos é um dos pilares fundamentais para o sucesso de um projeto de software, pois direciona a arquitetura, o escopo e o grau de qualidade da solução. Já ROYCE (1970) e BOEHM (1988) enfatizam que a definição clara dos requisitos e a validação contínua do produto são essenciais para reduzir retrabalho e aumentar a aderência do sistema às necessidades do usuário.

Do ponto de vista da pesquisa, a metodologia foi organizada em etapas sequenciais e interdependentes, que permitiram a construção de uma solução confiável, coerente com as exigências de infraestrutura urbana e de desenvolvimento tecnológico. A etapa inicial consistiu na identificação do problema, no levantamento de informações e na revisão bibliográfica sobre drenagem urbana, IoT e gestão de sistemas inteligentes de infraestrutura. Em seguida, foi realizada a elicitação dos requisitos com foco nos stakeholders envolvidos, seguida pela definição da arquitetura do sistema e pela escolha das tecnologias. Depois, o fluxo de dados, o banco de dados e os módulos do sistema foram modelados, permitindo a implementação do protótipo. Finalmente, foi planejada e executada a validação dos casos de teste, com análise dos resultados e avaliação da adequação funcional da solução.

## 5.1 Abordagem da pesquisa

A pesquisa foi classificada como aplicada, exploratória e experimental, pois busca solucionar um problema concreto de infraestrutura urbana por meio da construção e avaliação de um protótipo tecnológico. A abordagem aplicada é adequada porque o objetivo não é apenas compreender fenômenos, mas também propor uma solução funcional e verificável. A dimensão exploratória se manifesta na investigação do tema em diferentes fontes acadêmicas, técnicas e operacionais; já a dimensão experimental aparece na implementação do protótipo e na execução de testes que validam seu desempenho.

Quanto ao método de investigação, o trabalho adotou uma combinação de pesquisa documental, levantamento de requisitos, estudo de caso e desenvolvimento de protótipo. A pesquisa documental foi utilizada para consolidar o conhecimento bibliográfico e técnico; o levantamento de requisitos serviu para identificar as necessidades dos usuários e do problema de pesquisa; e o desenvolvimento do protótipo permitiu validar as hipóteses por meio de testes funcionais e de análise de comportamento do sistema em condições simuladas.

## 5.2 Engenharia de software e roteiro do desenvolvimento

A parte de engenharia de software do projeto foi organizada com base em um processo iterativo e incremental, combinando elementos da abordagem tradicional e de métodos ágeis. Essa escolha se justifica pela necessidade de equilibrar a definição formal dos requisitos com a flexibilização necessária para ajustes durante a implementação do protótipo. O processo foi estruturado em fases bem definidas: (i) levantamentos iniciais e contextualização do problema; (ii) elicitação de requisitos; (iii) análise e modelagem; (iv) arquitetura do sistema; (v) implementação; (vi) testes; e (vii) validação e ajustes.

A adoção de uma abordagem incremental foi importante porque permitiu a evolução do sistema conforme surgiam novos requisitos ou limitações identificadas durante a análise. Essa dinâmica é compatível com a natureza de projetos de software voltados à automação de infraestrutura urbana, em que a realidade operacional pode exigir adaptações em relação ao escopo inicial. Além disso, a metodologia permitiu maior controle de riscos, definição mais clara de artefatos e melhor organização dos componentes funcionais do sistema.

## 5.3 Elicitação de requisitos

A elicitação de requisitos foi uma etapa central da pesquisa, pois definiu o escopo da solução e orientou a especificação do sistema. Este processo foi realizado por meio de análise documental, discussão do problema de pesquisa e identificação das necessidades dos principais atores envolvidos no uso do sistema. A coleta de informações foi baseada em observações relacionadas ao problema de drenagem urbana, em dados bibliográficos e em considerações técnicas sobre uso operacional em contextos públicos e institucionais.

### 5.3.1 Stakeholders

Os principais stakeholders identificados foram:

- Prefeitura municipal e órgãos de infraestrutura urbana;
- equipes de manutenção e operação de redes de drenagem;
- empresas de saneamento e gestão hídrica;
- gestores de risco e defesa civil;
- usuários finais e operadores do sistema;
- pesquisadores e orientadores da pesquisa;
- equipe de desenvolvimento responsável pela implementação do protótipo.

A identificação desses atores foi importante para compreender não apenas a funcionalidade do sistema, mas também a forma como ele deveria ser acessado, monitorado e operado. Em projetos públicos e urbanos, a análise dos stakeholders medeia diretamente a aceitação da solução, a sua usabilidade e a relevância de seus alertas e indicadores.

### 5.3.2 Delimitação de escopo

O escopo do sistema foi delimitado para atender ao problema principal da pesquisa: monitorar condições críticas de bueiros urbanos, detectar elevação do nível de água e fornecer informações que ajudem na manutenção preventiva e na tomada de decisão. O sistema foi concebido para operar com sensores de nível e comunicação de dados em tempo real, sem depender de inspeções manuais frequentes. A solução incluiu coleta dos dados em campo, envio de informações para uma plataforma de gestão e disponibilização das informações em um painel de acompanhamento.

O escopo excluiu, em fase inicial, funções mais amplas de gestão urbana completa, como controle integrado de toda a rede de esgotos, gestão financeira, planejamento de obras civis e coordenação de equipes em múltiplas cidades. Essa delimitação foi necessária para manter o projeto focado em sua viabilidade técnica e em seu objetivo acadêmico de demonstrar a funcionalidade do protótipo.

### 5.3.3 Requisitos funcionais

Os requisitos funcionais definidos para o sistema são aqueles que descrevem as atividades que o sistema deve executar para atender à finalidade proposta. A seguir, apresentam-se os principais requisitos identificados:

- Monitorar o nível de água em bueiros por meio de sensores;
- Coletar e registrar dados em intervalos definidos de tempo;
- Enviar informações para um servidor ou plataforma em nuvem;
- Identificar condições de risco, como nível crítico de água ou obstrução;
- Emitir alertas para equipes de manutenção e gestores;
- Permitir consulta de histórico de medições;
- Visualizar dados em dashboard web ou mobile;
- Registrar eventos e ocorrências relacionadas à drenagem;
- Manter autenticação e controle de acesso ao sistema;
- Permitir organização de múltiplos bueiros por região, setor ou cidade;
- Exibir indicadores de status do sistema, como online/offline e nível de risco.

### 5.3.4 Requisitos não funcionais

Os requisitos não funcionais expressam características de qualidade, confiabilidade e desempenho que o sistema deve atender. Foram definidos os seguintes requisitos:

- Disponibilidade da coleta e envio de dados em tempo real;
- Confiabilidade da comunicação entre sensores e plataforma;
- Segurança no armazenamento e transmissão de dados;
- Escalabilidade para suportar múltiplos dispositivos e bueiros;
- Manutenibilidade do código e da arquitetura;
- Facilidade de uso na interface de acompanhamento;
- Baixo consumo de energia dos dispositivos embarcados;
- Robustez frente a condições ambientais externas, como chuva, umidade e variações de temperatura;
- Compatibilidade com tecnologias de comunicação sem fio de uso comum em IoT.

### 5.3.5 Critérios de qualidade desejados

Os critérios de qualidade estabelecidos para o projeto incluem:

- Precisão na medição do nível de água;
- Tempo adequado de resposta para geração de alertas;
- Funcionalidade da autenticação e controle de acesso;
- Integração estável entre dispositivos, backend e interface;
- Usabilidade do painel de monitoramento;
- Organização dos dados por histórico e relatórios;
- Facilidade de manutenção e evolução futura;
- Conformidade com padrões de segurança e armazenamento de dados de sistemas públicos.

## 5.4 Planejamento do projeto

O planejamento do projeto foi realizado com base no ciclo de desenvolvimento do sistema, considerando as etapas de análise, projeto, implementação e validação. O cronograma foi organizado para permitir o acompanhamento de cada fase com prazos e entregáveis definidos. O planejamento também contemplou a análise de risco, a definição de tecnologias e os artefatos produzidos ao longo do desenvolvimento.

As principais fases do planejamento foram:

1. Levantamento do problema e revisão bibliográfica;
2. Definição dos requisitos do sistema;
3. Projeto da arquitetura e modelagem de dados;
4. Implementação do protótipo de coleta e envio de informações;
5. Desenvolvimento da interface de visualização;
6. Configuração do banco de dados e do serviço em nuvem;
7. Testes de integração e validação funcional;
8. Ajustes finais e documentação da solução.

Esse cronograma foi essencial para garantir que as atividades de desenvolvimento estivessem alinhadas com os objetivos acadêmicos do projeto e com os critérios de qualidade esperados para um protótipo de pesquisa aplicada.

## 5.5 Artefatos produzidos

Durante o desenvolvimento, foram gerados vários artefatos de engenharia de software, que contribuíram para a formalização do projeto. Entre os artefatos principais, destacam-se:

- especificação de requisitos;
- diagrama de casos de uso;
- diagrama de arquitetura do sistema;
- definição das tecnologias e padrões;
- modelagem do banco de dados;
- protótipo funcional;
- cenários de teste;
- documentação e relatórios de execução de testes.

Esses artefatos permitiram uma visão clara da solução, facilitando a comunicação entre a equipe de desenvolvimento, os stakeholders e a orientação acadêmica. Também foram úteis para validar se o sistema estava atendendo aos requisitos identificados e se as decisões técnicas eram coerentes com os objetivos de pesquisa.

## 5.6 Desenho da arquitetura do sistema

A arquitetura do sistema foi definida com foco na integração de sensores, processamento local, comunicação de dados e plataforma de visualização. O desenho foi elaborado para atender ao ciclo completo de coleta, armazenamento, processamento e apresentação das informações. A solução foi pensada como um sistema distribuído, composto por camadas bem definidas para facilitar manutenção, escalabilidade e organização do código.

### 5.6.1 Arquitetura geral

A arquitetura proposta contempla as seguintes camadas:

- camada de sensoriamento: dispositivos instalados nos bueiros para medir nível de água e condições ambientais;
- camada de processamento embarcado: microcontrolador responsável pela leitura dos sensores e pela comunicação com o módulo de rede;
- camada de comunicação: transmissão dos dados por meio de rede sem fio ou rede celular;
- camada de backend: aplicação responsável por receber, processar, validar e armazenar as informações;
- camada de persistência: banco de dados para armazenamento dos registros e dos eventos;
- camada de interface: painel web ou mobile para visualização dos dados e geração de alertas;
- camada de alertas: mecanismo de notificação para manutenção e operação.

Essa estrutura possibilita a separação de responsabilidades, reduz acoplamento entre componentes e facilita futuras expansões do sistema, como inclusão de novos sensores, integração com mapas georreferenciados ou aumento do número de pontos monitorados.

### 5.6.2 Uso de nuvem

O projeto foi concebido para utilizar uma infraestrutura em nuvem para receber e processar os dados coletados pelos dispositivos na rede de drenagem. A utilização de serviços em nuvem é justificada por diversas vantagens, como armazenamento seguro, acesso remoto, escalabilidade, disponibilidade e capacidade de integração com APIs e dashboards. Em uma solução aplicada à infraestrutura urbana, a nuvem também permite que os dados sejam acessados por diferentes agentes, como gestores públicos, equipes de manutenção e pesquisadores, independentemente do local físico.

A arquitetura em nuvem pode ser configurada em plataformas como AWS, Microsoft Azure ou Google Cloud, com uso de serviços de banco de dados, API, autenticação e armazenamento de arquivos. Para o protótipo desenvolvido, a solução pode ser implantada em um ambiente de baixa complexidade, com servidor hospedado em nuvem ou em infraestrutura local, dependendo do nível de exigência do projeto e da disponibilidade operacional.

### 5.6.3 Backend

O backend é responsável por receber os dados provenientes dos sensores, validar as informações, armazenar os registros e disponibilizar endpoints para consumo da interface e de aplicativos. Esse módulo pode ser implementado com tecnologias como Node.js, Python (Flask ou FastAPI) ou Java, sendo que a escolha depende dos requisitos de integração, tempo de resposta e familiaridade da equipe de desenvolvimento.

As funções principais do backend incluem:

- recebimento das mensagens dos dispositivos;
- autenticação e autorização de usuários e dispositivos;
- validação e padronização dos dados;
- persistência no banco de dados;
- processamento de regras de alerta;
- exposição de APIs REST para frontend e mobile;
- geração de logs e auditoria de eventos.

A existência do backend é fundamental para garantir que os dados coletados sejam organizados, consistentes e acessíveis em tempo real por meio de um canal seguro e controlado.

### 5.6.4 Frontend

O frontend do sistema tem como objetivo apresentar os dados em um ambiente amigável e funcional para gestão, monitoramento e tomada de decisão. A interface pode ser implementada em uma aplicação web responsiva, permitindo acesso por navegadores em desktops e tablets, e também por aplicação mobile em smartphones.

A interface deve contemplar:

- painel com status dos bueiros;
- indicadores de nível de água;
- histórico de medições;
- notificações de alertas;
- filtros por município, região, setor ou ponto de coleta;
- mapa ou listagem dos dispositivos cadastrados;
- relatórios operacionais e de manutenção.

O frontend é essencial para a usabilidade da solução, pois transforma os dados em informação útil para os agentes envolvidos na gestão pública e na manutenção urbana.

### 5.6.5 Banco de dados

A persistência dos dados é um elemento crítico do sistema, pois é responsável por registrar as leituras, os eventos e os históricos necessários para análise e manutenção. O banco de dados deve garantir segurança, integridade e organização das informações coletadas pelos sensores. Em sistemas de IoT e monitoramento urbano, isolar corretamente as entidades e garantir o relacionamento entre elas é fundamental para a confiabilidade do sistema.

O banco pode ser relacional, como PostgreSQL ou MySQL, ou não relacional, como MongoDB, dependendo da escala e da natureza dos dados. Para uma solução de gestão de bueiros e leitura de sensores, a abordagem relacional é mais adequada, porque favorece consistência, integridade referencial, consultas estruturadas e suporte à organização de tabelas e métricas operacionais.

### 5.6.6 Mobile

A arquitetura também pode incluir uma aplicação mobile para facilitar o acesso às informações em campo. Essa funcionalidade é especialmente útil para equipes de manutenção, que podem consultar o estado dos bueiros, visualizar alertas e confirmar intervenção em tempo real. O uso de mobile também facilita o envio de relatórios, organização de ocorrências e acompanhamento de atividades em campo.

A aplicação mobile pode ser desenvolvida em Flutter, React Native ou Android nativo, dependendo dos objetivos, do público-alvo e da disponibilidade da equipe. Em um protótipo acadêmico, a aplicação mobile pode ser limitada a funcionalidades essenciais, como consulta de status, visualização de alertas e acesso ao histórico de ocorrências.

## 5.7 Banco de dados: especificação e modelagem

A modelagem do banco de dados foi elaborada com base na necessidade de armazenar as informações produzidas pelo monitoramento dos bueiros. O sistema deve registrar dados dos dispositivos, informações dos pontos de monitoramento, leituras dos sensores, alertas gerados e ocorrências de manutenção. A estrutura do banco foi pensada para contemplar integridade dos dados, histórico de utilização e controle de acesso às funcionalidades do sistema.

### 5.7.1 Dados a serem armazenados

Os dados armazenados no sistema incluem:

- cadastro dos usuários do sistema;
- cadastro dos bueiros e sua localização;
- informações dos sensores instalados;
- leituras periódicas do nível de água;
- histórico de eventos de risco e alarme;
- registro de alertas emitidos;
- registros de manutenção e intervenções;
- dados temporais e geográficos associados aos pontos monitorados;
- status operacional dos dispositivos.

Esses dados são essenciais para a análise do comportamento dos bueiros, identificação de padrões, avaliação de riscos e acompanhamento das ações corretivas.

### 5.7.2 Modelagem conceitual

A modelagem conceitual do banco é composta pelas seguintes entidades principais:

- Usuário: representa os operadores, gestores ou administradores do sistema;
- Município ou região: identifica a área urbana atendida;
- Bueiro: representa cada ponto de drenagem monitorado;
- Sensor: descreve os dispositivos instalados em cada bueiro;
- Leitura: registra os dados coletados em cada período de medição;
- Alerta: armazena ocorrências de risco ou nível crítico;
- Manutenção: registra intervenções realizadas no equipamento ou na estrutura.

A modelagem conceitual demonstra que o sistema deve manter um relacionamento entre bueiros, sensores, leituras e alertas, permitindo que o histórico seja consultado por local, período e tipo de problema.

### 5.7.3 Modelagem lógica

A modelagem lógica foi organizada em tabelas com atributos estruturados e identificadores únicos, de acordo com a necessidade funcional do sistema. Os principais componentes do modelo lógico são descritos a seguir.

#### Tabela: usuario

Atributos principais:

- id_usuario (PK): identificador único do usuário;
- nome: nome completo;
- email: endereço eletrônico;
- senha: senha criptografada;
- perfil: administrador, operador ou gestor;
- data_cadastro: data de criação do registro;
- status: ativo/inativo.

Restrição: email deve ser único; perfil deve seguir domínio de valores pré-definidos.

#### Tabela: municipio

Atributos principais:

- id_municipio (PK): identificador da cidade ou região;
- nome: nome do município;
- estado: unidade federativa;
- codigo_ibge: código oficial do município;
- data_cadastro: data de criação do registro.

Restrição: nome e estado devem ser preenchidos obrigatoriamente.

#### Tabela: bueiro

Atributos principais:

- id_bueiro (PK): identificador do ponto de monitoramento;
- id_municipio (FK): município ao qual o bueiro pertence;
- nome: identificação do bueiro;
- latitude: coordenada geográfica;
- longitude: coordenada geográfica;
- endereco: endereço ou referência do local;
- status: ativo/inativo/manutenção;
- data_instalacao: data de instalação do equipamento.

Restrição: coordenadas devem respeitar valores numéricos válidos; status deve obedecer a domínio específico.

#### Tabela: sensor

Atributos principais:

- id_sensor (PK): identificador do sensor;
- id_bueiro (FK): bueiro ao qual o sensor está associado;
- tipo_sensor: nível de água, sensor de presença, temperatura, umidade, etc.;
- modelo: modelo do equipamento;
- data_instalacao: data da instalação;
- status: operacional, em manutenção ou falho.

Restrição: tipo_sensor e status devem respeitar domínios pré-definidos.

#### Tabela: leitura

Atributos principais:

- id_leitura (PK): identificador da leitura;
- id_bueiro (FK): bueiro monitorado;
- id_sensor (FK): sensor relacionado;
- nivel_agua: valor medido do nível de água;
- temperatura: temperatura ambiente ou do equipamento;
- umidade: percentual de umidade;
- data_hora: data e hora da coleta;
- valor_criticidade: classificação da leitura conforme nível de risco.

Restrição: nível_agua e data_hora devem ser obrigatórios; o valor de nível deve respeitar faixas plausíveis para a operação do equipamento.

#### Tabela: alerta

Atributos principais:

- id_alerta (PK): identificador do alarme;
- id_bueiro (FK): bueiro relacionado;
- tipo_alerta: nível crítico, obstrução, falha de sensor, comunicação indisponível;
- descricao: descrição detalhada do evento;
- data_hora: momento em que o alerta foi gerado;
- nivel_severidade: baixo, médio, alto, crítico;
- status: aberto, em análise, resolvido.

Restrição: severidade e status devem respeitar valores previamente definidos.

#### Tabela: manutencao

Atributos principais:

- id_manutencao (PK): identificador da manutenção;
- id_bueiro (FK): bueiro atendido;
- id_usuario (FK): responsável pela ação;
- tipo_manutencao: preventiva, corretiva, inspeção;
- descricao: descrição da atividade;
- data_inicio: início da manutenção;
- data_fim: fim da manutenção;
- status: agendada, em andamento, concluída.

Restrição: data_fim deve ser maior ou igual a data_inicio quando preenchida.

### 5.7.4 Modelagem física

A modelagem física do banco foi concebida para uso em banco relacional, com foco em integridade, performance e facilidade de consulta. Os campos numéricos devem ser tipados com precisão adequada para valores de sensores e coordenadas geográficas; as datas devem seguir padrões consistentes de armazenamento em UTC ou em horário local, conforme a estratégia de operação. O uso de índices em atributos como id_bueiro, data_hora, id_sensor e status é recomendável para otimizar consultas históricas e alertas em tempo real.

A modelagem física também considerou a necessidade de armazenamento histórico, o que implica em manter registros de leituras em tabelas de grande volume. Para isso, é recomendável a utilização de particionamento ou registros organizados por período em ambientes de produção, caso o sistema seja expandido para atender múltiplos pontos de monitoramento de forma contínua.

### 5.7.5 DER (Diagrama Entidade-Relacionamento)

O Diagrama Entidade-Relacionamento (DER) do sistema pode ser descrito de forma resumida da seguinte maneira:

- Um município possui vários bueiros;
- Um bueiro pode ter vários sensores;
- Um sensor pode gerar várias leituras;
- Um bueiro pode gerar vários alertas;
- Um usuário pode registrar várias manutenções;
- Uma manutenção pode estar associada a um ou mais bueiros.

Esse relacionamento garante que as informações sejam integradas e que o sistema tenha capacidade de acompanhar, em nível operacional, o histórico de cada ponto de monitoramento.

## 5.8 Prototipação e desenvolvimento do sistema

A etapa de prototipação foi realizada após a definição dos requisitos e da arquitetura. O protótipo foi desenvolvido com foco em demonstrar a funcionalidade principal do sistema: monitorar o nível de água em bueiros e disponibilizar alertas em tempo real. O protótipo contemplou o uso de sensores, processamento eletrônico, comunicação e dashboard de acompanhamento.

A implementação inicial envolveu a criação da base técnica do hardware e da lógica de leitura. Em seguida, foi configurada a comunicação com a camada de backend. Na sequência, o banco de dados foi estruturado para receber as leituras e a interface foi desenvolvida para visualizar os dados e os indicadores de risco.

O protótipo foi concebido como uma solução de validação tecnológica, isto é, um modelo funcional capaz de demonstrar que a proposta é viável e que a arquitetura definida é adequada ao problema proposto. A simplicidade do protótipo foi deliberada para permitir testes, ajustes e validação sem comprometer o foco da pesquisa.

## 5.9 Casos de teste e validação

A validação do sistema foi conduzida por meio da execução de casos de teste, com objetivo de verificar se o protótipo atendia aos requisitos funcionais e não funcionais definidos. Os testes contemplaram aspectos como leitura dos sensores, envio dos dados, persistência no banco, geração de alertas e funcionamento da interface.

Os principais casos de teste incluem:

- teste de leitura do sensor de nível em situação normal;
- teste de leitura com nível elevado de água;
- teste de envio de dados para o backend;
- teste de persistência no banco de dados;
- teste de geração de alerta de risco;
- teste de visualização das informações no dashboard;
- teste de autenticação de usuários;
- teste de disponibilidade da comunicação em rede;
- teste de recuperação de falhas temporárias;
- teste de consistência dos registros históricos.

A execução desses casos de teste permitiu verificar se a solução apresentava comportamento aceitável, identificando pontos de melhoria e ajustando elementos críticos da arquitetura. O conjunto de resultados obtidos foi utilizado como evidência de validade funcional do protótipo e como base para a análise final do projeto.

## 5.10 Justificativa da metodologia

A metodologia adotada foi escolhida pela sua capacidade de combinar rigor científico, viabilidade técnica e adequação ao contexto prático da pesquisa. A abordagem fundamentada em requisitos, arquitetura, prototipação e testes é compatível com a natureza de projetos de desenvolvimento de sistemas inteligentes para infraestrutura urbana, pois permite demonstrar não apenas a teoria por trás da solução, mas também a execução de uma implementação funcional.

Além disso, a organização metodológica favoreceu a gestão do projeto, reduzindo riscos de divergência entre o problema identificado e a solução implementada. A escolha de uma estratégia estruturada, porém flexível, foi essencial para garantir que o protótipo pudesse evoluir conforme as necessidades emergentes da pesquisa e da aplicação real.

Em síntese, a metodologia adotada neste trabalho foi adequada para o desenvolvimento do sistema de monitoramento de bueiros, pois reuniu fundamentos de engenharia de software, pesquisa aplicada, modelagem de dados e validação técnica, evidenciando a viabilidade da solução proposta.

Palavras-chave: metodologia; engenharia de software; elicitação de requisitos; arquitetura de software; banco de dados; IoT; monitoramento de bueiros.
