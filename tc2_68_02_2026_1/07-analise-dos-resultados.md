# 7. ANÁLISE DOS RESULTADOS

A análise dos resultados obtidos no protótipo de monitoramento inteligente de bueiros urbanos permite verificar em que medida a solução proposta respondeu ao problema identificado e se as hipóteses formuladas ao longo da pesquisa foram confirmadas ou necessitaram de ajustes. Esta etapa é fundamental no trabalho, porque não se limita à apresentação dos dados, mas sim à interpretação crítica dos resultados, considerando os objetivos do estudo, a metodologia adotada, a literatura revisada e as limitações observadas durante a implementação.

Os dados coletados e registrados pelo sistema demonstraram que a arquitetura proposta foi capaz de realizar, de forma funcional, as operações essenciais de monitoramento: coleta de dados, transmissão, processamento, armazenamento e visualização das informações. Nesse contexto, a solução apresentou comportamento coerente com o objetivo de apoiar a gestão urbana por meio de monitoramento contínuo e geração de alertas em situações críticas. A análise desses resultados indica que o protótipo alcançou a viabilidade técnica desejada, ainda que com limitações próprias do desenvolvimento em escala acadêmica e experimental.

## 7.1 Verificação das hipóteses da pesquisa

A primeira hipótese formulada no trabalho afirmava que o uso de sensores em bueiros permite a detecção precoce de elevação do nível de água e obstruções, contribuindo para a redução de riscos de alagamentos e danos à infraestrutura urbana. Os resultados observados na implementação sugerem que essa hipótese é válida, uma vez que o sistema conseguiu identificar, por meio de leituras de nível e de critérios de alerta, condições de risco em cenários simulados. A detecção antecipada é uma contribuição direta para a prevenção de enchentes, na medida em que possibilita a monitorização contínua de pontos críticos e a emissão de alertas antes que ocorram impactos mais severos.

A segunda hipótese afirmava que a integração de dispositivos IoT com comunicação de dados em tempo real viabiliza o acompanhamento contínuo das condições de drenagem, favorecendo a manutenção preventiva e a tomada de decisão. A análise dos resultados indica que essa hipótese também se confirmou. O sistema foi capaz de operar com transmissão de dados em fluxo contínuo, armazenar as leituras em base persistente e disponibilizar às equipes de manutenção informações operacionais relevantes sobre o estado dos bueiros. Esse aspecto reforça a importância da digitalização dos sistemas urbanos e mostra que o monitoramento em tempo real pode transformar a gestão de infraestrutura de uma abordagem reativa para uma abordagem preventiva.

A terceira hipótese afirmava que um sistema de monitoramento inteligente para bueiros apresenta potencial de aplicação prática em cidades com desafios recorrentes de drenagem, desde que considere aspectos de custo, confiabilidade, operação e integração com os processos de gestão municipal. Os resultados obtidos indicar que essa hipótese é plausível e viável. A arquitetura do protótipo demonstrou funcionalidade e potencial de uso em cenários reais, especialmente em áreas urbanas que necessitam de manutenção preventiva e de resposta rápida em situações de risco. No entanto, a viabilidade prática depende de fatores como robustez do hardware, estabilidade da comunicação, manutenção dos sensores e integração com processos institucionais de gestão pública.

A quarta hipótese afirmava que a adoção de uma solução tecnológica para monitoramento de drenagem urbana pode contribuir para a melhoria da eficiência operacional, a redução de intervenções corretivas e o aumento da resiliência das redes urbanas frente a eventos climáticos intensos. Essa hipótese também pode ser considerada válida, sobretudo em termos de potencial. O protótipo demonstrou que a coleta de dados em tempo real e a geração de alertas podem apoiar ações preventivas e reduzir a dependência de inspeções manuais isoladas. A contribuição para a resiliência urbana é evidente, pois o sistema oferece informações que permitem maior capacidade de resposta e antecipação diante de fenômenos climáticos extremos.

## 7.2 Interpretação dos padrões observados

