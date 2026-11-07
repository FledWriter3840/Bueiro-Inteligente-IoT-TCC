# Roteiro de demonstração em quatro passos

## Preparação

- Configure e inicie MySQL e a API conforme o README da raiz.
- Execute `001_app_mobile.sql` uma vez e, para obter três sensores, também
  `002_sensores_demo.sql`.
- Inicie o simulador com um intervalo de cinco segundos. No celular, configure
  `EXPO_PUBLIC_API_URL` com o IPv4 do computador e abra o app no Expo Go.
- Permita notificações locais e deixe o app aberto na tela Mapa. Inicie a
  demonstração com os sensores em status não crítico para que uma transição
  posterior seja detectada.

## Demonstração

1. **Leitura:** mostre no terminal o simulador enviando leituras para
   `POST /sensores/leitura`; a mesma entrada pode ser inspecionada no Swagger.
2. **Mudança de status:** aguarde o nível simulado passar de 80%. O status do
   bueiro muda para `critico` e aparece em vermelho no mapa, atualizado pelo
   polling de dez segundos.
3. **Alerta no celular:** na primeira transição de não crítico para crítico, o
   aparelho recebe uma notificação local. O sistema evita repetir o alerta
   enquanto o mesmo bueiro permanecer crítico.
4. **Denúncia no mapa:** abra **Denunciar**, obtenha a localização, escolha
   gravidade e descrição e envie. A nova ocorrência aparece como marcador azul
   no mapa após a próxima consulta. Se a API estiver indisponível, a tela
   informa que a denúncia ficou na fila local e tenta reenviá-la quando a API
   voltar.

## Critério de conclusão

A demonstração está concluída quando uma leitura altera o nível/status
observado, o app notifica a transição para crítico e uma denúncia com localização
é persistida pela API e exibida no mapa.
