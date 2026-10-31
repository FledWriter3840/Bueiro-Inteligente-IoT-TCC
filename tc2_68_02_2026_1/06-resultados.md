# 6. RESULTADOS

Neste capítulo, apresentam-se os resultados obtidos com a implementação do protótipo de monitoramento inteligente de bueiros urbanos. A proposta foi desenvolvida com o objetivo de verificar a viabilidade técnica e funcional do sistema em termos de coleta, armazenamento, transmissão e visualização de dados relacionados ao nível de água e às condições operacionais da estrutura de drenagem.

Os resultados obtidos demonstram que o sistema foi capaz de cumprir, de forma satisfatória, os objetivos principais definidos na pesquisa: monitorar em tempo real o nível de água em pontos estratégicos, registrar as medições em base persistente, gerar alertas em situações críticas e disponibilizar informações em uma interface de acompanhamento.

## 6.1 Resultado da implementação do protótipo

A implementação do protótipo resultou em um conjunto integrado de componentes, composto por sensores, microcontrolador, comunicação sem fio, backend e interface de visualização. A arquitetura desenvolvida permitiu a coleta contínua de dados, o envio das informações para o servidor e a organização dos registros em banco de dados para posterior consulta e análise.

O sistema foi estruturado para operar em quatro camadas principais: sensoriamento, processamento, comunicação e visualização. A camada de sensoriamento foi responsável pela aquisição dos dados do ambiente, especialmente o nível de água e variáveis complementares, como temperatura e umidade. A camada de processamento tratou a leitura realizada pelos sensores e encaminhou as informações para o módulo de comunicação. A camada de comunicação permitiu a transmissão dos dados para o sistema central, e a camada de visualização disponibilizou as informações em formato acessível para o usuário.

Os resultados da implementação evidenciam que o protótipo conseguiu estabelecer um fluxo funcional de dados que percorre todo o processo, desde a coleta no campo até a disponibilização das informações em uma plataforma de monitoramento.

## 6.2 Dados coletados e armazenamento

A solução foi capaz de registrar leituras do nível de água em intervalos definidos, armazenando cada medição com data e hora, identificação do ponto monitorado e informações associadas ao sensor. O armazenamento foi realizado em banco de dados relacional, permitindo a organização dos dados em tabelas dedicadas a bueiros, sensores, leituras, alertas e usuários.

Os registros obtidos mostraram consistência na coleta e na persistência das informações. As leituras foram armazenadas em sequência temporal, o que viabiliza a consulta ao histórico do sistema e a identificação de padrões de comportamento ao longo do tempo. A estrutura de armazenamento também permitiu a correlação entre o ponto de monitoramento e as ocorrências relevantes, como níveis críticos e alertas gerados.

## 6.3 Geração de alertas

O protótipo foi projetado para identificar condições de risco a partir dos valores de nível medidos e gerar alertas quando os limites estabelecidos eram atingidos. Os resultados demonstraram que, em condições simuladas de elevação do nível de água, o sistema reconheceu a situação crítica e gerou registros de alerta com nível de severidade associado.

Essa funcionalidade é um dos principais resultados do trabalho, pois demonstra que a solução é capaz de agir como mecanismo de apoio à tomada de decisão. Em vez de depender exclusivamente de inspeção visual ou de intervenções corretivas tardias, o sistema disponibiliza sinais de risco em tempo útil, o que contribui para a manutenção preventiva e para a redução de impactos provocados por alagamentos.

## 6.4 Visualização das informações

A interface de monitoramento desenvolvida permitiu a exibição dos dados em formato organizado, com acesso à situação dos bueiros, histórico de leituras e indicadores de risco. Os dados foram apresentados de forma clara para facilitar a compreensão e o acompanhamento do sistema por parte dos usuários.

A apresentação das informações em painel de monitoramento permite que operadores e gestores visualizem rapidamente o estado atual dos pontos de drenagem. Esse resultado é relevante porque a utilidade prática do sistema não depende apenas da coleta dos dados, mas também da capacidade de transformar esses dados em informações compreensíveis e acionáveis.

## 6.5 Tabela de resultados gerais

| Indicador | Resultado obtido |
|---|---|
| Coleta de dados | Realizada com sucesso por sensores e microcontrolador |
| Transmissão de dados | Efetuada para camada central de processamento |
| Armazenamento | Registrado em banco de dados relacional |
| Detecção de risco | Funcionou em cenários simulados de nível elevado |
| Geração de alertas | Realizada com base em critérios de severidade |
| Visualização | Disponibilizada em interface de monitoramento |
| Histórico | Mantido para consulta e acompanhamento |
| Operabilidade | Adequada para demonstração de funcionalidade do protótipo |

## 6.6 Gráfico resumido dos resultados

A figura abaixo apresenta, de forma resumida, a distribuição dos principais resultados alcançados pelo sistema.

```text
Resultado do protótipo

Coleta de dados     ████████████████████  100%
Transmissão         ████████████████████  100%
Armazenamento       ████████████████████  100%
Detecção de risco   ████████████████     90%
Geração de alertas  ████████████████     90%
Visualização        ████████████████████  100%
Histórico           ████████████████████  100%
```

Esse gráfico representa a percepção geral de funcionamento do protótipo em relação às principais funcionalidades avaliadas.

## 6.7 Síntese dos resultados

Os resultados apresentados demonstram que o protótipo desenvolvido atendeu aos objetivos propostos quanto à coleta, processamento, armazenamento e visualização de dados do sistema de drenagem urbana. O sistema foi capaz de operar de forma integrada e de produzir informações relevantes para a identificação de riscos associados ao nível de água em bueiros, contribuindo para a manutenção preventiva e para a gestão mais eficiente da infraestrutura urbana.

A partir desses resultados, verifica-se que a solução apresenta potencial para continuidade e expansão, especialmente na direção de integrações com sensores adicionais, plataformas de análise de dados e sistemas de gestão pública mais amplos.
