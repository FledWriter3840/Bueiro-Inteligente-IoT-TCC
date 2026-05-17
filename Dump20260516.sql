-- MySQL dump 10.13  Distrib 8.0.38, for Win64 (x86_64)
--
-- Host: localhost    Database: bueiro_inteligente
-- ------------------------------------------------------
-- Server version	8.0.39

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!50503 SET NAMES utf8 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Table structure for table `alerta`
--

DROP TABLE IF EXISTS `alerta`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `alerta` (
  `id_alerta` int NOT NULL AUTO_INCREMENT,
  `descricao` varchar(255) NOT NULL,
  `nivel_criticidade` varchar(20) NOT NULL,
  `data_hora` datetime DEFAULT CURRENT_TIMESTAMP,
  `id_leitura` int NOT NULL,
  PRIMARY KEY (`id_alerta`),
  KEY `fk_alerta_leitura` (`id_leitura`),
  CONSTRAINT `fk_alerta_leitura` FOREIGN KEY (`id_leitura`) REFERENCES `leiturasensor` (`id_leitura`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `alerta`
--

LOCK TABLES `alerta` WRITE;
/*!40000 ALTER TABLE `alerta` DISABLE KEYS */;
/*!40000 ALTER TABLE `alerta` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `camera`
--

DROP TABLE IF EXISTS `camera`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `camera` (
  `id_camera` int NOT NULL AUTO_INCREMENT,
  `status_camera` varchar(20) NOT NULL,
  `resolucao` varchar(50) DEFAULT NULL,
  PRIMARY KEY (`id_camera`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `camera`
--

LOCK TABLES `camera` WRITE;
/*!40000 ALTER TABLE `camera` DISABLE KEYS */;
/*!40000 ALTER TABLE `camera` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `compactacao`
--

DROP TABLE IF EXISTS `compactacao`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `compactacao` (
  `id_compactacao` int NOT NULL AUTO_INCREMENT,
  `nivel_residuo` float NOT NULL,
  `data_hora` datetime DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id_compactacao`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `compactacao`
--

LOCK TABLES `compactacao` WRITE;
/*!40000 ALTER TABLE `compactacao` DISABLE KEYS */;
/*!40000 ALTER TABLE `compactacao` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `historicosistema`
--

DROP TABLE IF EXISTS `historicosistema`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `historicosistema` (
  `id_historico` int NOT NULL AUTO_INCREMENT,
  `descricao_evento` varchar(255) NOT NULL,
  `data_hora` datetime DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id_historico`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `historicosistema`
--

LOCK TABLES `historicosistema` WRITE;
/*!40000 ALTER TABLE `historicosistema` DISABLE KEYS */;
/*!40000 ALTER TABLE `historicosistema` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `leiturasensor`
--

DROP TABLE IF EXISTS `leiturasensor`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `leiturasensor` (
  `id_leitura` int NOT NULL AUTO_INCREMENT,
  `valor_leitura` float NOT NULL,
  `data_hora` datetime DEFAULT CURRENT_TIMESTAMP,
  `id_sensor` int NOT NULL,
  PRIMARY KEY (`id_leitura`),
  KEY `fk_sensor_leitura` (`id_sensor`),
  CONSTRAINT `fk_sensor_leitura` FOREIGN KEY (`id_sensor`) REFERENCES `sensor` (`id_sensor`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `leiturasensor`
--

LOCK TABLES `leiturasensor` WRITE;
/*!40000 ALTER TABLE `leiturasensor` DISABLE KEYS */;
/*!40000 ALTER TABLE `leiturasensor` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `limpeza`
--

DROP TABLE IF EXISTS `limpeza`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `limpeza` (
  `id_limpeza` int NOT NULL AUTO_INCREMENT,
  `data_hora` datetime DEFAULT CURRENT_TIMESTAMP,
  `status_limpeza` varchar(20) NOT NULL,
  PRIMARY KEY (`id_limpeza`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `limpeza`
--

LOCK TABLES `limpeza` WRITE;
/*!40000 ALTER TABLE `limpeza` DISABLE KEYS */;
/*!40000 ALTER TABLE `limpeza` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `registroimagem`
--

DROP TABLE IF EXISTS `registroimagem`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `registroimagem` (
  `id_imagem` int NOT NULL AUTO_INCREMENT,
  `caminho_imagem` varchar(255) NOT NULL,
  `data_hora` datetime DEFAULT CURRENT_TIMESTAMP,
  `id_camera` int NOT NULL,
  PRIMARY KEY (`id_imagem`),
  KEY `fk_camera_imagem` (`id_camera`),
  CONSTRAINT `fk_camera_imagem` FOREIGN KEY (`id_camera`) REFERENCES `camera` (`id_camera`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `registroimagem`
--

LOCK TABLES `registroimagem` WRITE;
/*!40000 ALTER TABLE `registroimagem` DISABLE KEYS */;
/*!40000 ALTER TABLE `registroimagem` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `sensor`
--

DROP TABLE IF EXISTS `sensor`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `sensor` (
  `id_sensor` int NOT NULL AUTO_INCREMENT,
  `tipo_sensor` varchar(50) NOT NULL,
  `status_sensor` varchar(20) NOT NULL,
  PRIMARY KEY (`id_sensor`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `sensor`
--

LOCK TABLES `sensor` WRITE;
/*!40000 ALTER TABLE `sensor` DISABLE KEYS */;
/*!40000 ALTER TABLE `sensor` ENABLE KEYS */;
UNLOCK TABLES;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2026-05-16 20:37:47
