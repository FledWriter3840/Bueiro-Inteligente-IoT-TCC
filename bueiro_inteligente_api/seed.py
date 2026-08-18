from app.database import SessionLocal
from app import models

db = SessionLocal()

# Sensor
sensor = models.Sensor(tipo_sensor="Ultrassonico", status_sensor="ativo")
db.add(sensor)
db.commit()
db.refresh(sensor)

# Camera
camera = models.Camera(status_camera="ativa", resolucao="1280x720")
db.add(camera)
db.commit()
db.refresh(camera)

# Usuario
usuario = models.Usuario(
    nome="Matheus",
    email="matheus@exemplo.com",
    senha="senha_hash_exemplo",
    perfil="admin"
)
db.add(usuario)
db.commit()
db.refresh(usuario)

# LeituraSensor
leitura = models.LeituraSensor(
    valor_leitura=8.5,
    unidade_medida="cm",
    id_sensor=sensor.id_sensor
)
db.add(leitura)
db.commit()
db.refresh(leitura)

# Alerta
alerta = models.Alerta(
    descricao="Nível crítico detectado",
    nivel_criticidade="alto",
    id_leitura=leitura.id_leitura
)
db.add(alerta)

# Limpeza
limpeza = models.Limpeza(status_limpeza="concluida")
db.add(limpeza)

# Compactacao
compactacao = models.Compactacao(nivel_residuo=72.3)
db.add(compactacao)

# HistoricoSistema
historico = models.HistoricoSistema(
    descricao_evento="Sistema iniciado e primeira leitura registrada",
    id_usuario=usuario.id_usuario
)
db.add(historico)

db.commit()
db.close()

print("Seed concluído com sucesso!")