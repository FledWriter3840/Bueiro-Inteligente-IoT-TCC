from app.database import SessionLocal
from app import models

db = SessionLocal()

# Sensor
sensor = models.Sensor(tipo_sensor="Ultrassonico", status_sensor="ativo")
db.add(sensor)
db.commit()
db.refresh(sensor)

# Camera
camera = models.Camera(status_camera="ativa", resolucao="1920x1080")
db.add(camera)
db.commit()
db.refresh(camera)

# Usuario (e-mail diferente do primeiro seed)
usuario = models.Usuario(
    nome="Leonardo",
    email="leonardo@exemplo.com",
    senha="senha_hash_exemplo2",
    perfil="operador"
)
db.add(usuario)
db.commit()
db.refresh(usuario)

# LeituraSensor (valor alto, simulando nível crítico de água/detritos)
leitura = models.LeituraSensor(
    valor_leitura=2.1,
    unidade_medida="cm",
    id_sensor=sensor.id_sensor
)
db.add(leitura)
db.commit()
db.refresh(leitura)

# Alerta (crítico, ligado à leitura acima)
alerta = models.Alerta(
    descricao="Risco iminente de obstrução detectado",
    nivel_criticidade="critico",
    id_leitura=leitura.id_leitura
)
db.add(alerta)

# Limpeza (em andamento, diferente do "concluida" do primeiro seed)
limpeza = models.Limpeza(status_limpeza="em_andamento")
db.add(limpeza)

# Compactacao
compactacao = models.Compactacao(nivel_residuo=91.7)
db.add(compactacao)

# HistoricoSistema
historico = models.HistoricoSistema(
    descricao_evento="Alerta crítico gerado e limpeza automática acionada",
    id_usuario=usuario.id_usuario
)
db.add(historico)

db.commit()
db.close()

print("Seed 2 concluído com sucesso!")