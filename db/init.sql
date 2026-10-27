CREATE TYPE rol_usuario AS ENUM ('cliente', 'repartidor', 'admin');
CREATE TYPE estado_envio AS ENUM ('pendiente', 'asignado', 'en_transito', 'entregado', 'incidencia');

CREATE TABLE usuarios (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    nombre VARCHAR(100) NOT NULL,
    email VARCHAR(150) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    rol rol_usuario NOT NULL,
    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE paquetes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    cliente_id UUID REFERENCES usuarios(id) ON DELETE CASCADE,
    descripcion TEXT NOT NULL,
    peso_kg DECIMAL(5,2) NOT NULL,
    direccion_origen VARCHAR(255) NOT NULL,
    direccion_destino VARCHAR(255) NOT NULL,
    fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE envios (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    paquete_id UUID REFERENCES paquetes(id) ON DELETE CASCADE,
    repartidor_id UUID REFERENCES usuarios(id) ON DELETE SET NULL,
    estado estado_envio DEFAULT 'pendiente',
    codigo_rastreo VARCHAR(50) UNIQUE NOT NULL,
    fecha_estimada TIMESTAMP,
    fecha_actualizacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE trazabilidad (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    envio_id UUID REFERENCES envios(id) ON DELETE CASCADE,
    estado_nuevo estado_envio NOT NULL,
    ubicacion_actual VARCHAR(255),
    notas TEXT,
    fecha_evento TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);