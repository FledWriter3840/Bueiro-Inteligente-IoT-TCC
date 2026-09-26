# Adições de Mapeamento, Localização e Limpeza

Este documento explica as funcionalidades acrescentadas ao painel e à API para selecionar e mapear bueiros, cadastrar novos locais, consultar solicitações do SAC e acompanhar indicadores de limpeza.

## 1. Inventário de bueiros

O arquivo `bueiro_inteligente_api/datasets_exemplo/bueiros.csv` passou a ser carregado pela API. Ele contém registros de bueiros rodoviários com regional, rodovia, quilômetro, tipo e coordenadas de montante e jusante.

O carregador:

- aceita arquivos em UTF-8 ou Windows-1252;
- converte números com vírgula decimal;
- ignora linhas sem coordenadas ou quilometragem válidas;
- rejeita latitude fora de `-90..90` e longitude fora de `-180..180`;
- permite que extensão e dimensão estejam ausentes, pois esses campos não impedem o mapeamento.

No seletor **Local predefinido** da barra **Localização do Bueiro**, escolha **Inventário rodoviário (bueiros.csv)**. Em seguida, selecione a rodovia, o registro por quilômetro e o ponto (**Montante** ou **Jusante**). A latitude e a longitude selecionadas são usadas pelas consultas geográficas existentes, incluindo clima, topografia e busca dos chamados SAC.

A aba **Mapa de Bueiros** mostra os pontos de montante e jusante da rodovia escolhida em um mapa OpenStreetMap. A legenda distingue montante de jusante e destaca o registro selecionado. Ao passar o cursor sobre um marcador, aparecem informações do bueiro.

> O arquivo de origem representa principalmente bueiros de rodovias; não deve ser interpretado como um cadastro municipal completo de bocas de lobo urbanas. Registros sem coordenadas geográficas utilizáveis não são apresentados.

## 2. Cadastro de um novo bueiro

Na barra lateral **Localização do Bueiro**, expanda **Adicionar novo bueiro**. O formulário solicita:

- regional;
- elemento (por exemplo, bueiro ou boca de lobo);
- rodovia ou logradouro;
- quilômetro ou outra referência;
- data do levantamento;
- tipo ou material;
- extensão e dimensão, quando conhecidas;
- latitude e longitude de montante;
- latitude e longitude de jusante.

As coordenadas começam preenchidas com a localização atualmente selecionada, mas podem ser ajustadas antes do envio. Regional, elemento, rodovia/logradouro, data do levantamento, referência quilométrica e tipo/material, além das quatro coordenadas, são obrigatórios. Extensão e dimensão são opcionais; se permanecerem em zero no formulário, são enviadas como ausentes.

Ao salvar, a API valida os valores e cria um identificador com o prefixo `NOVO-`. Os registros manuais são gravados em `bueiro_inteligente_api/datasets_exemplo/bueiros_adicionados.json`, separados do CSV recebido, para preservar a fonte original. Depois do cadastro, a rodovia e o bueiro passam a integrar as opções de seleção e o mapa.

### Exemplo de chamada da API

`POST /bueiros/` cria um registro e responde com status HTTP `201`:

```json
{
  "regional": "Cadastro manual",
  "elemento": "Boca de lobo",
  "rodovia": "Rua Exemplo",
  "levantamento": "2026-09-26",
  "km": 12.5,
  "extensao_m": null,
  "dimensao_m": null,
  "tipo": "Boca de lobo de concreto",
  "latitude_montante": -23.55,
  "longitude_montante": -46.63,
  "latitude_jusante": -23.5501,
  "longitude_jusante": -46.6301
}
```

Latitude e longitude são validadas pelo modelo da API. Valores inválidos ou campos obrigatórios ausentes são rejeitados com HTTP `422`.

## 3. Endpoints do inventário

| Método e rota | Finalidade |
|---|---|
| `GET /bueiros/rodovias` | Lista as rodovias que aparecem no CSV ou nos cadastros manuais. |
| `GET /bueiros/` | Lista todos os bueiros do inventário combinado. |
| `GET /bueiros/?rodovia=SP%20081` | Filtra bueiros pela rodovia informada. |
| `POST /bueiros/` | Valida e persiste um novo bueiro. |
| `GET /bueiros/solicitacoes-limpeza?lat=-23.55&lon=-46.63&raio_m=500` | Busca chamados SAC próximos da localização. |

Os parâmetros `lat` e `lon` do endpoint SAC são obrigatórios. `raio_m` aceita de 100 a 5.000 metros; por padrão, usa 500 metros. O parâmetro opcional `limite` controla o máximo de solicitações retornadas, entre 1 e 5.000.

## 4. Integração com o CSV do SAC

O arquivo `bueiro_inteligente_api/datasets_exemplo/sac_limpeza_bueiro.csv` contém solicitações de serviço com endereço, datas, situação e geometria `POINT`. Os pontos estão em coordenadas projetadas UTM SIRGAS 2000 / zona 23S, identificada como EPSG:31983. A API converte a geometria para latitude/longitude WGS84 (EPSG:4326) com a dependência `pyproj` antes de calcular distâncias.

