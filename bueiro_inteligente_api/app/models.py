from datetime import datetime

from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, func
from .database import Base

class Sensor(Base):
    __tablename__ = "Sensor"

    id_sensor = Column(Integer, primary_key=True, index=True)
    tipo_sensor = Column(String(50))
    status_sensor = Column(String(20))

class LeituraSensor(Base):
    __tablename__ = "LeituraSensor"

    id_leitura = Column(Integer, primary_key=True, index=True)
    id_sensor = Column(Integer, ForeignKey("Sensor.id_sensor"))
    valor_leitura = Column(Float)
    data_hora = Column(DateTime,default=datetime.utcnow ,server_default=func.now())
    unidade_medida = Column(String(20), nullable=False)


class Camera(Base):
    __tablename__ = "Camera"

    id_camera = Column(Integer, primary_key=True, index=True)
    status_camera = Column(String(20), nullable=False)
    resolucao = Column(String(50))

class RegistroImagem(Base):
    __tablename__ = "RegistroImagem"

    id_imagem = Column(Integer, primary_key=True, index=True)
    caminho_imagem = Column(String(255), nullable=False)
    tipo_residuo = Column(String(50))
    confianca_ia = Column(Float)
    status_analise = Column(String(30))
    data_hora = Column(DateTime,default=datetime.utcnow, server_default=func.now())
    id_camera = Column(Integer, ForeignKey("Camera.id_camera"), nullable=False)


class Usuario(Base):
    __tablename__ = "Usuario"

    id_usuario = Column(Integer, primary_key=True, index=True)
    nome = Column(String(100), nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    senha = Column(String(255), nullable=False)
    perfil = Column(String(30), nullable=False)

class Compactacao(Base):
    __tablename__ = "Compactacao"

    id_compactacao = Column(Integer, primary_key=True, index=True)
    data_hora = Column(DateTime,default=datetime.utcnow, server_default=func.now())
    nivel_residuo = Column(Float, nullable=False)

class Alerta(Base):
    __tablename__ = "Alerta"

    id_alerta = Column(Integer, primary_key=True, index=True)
    descricao = Column(String(255), nullable=False)
    nivel_criticidade = Column(String(20), nullable=False)
    data_hora = Column(DateTime,default=datetime.utcnow, server_default=func.now())
    id_leitura = Column(Integer, ForeignKey("LeituraSensor.id_leitura"), nullable=False)

class PrevisaoEntupimento(Base):
    __tablename__ = "PrevisaoEntupimento"

    id_previsao = Column(Integer, primary_key=True, index=True)
    data_hora = Column(DateTime,default=datetime.utcnow, server_default=func.now())
    probabilidade = Column(Float, nullable=False)
    nivel_risco = Column(String(20), nullable=False)
    id_leitura = Column(Integer, ForeignKey("LeituraSensor.id_leitura"), nullable=False)

class Limpeza(Base):
    __tablename__ = "Limpeza"

    id_limpeza = Column(Integer, primary_key=True, index=True)
    data_hora = Column(DateTime,default=datetime.utcnow, server_default=func.now())
    status_limpeza = Column(String(20), nullable=False)

class HistoricoSistema(Base):
    __tablename__ = "HistoricoSistema"

    id_historico = Column(Integer, primary_key=True, index=True)
    data_hora = Column(DateTime,default=datetime.utcnow, server_default=func.now())
    descricao_evento = Column(String(255), nullable=False)
    id_usuario = Column(Integer, ForeignKey("Usuario.id_usuario"))

