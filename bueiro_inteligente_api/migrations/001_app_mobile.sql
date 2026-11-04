-- Aplicar uma única vez no banco bueiro_inteligente antes de iniciar a API.
-- A migração é aditiva e preserva as leituras e os sensores já cadastrados.

ALTER TABLE sensor
    ADD COLUMN latitude DECIMAL(10, 7) NULL,
    ADD COLUMN longitude DECIMAL(10, 7) NULL;

-- Coordenadas fictícias próximas ao centro de São Paulo para demonstração.
UPDATE sensor
SET latitude = COALESCE(
        latitude,
        -23.5505000 + MOD(GREATEST(id_sensor - 1, 0), 20) * 0.0010000
    ),
    longitude = COALESCE(
        longitude,
        -46.6333000 + MOD(GREATEST(id_sensor - 1, 0), 20) * 0.0010000
    );

ALTER TABLE sensor
    MODIFY COLUMN latitude DECIMAL(10, 7) NOT NULL,
    MODIFY COLUMN longitude DECIMAL(10, 7) NOT NULL;

-- Timestamps repetidos enviados pelo mesmo dispositivo tornam-se idempotentes.
-- A coluna permite NULL para não exigir alteração em leituras antigas.
ALTER TABLE leiturasensor
    ADD COLUMN timestamp_dispositivo DATETIME(6) NULL;

CREATE UNIQUE INDEX uq_leiturasensor_dispositivo_timestamp
    ON leiturasensor (id_sensor, timestamp_dispositivo);

CREATE TABLE ocorrencias (
    id INT NOT NULL AUTO_INCREMENT,
    descricao TEXT NULL,
    latitude DECIMAL(10, 7) NOT NULL,
    longitude DECIMAL(10, 7) NOT NULL,
    foto_url VARCHAR(255) NULL,
    gravidade ENUM('leve', 'moderada', 'grave') NOT NULL DEFAULT 'moderada',
    status ENUM('aberta', 'em_analise', 'resolvida') NOT NULL DEFAULT 'aberta',
    criado_em TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