Na aba **Mapa de Bueiros**, a seção **Solicitações SAC de limpeza próximas** centraliza a consulta nas coordenadas ativas. É possível ajustar o raio e ver:

- número de solicitações encontradas;
- número encerrado como `FINALIZADA` no SAC;
- número `CANCELADA`;
- mapa dos pontos, com endereço, situação, data do parecer e distância no detalhe do marcador;
- tabela com os registros mais próximos.

O histórico fornecido pelo SAC é majoritariamente de 2020 a 2021. A situação `FINALIZADA` indica que a solicitação foi encerrada no sistema de atendimento; **não confirma, sozinha, que uma equipe executou a limpeza física naquele ponto**. Por isso, os resultados e o indicador associado são tratados como proxy de recorrência de solicitações, não como comprovante de serviço.

## 5. Indicadores de constância

O painel mostra dois indicadores distintos. Eles usam fontes, áreas e interpretações diferentes.

### Índice global dos registros do sistema

Na **Visão Geral**, o **Índice de constância de limpeza** usa os registros da rota `GET /limpeza/`, dentro de uma janela dos últimos 180 dias. São necessários ao menos três registros para calcular dois ou mais intervalos. O indicador é global porque o modelo atual de limpeza não vincula cada registro a um bueiro específico.

Seja $d_i$ o intervalo, em dias, entre registros consecutivos. A fórmula usada é:

$$
CV = \frac{s_d}{\bar{d}}, \qquad IC = \frac{100}{1 + CV}
$$

em que $s_d$ é o desvio-padrão amostral dos intervalos e $\bar{d}$ é a média desses intervalos. Quanto mais regulares os intervalos, maior o índice. O coeficiente de variação é definido como desvio-padrão dividido pela média; referência: [NIST Dataplot — Coefficient of Variation](https://www.itl.nist.gov/div898/software/dataplot/refman2/auxillar/coefvari.htm).

Esse IC é uma métrica operacional derivada para o projeto, não uma norma de manutenção nem uma medida da eficácia da limpeza.

### Regularidade histórica dos chamados SAC

Na aba **Mapa de Bueiros**, o indicador **Regularidade histórica dos chamados SAC** é local: considera as datas dos pareceres de solicitações `FINALIZADA` que estejam dentro do raio consultado. Usa a mesma transformação de coeficiente de variação e a mesma fórmula `100 / (1 + CV)`, mas não é o índice global da Visão Geral.

São necessárias pelo menos três datas distintas de parecer finalizado para calcular o indicador. A API também retorna intervalo médio, período coberto, total de solicitações e lista dos registros dentro do raio. Se não houver amostra suficiente, a interface informa que o índice está indisponível.

## 6. Cores do gráfico de IA e previsão

O gráfico **IA / Previsão — risco e necessidade de limpeza**, na Visão Geral, representa a probabilidade de entupimento em uma escala de 0% a 100%. A cor considera tanto o nível de risco quanto a urgência de limpeza:

| Condição predominante | Cor |
|---|---|
| Baixo / rotina | Verde |
| Alto ou preventiva | Laranja |
| Crítico, urgente ou emergência | Vermelho |
| Médio | Amarelo |

O detalhe ao passar o cursor mostra risco, urgência de limpeza e probabilidade. Na comparação dos motores de IA, o gráfico de probabilidades por classe usa a mesma escala semântica: verde para baixo, amarelo para médio, laranja para alto e vermelho para crítico.

## 7. Arquivos envolvidos

- `bueiro_inteligente_api/app/routers/bueiros.py`: leitura do inventário, cadastro, endpoints e consulta espacial do SAC.
- `bueiro_inteligente_api/app/main.py`: inclusão do router de bueiros na aplicação FastAPI.
- `bueiro_inteligente_api/dashboard.py`: seletores, formulário de cadastro, mapa, gráficos e indicadores.
- `bueiro_inteligente_api/tests/test_bueiros.py`: testes do inventário, consulta SAC, limites e cadastro.
- `bueiro_inteligente_api/datasets_exemplo/bueiros.csv`: inventário de origem, preservado pelo cadastro manual.
- `bueiro_inteligente_api/datasets_exemplo/bueiros_adicionados.json`: destino persistente dos cadastros feitos pelo painel/API; criado quando o primeiro bueiro é salvo.
- `bueiro_inteligente_api/datasets_exemplo/sac_limpeza_bueiro.csv`: solicitações georreferenciadas usadas como histórico SAC.
- `requirements.txt`: declaração de `pyproj`, usada para converter as geometrias UTM do SAC.
- `docs/funcionamento_bueiro_api.md`: documentação funcional geral da API e das integrações.

## 8. Testes

A suíte focada pode ser executada a partir da pasta `bueiro_inteligente_api`:

```powershell
python -m unittest discover -s tests -p test_bueiros.py -v
```

Os testes verificam a lista de rodovias, o filtro por rodovia, a busca SAC por raio, rejeição de raio inválido, criação persistente/listagem de um novo bueiro e rejeição de coordenadas inválidas. O teste de persistência usa um arquivo temporário e não grava dados de teste no inventário real.