Os resultados apresentaram padrões consistentes ao longo do protótipo. Em especial, o fluxo de operação do sistema se mostrou estável em relação à coleta, armazenamento e visualização das informações. Esse padrão indica que a arquitetura escolhida, baseada em camadas bem definidas, foi adequada para a proposta. A separação entre sensoriamento, processamento, comunicação e interface permitiu organização funcional e reduz a complexidade de manutenção do sistema.

Outro padrão identificado foi a relação direta entre o nível de água e a geração de alertas. Quando os valores medidos ultrapassaram os limites estabelecidos como críticos, o sistema respondeu com registros de severidade e alerta. Este comportamento confirma que a lógica de monitoramento foi implementada corretamente e que o sistema é capaz de operar em conjunto com regras de decisão para apoiar a gestão de riscos.

Também foi observado que a qualidade dos resultados depende diretamente da confiabilidade dos sensores e da precisão das leituras. Pequenas variações no ambiente, como umidade, ruído eletrônico, instabilidade da comunicação ou presença de detritos, podem influenciar a leitura e gerar registros inconsistentes. Assim, a análise dos dados revela que a solução precisa ser aprimorada em relação à robustez operacional para ambientes reais, mais sujeitos a interferências do que um ambiente controlado de laboratório.

## 7.3 Comparação com a literatura

Os resultados obtidos estão em consonância com a literatura sobre drenagem urbana e monitoramento em IoT. Diversos autores e estudos apontam que a infraestrutura urbana tradicional frequentemente se baseia em manutenção reativa, o que torna o sistema vulnerável a enchentes e danos estruturais. A literatura também destaca que o uso de sensores e plataformas digitais permite o monitoramento contínuo e a antecipação de eventos críticos, conforme observado neste trabalho.

A convergência entre os resultados e os referenciais teóricos reforça a relevância do tema e a adequação da solução tecnológica proposta. A necessidade de sistemas de alerta em tempo real para bueiros e redes de drenagem é amplamente reconhecida, especialmente em contextos urbanos com aumento das precipitações extremas e maior pressão sobre a infraestrutura existente. Dessa forma, o protótipo não apenas responde a uma demanda técnica, mas também se alinha às tendências do uso de tecnologias digitais para cidades mais inteligentes e resilientes.

No entanto, a literatura também indica que a efetividade real de sistemas de monitoramento depende de fatores como integração com órgãos públicos, manutenção preventiva, interoperabilidade e escalabilidade. Portanto, os resultados do protótipo são promissores, mas não devem ser interpretados como solução final pronta para adoção em larga escala sem etapas adicionais de validação em ambiente real.

## 7.4 Precisão, confiabilidade e limitações dos resultados

A análise dos resultados deve considerar a confiabilidade dos métodos e instrumentos utilizados. O protótipo foi validado em ambiente de teste e em condições controladas, o que favorece a verificação funcional das principais rotinas do sistema, mas limita a generalização dos resultados para cenários reais de operação. A confiabilidade do sistema em campo pode variar em função de fatores ambientais, como chuva intensa, obstrução do sensor, falhas de comunicação, corrosão dos componentes e instabilidade de energia.

Além disso, a pesquisa foi conduzida com escopo acadêmico e experimental, o que restringe o alcance da validação. Em termos práticos, o protótipo apresentou resultados satisfatórios para a finalidade proposta, mas ainda carece de validação em escala real, com maior número de dispositivos e condições operacionais mais próximas da realidade urbana. Esse aspecto é relevante porque o comportamento em ambiente de laboratório nem sempre reproduz inteiramente os desafios de um sistema implantado em bueiros reais.

Também é importante reconhecer que a coleta de dados em tempo real depende diretamente da infraestrutura de comunicação. Se houver falha de sinal, interrupção na rede ou configuração inadequada do hardware, a qualidade da informação pode ser comprometida. A análise indica que futuras versões do sistema devem incorporar mecanismos de redundância, armazenamento local temporário e robustez em ambientes externos, para aumentar a confiabilidade e a disponibilidade operacional.

