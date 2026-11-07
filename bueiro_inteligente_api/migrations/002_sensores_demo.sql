-- Opcional: cria três sensores fictícios para a demonstração do simulador.
-- Pode ser executada novamente sem duplicar os sensores já criados.

INSERT INTO sensor (tipo_sensor, status_sensor, latitude, longitude)
SELECT 'Ultrassonico - Demo 2', 'Ativo', -23.5580000, -46.6430000
WHERE NOT EXISTS (
    SELECT 1 FROM sensor WHERE tipo_sensor = 'Ultrassonico - Demo 2'
);

INSERT INTO sensor (tipo_sensor, status_sensor, latitude, longitude)
SELECT 'Ultrassonico - Demo 3', 'Ativo', -23.5420000, -46.6200000
WHERE NOT EXISTS (
    SELECT 1 FROM sensor WHERE tipo_sensor = 'Ultrassonico - Demo 3'
);

INSERT INTO sensor (tipo_sensor, status_sensor, latitude, longitude)
SELECT 'Ultrassonico - Demo 4', 'Ativo', -23.5650000, -46.6540000
WHERE NOT EXISTS (
    SELECT 1 FROM sensor WHERE tipo_sensor = 'Ultrassonico - Demo 4'
);
