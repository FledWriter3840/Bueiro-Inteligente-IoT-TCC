# Adições recentes ao painel e à API

Este documento registra as alterações mais recentes no painel Streamlit e na API FastAPI: seleção de locais provenientes do SAC, cores das séries temporais e tempo de espera para consultas geográficas e de previsão.

## 1. Locais do SAC como opções de localização

O endpoint `GET /bueiros/locais-sac` disponibiliza os pontos georreferenciados do arquivo `bueiro_inteligente_api/datasets_exemplo/sac_limpeza_bueiro.csv`. As geometrias UTM são convertidas para latitude e longitude WGS84 pelo carregador do SAC. Chamados no mesmo ponto são agrupados por coordenadas arredondadas a seis casas decimais; cada local informa endereço, coordenadas e quantidade de solicitações associadas.

Na barra lateral **Localização do Bueiro**, escolha **Localização do SAC (bueiro/boca de lobo)** e selecione um endereço. As coordenadas do local passam a ser usadas pelas consultas dependentes da localização, como previsão, clima, topografia e busca de chamados próximos.

Selecionar um local não cria automaticamente um registro de bueiro. Para incluí-lo no inventário, abra **Adicionar novo bueiro** e salve o cadastro. O formulário sugere o elemento **Boca de lobo**, preenche o logradouro e usa a coordenada SAC selecionada como valor inicial para os pontos de montante e jusante. Os campos continuam editáveis antes do envio. Depois de salvar, o novo registro fica disponível no inventário junto aos demais cadastros.

> O ponto do SAC representa a localização informada em uma solicitação de serviço. Ele pode servir de referência para cadastro, mas não comprova que existe um bueiro ou uma boca de lobo exatamente naquela coordenada. Verifique o local antes de registrar o elemento no inventário.

## 2. Cores das linhas dos gráficos

As linhas do gráfico de distância medida pelo sensor e do gráfico de projeção da simulação usam laranja (`#f97316`), aproximando sua aparência de um gráfico de temperatura. A linha tem espessura reforçada para facilitar a leitura. Essa alteração não muda os valores, eixos ou cálculos dos gráficos.

As cores dos gráficos de risco permanecem semânticas: verde para baixo, amarelo para médio, laranja para alto e vermelho para crítico.

## 3. Timeout das consultas do painel

A função `get_json` do dashboard aceita um timeout por chamada. O padrão continua em 5 segundos para consultas rápidas. O painel usa limites maiores nas operações que podem consultar serviços externos sequencialmente:

| Endpoint | Timeout do dashboard | Motivo |
|---|---:|---|
| `GET /ia/previsao` | 120 s | Pode consultar clima, topografia, histórico de alagamentos e uso do solo. |
| `GET /ia/comparativo` | 120 s | Executa a análise multivariada e o modelo de Machine Learning. |
| `GET /ia/topografia-atual` | 65 s | Pode buscar a elevação do ponto central e de até quatro pontos vizinhos. |

O timeout controla quanto tempo o dashboard espera pela resposta; ele não altera o timeout interno dos serviços externos nem garante que uma API remota esteja disponível. As consultas OpenTopography e Overpass podem demorar mais que as rotas locais. Se uma chamada ainda exceder o limite configurado, a mensagem de erro continuará sendo exibida pelo painel.

## 4. Arquivos envolvidos

- `bueiro_inteligente_api/app/routers/bueiros.py`: carrega e converte os pontos SAC e implementa `GET /bueiros/locais-sac`.
- `bueiro_inteligente_api/dashboard.py`: seletor SAC, preenchimento do formulário, cores dos gráficos e timeouts por endpoint.
- `bueiro_inteligente_api/tests/test_bueiros.py`: teste de locais SAC únicos e com coordenadas válidas.
- `docs/adicoes_mapeamento_localizacao_limpeza.md`: documentação anterior do inventário, mapa e solicitações SAC próximas.

## 5. Verificações

O teste focado do roteador de bueiros passou com sete casos, incluindo a validação da lista de locais SAC. Os arquivos Python alterados também passaram pela compilação sintática. Em uma verificação do servidor local, o novo endpoint SAC e a consulta de clima com coordenadas escolhidas dessa lista responderam com HTTP `200`.