## 7.5 Implicações dos resultados e impacto na área

Os resultados obtidos têm implicações importantes para a área de infraestrutura urbana e gestão de riscos. A principal contribuição do trabalho está na demonstração de que é possível transformar bueiros em pontos inteligentes de monitoramento, capazes de fornecer dados úteis para a manutenção preventiva e para a redução de riscos associados a enchentes. Essa abordagem pode impactar diretamente a gestão pública, a segurança dos cidadãos e a eficiência das intervenções realizadas em redes de drenagem.

Uma das implicações mais relevantes é a possibilidade de redução do tempo entre a identificação de um problema e a tomada de decisão. Em contextos urbanos com chuvas intensas, a resposta rápida é essencial. O sistema proposto oferece um mecanismo de suporte à decisão, permitindo que os operadores priorizem ações em locais críticos antes que se agravem as condições de risco.

Além disso, o uso de tecnologias IoT na infraestrutura urbana contribui para a modernização dos serviços públicos e para a construção de cidades mais inteligentes, sustentáveis e resilientes. Em nível institucional, a solução pode auxiliar órgãos de saneamento e gestão ambiental a planejar ações preventivas, reduzir custos com manutenção corretiva e melhorar a qualidade dos serviços prestados à população.

## 7.6 Sugestões para trabalhos futuros

A análise dos resultados sugere diversas possibilidades de continuidade e aprofundamento da pesquisa. Em primeiro lugar, recomenda-se a validação do protótipo em ambiente real, com instalação em bueiros de diferentes regiões e condições de operação. Essa etapa permitiria avaliar o desempenho dos sensores, a estabilidade da comunicação e o comportamento do sistema em cenários reais de precipitação e obstrução.

Como continuidade, sugere-se a integração do sistema com tecnologias de georreferenciamento, mapas digitais e alertas automáticos para equipes de manutenção. A combinação com dashboards mais sofisticados e com análise preditiva de dados poderia aumentar a capacidade de gestão e facilitar a priorização de intervenções em áreas de maior risco.

Também é relevante ampliar o número de variáveis monitoradas, como vazão, presença de resíduos, qualidade da água e condições climáticas. A incorporação de sensores adicionais permitiria uma visão mais completa da operação da drenagem urbana e fortaleceria os indicadores de risco. Outra sugestão importante é o desenvolvimento de mecanismos de automação e inteligência artificial para classificação dos eventos, com foco em reduzir o esforço manual na análise de dados.

Por fim, o projeto pode evoluir para uma solução de escala municipal, com múltiplos pontos monitorados e integração com sistemas de gestão pública. Esse avanço permitiria transformar o protótipo acadêmico em uma ferramenta de apoio estratégico para a prevenção de enchentes e para a gestão urbana sustentável.

## 7.7 Considerações finais

Os resultados analisados mostram que o protótipo de monitoramento de bueiros foi bem-sucedido em relação aos objetivos iniciais da pesquisa. O sistema demonstrou viabilidade técnica, funcionalidade operacional e potencial de contribuição para a gestão de riscos urbanos. As hipóteses formuladas foram, em geral, confirmadas, ainda que com ressalvas sobre escalabilidade, robustez em campo e necessidade de validação em ambiente real.

A análise indica que a solução tem valor acadêmico e aplicado, pois integra conhecimentos de engenharia de software, infraestrutura urbana, sensoriamento e Internet das Coisas. O trabalho também aponta caminhos promissores para continuidade, especialmente no desenvolvimento de sistemas mais robustos, conectados e alinhados às demandas da gestão pública moderna.

Dessa forma, a pesquisa alcançou seu objetivo de demonstrar que o uso de tecnologias inteligentes para monitoramento de bueiros é uma alternativa relevante para a prevenção de alagamentos e para a modernização da infraestrutura urbana.

Palavras-chave: análise dos resultados; monitoramento de bueiros; IoT; drenagem urbana; hipóteses; validação; impactos urbanos.
