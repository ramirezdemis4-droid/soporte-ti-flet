CREATE DATABASE IF NOT EXISTS soporte_ti CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE soporte_ti;

CREATE TABLE IF NOT EXISTS usuarios (
  id INT AUTO_INCREMENT PRIMARY KEY,
  nombre VARCHAR(100) NOT NULL,
  correo VARCHAR(150) NOT NULL UNIQUE,
  activo BOOLEAN NOT NULL DEFAULT TRUE,
  creado_en DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

-- Relación 1:1: el ID del perfil es también FK única a usuarios.
CREATE TABLE IF NOT EXISTS perfiles_usuario (
  usuario_id INT PRIMARY KEY,
  departamento VARCHAR(100) NOT NULL,
  telefono VARCHAR(30),
  CONSTRAINT fk_perfil_usuario FOREIGN KEY (usuario_id)
    REFERENCES usuarios(id) ON DELETE CASCADE
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS tecnicos (
  id INT AUTO_INCREMENT PRIMARY KEY,
  nombre VARCHAR(100) NOT NULL,
  correo VARCHAR(150) NOT NULL UNIQUE,
  activo BOOLEAN NOT NULL DEFAULT TRUE
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS especialidades (
  id INT AUTO_INCREMENT PRIMARY KEY,
  nombre VARCHAR(80) NOT NULL UNIQUE
) ENGINE=InnoDB;

-- Tabla intermedia: relación N:M entre técnicos y especialidades.
CREATE TABLE IF NOT EXISTS tecnico_especialidad (
  tecnico_id INT NOT NULL,
  especialidad_id INT NOT NULL,
  PRIMARY KEY (tecnico_id, especialidad_id),
  CONSTRAINT fk_te_tecnico FOREIGN KEY (tecnico_id)
    REFERENCES tecnicos(id) ON DELETE CASCADE,
  CONSTRAINT fk_te_especialidad FOREIGN KEY (especialidad_id)
    REFERENCES especialidades(id) ON DELETE CASCADE
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS tickets (
  id INT AUTO_INCREMENT PRIMARY KEY,
  titulo VARCHAR(150) NOT NULL,
  descripcion TEXT NOT NULL,
  usuario_id INT NOT NULL,
  tecnico_id INT NULL,
  especialidad_id INT NOT NULL,
  prioridad ENUM('Baja','Media','Alta') NOT NULL DEFAULT 'Media',
  estado ENUM('Pendiente','En proceso','Resuelto','Cerrado') NOT NULL DEFAULT 'Pendiente',
  creado_en DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  actualizado_en DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  CONSTRAINT fk_ticket_usuario FOREIGN KEY (usuario_id)
    REFERENCES usuarios(id) ON DELETE RESTRICT,
  CONSTRAINT fk_ticket_tecnico FOREIGN KEY (tecnico_id)
    REFERENCES tecnicos(id) ON DELETE RESTRICT,
  CONSTRAINT fk_ticket_especialidad FOREIGN KEY (especialidad_id)
    REFERENCES especialidades(id) ON DELETE RESTRICT,
  CONSTRAINT ck_titulo_no_vacio CHECK (CHAR_LENGTH(TRIM(titulo)) > 0),
  CONSTRAINT ck_estado_con_asignacion CHECK (estado = 'Pendiente' OR tecnico_id IS NOT NULL)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS historial_tickets (
  id INT AUTO_INCREMENT PRIMARY KEY,
  ticket_id INT NOT NULL,
  estado_anterior VARCHAR(20) NOT NULL,
  estado_nuevo VARCHAR(20) NOT NULL,
  cambiado_en DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT fk_historial_ticket FOREIGN KEY (ticket_id)
    REFERENCES tickets(id) ON DELETE CASCADE
) ENGINE=InnoDB;
