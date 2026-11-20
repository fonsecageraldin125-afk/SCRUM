CREATE DATABASE IF NOT EXISTS cecytem
CHARACTER SET utf8mb4
COLLATE utf8mb4_unicode_ci;

USE cecytem;

CREATE TABLE IF NOT EXISTS usuarios (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    usuario VARCHAR(50) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    rol ENUM('docente', 'director') NOT NULL
);

CREATE TABLE IF NOT EXISTS grupos_escolares (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(30) NOT NULL UNIQUE,
    creado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS docente_grupos (
    id INT AUTO_INCREMENT PRIMARY KEY,
    docente VARCHAR(100) NOT NULL,
    grupo_id INT NOT NULL,
    UNIQUE KEY asignacion_unica (docente, grupo_id),
    FOREIGN KEY (grupo_id)
        REFERENCES grupos_escolares(id)
        ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS alumnos_escolares (
    id INT AUTO_INCREMENT PRIMARY KEY,
    grupo_id INT NOT NULL,
    numero_lista INT NOT NULL,
    nombre VARCHAR(150) NOT NULL,
    activo BOOLEAN DEFAULT TRUE,
    UNIQUE KEY alumno_lista (grupo_id, numero_lista),
    FOREIGN KEY (grupo_id)
        REFERENCES grupos_escolares(id)
        ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS asistencias_escolares (
    id INT AUTO_INCREMENT PRIMARY KEY,
    alumno_id INT NOT NULL,
    grupo_id INT NOT NULL,
    fecha DATE NOT NULL,
    estado VARCHAR(30) NOT NULL,
    docente VARCHAR(100) NOT NULL,
    observaciones TEXT,
    creado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY asistencia_diaria (alumno_id, fecha),
    FOREIGN KEY (alumno_id)
        REFERENCES alumnos_escolares(id),
    FOREIGN KEY (grupo_id)
        REFERENCES grupos_escolares(id)
);

CREATE TABLE IF NOT EXISTS registros_escolares (
    id INT AUTO_INCREMENT PRIMARY KEY,
    tipo VARCHAR(50) NOT NULL,
    alumno VARCHAR(150) NOT NULL,
    grupo VARCHAR(50),
    fecha DATE NOT NULL,
    hora TIME NULL,
    detalle TEXT,
    accion VARCHAR(150),
    evidencia VARCHAR(500),
    seguimiento BOOLEAN DEFAULT FALSE,
    estado VARCHAR(40) DEFAULT 'Pendiente',
    registrado_por VARCHAR(100) NOT NULL,
    creado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS decisiones_directivas (
    id INT AUTO_INCREMENT PRIMARY KEY,
    registro_id INT NULL,
    alumno VARCHAR(150) NOT NULL,
    accion VARCHAR(100) NOT NULL,
    justificacion TEXT,
    estado VARCHAR(40) DEFAULT 'Pendiente',
    director VARCHAR(100) NOT NULL,
    creado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS cartas_compromiso (
    id INT AUTO_INCREMENT PRIMARY KEY,
    alumno VARCHAR(150) NOT NULL,
    tutor VARCHAR(150),
    motivo TEXT,
    compromisos TEXT,
    fecha DATE,
    director VARCHAR(100) NOT NULL,
    creado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

INSERT IGNORE INTO grupos_escolares (nombre) VALUES
('1A'), ('1B'), ('1C'),
('2A'), ('2B'), ('2C'),
('3A'), ('3B'), ('3C');