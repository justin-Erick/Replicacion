----------------------------
-- 1. Eliminar tablas existentes
----------------------------
DROP TABLE IF EXISTS DatosHora CASCADE;
DROP TABLE IF EXISTS DatosDiarios CASCADE;
DROP TABLE IF EXISTS Metrica CASCADE;
DROP TABLE IF EXISTS Entidad CASCADE;
DROP TYPE IF EXISTS entidad_tipo CASCADE;
DROP TYPE IF EXISTS categoria_metrica CASCADE;
DROP TYPE IF EXISTS frecuencia_tipo CASCADE;

----------------------------
-- 2. Tipos personalizados (ampliados)
----------------------------
CREATE TYPE entidad_tipo AS ENUM (
    'Sistema', 'Agente', 'Recurso', 'CIIU', 'Embalse', 'Rio', 
    'Area', 'Subarea', 'MercadoComercializacion', 'RecursoComb', 'Enlace', 'Combustible'
);

CREATE TYPE categoria_metrica AS ENUM (
    'Demanda', 'Generación', 'Precios', 'Pérdidas', 'Sostenibilidad', 
    'Transacciones', 'Disponibilidad', 'Emisiones', 'Hidrología', 'Mercado'
);

CREATE TYPE frecuencia_tipo AS ENUM ('Hourly', 'Daily', 'Monthly', 'Lists');

----------------------------
-- 3. Tablas principales (optimizadas)
----------------------------
CREATE TABLE Entidad (
    EntidadID SERIAL PRIMARY KEY,
    Codigo VARCHAR(200) NOT NULL,
    Nombre VARCHAR(300),
    Tipo entidad_tipo NOT NULL,
    Filtro VARCHAR(150) DEFAULT 'No aplica',
    UNIQUE (Codigo, Tipo)
);

CREATE TABLE Metrica (
    MetricaID SERIAL PRIMARY KEY,
    MetricKey VARCHAR(100) NOT NULL,
    Nombre VARCHAR(300) NOT NULL,
    Categoria categoria_metrica NOT NULL,
    Unidad VARCHAR(50) NOT NULL,
    Url VARCHAR(300) NOT NULL,
    Filtro VARCHAR(150),
    Descripcion TEXT,
    Frecuencia frecuencia_tipo NOT NULL,
    EntidadTipo entidad_tipo NOT NULL,
    UNIQUE (MetricKey, EntidadTipo)
);

CREATE TABLE DatosHora (
    DatoID BIGSERIAL,
    MetricaID INT NOT NULL,
    EntidadID INT NOT NULL,
    Fecha TIMESTAMP NOT NULL,
    Valores JSONB NOT NULL,
    PRIMARY KEY (DatoID, Fecha),
    FOREIGN KEY (MetricaID) REFERENCES Metrica(MetricaID),
    FOREIGN KEY (EntidadID) REFERENCES Entidad(EntidadID)
) PARTITION BY RANGE (Fecha);

CREATE TABLE DatosDiarios (
    DatoID BIGSERIAL,
    MetricaID INT NOT NULL,
    EntidadID INT NOT NULL,
    Fecha DATE NOT NULL,
    Valores JSONB NOT NULL,
    PRIMARY KEY (DatoID, Fecha),
    FOREIGN KEY (MetricaID) REFERENCES Metrica(MetricaID),
    FOREIGN KEY (EntidadID) REFERENCES Entidad(EntidadID)
) PARTITION BY RANGE (Fecha);

----------------------------
-- 4. Crear particiones (incluidas particiones para datos futuros)
----------------------------
-- Particiones para DatosHora
CREATE TABLE datoshora_2020 PARTITION OF DatosHora FOR VALUES FROM ('2020-01-01') TO ('2021-01-01');
CREATE TABLE datoshora_2021 PARTITION OF DatosHora FOR VALUES FROM ('2021-01-01') TO ('2022-01-01');
CREATE TABLE datoshora_2022 PARTITION OF DatosHora FOR VALUES FROM ('2022-01-01') TO ('2023-01-01');
CREATE TABLE datoshora_2023 PARTITION OF DatosHora FOR VALUES FROM ('2023-01-01') TO ('2024-01-01');
CREATE TABLE datoshora_2024 PARTITION OF DatosHora FOR VALUES FROM ('2024-01-01') TO ('2025-01-01');
CREATE TABLE datoshora_2025 PARTITION OF DatosHora FOR VALUES FROM ('2025-01-01') TO ('2026-01-01');
CREATE TABLE datoshora_futuro PARTITION OF DatosHora FOR VALUES FROM ('2026-01-01') TO (MAXVALUE);

-- Particiones para DatosDiarios
CREATE TABLE datosdiarios_2020 PARTITION OF DatosDiarios FOR VALUES FROM ('2020-01-01') TO ('2021-01-01');
CREATE TABLE datosdiarios_2021 PARTITION OF DatosDiarios FOR VALUES FROM ('2021-01-01') TO ('2022-01-01');
CREATE TABLE datosdiarios_2022 PARTITION OF DatosDiarios FOR VALUES FROM ('2022-01-01') TO ('2023-01-01');
CREATE TABLE datosdiarios_2023 PARTITION OF DatosDiarios FOR VALUES FROM ('2023-01-01') TO ('2024-01-01');
CREATE TABLE datosdiarios_2024 PARTITION OF DatosDiarios FOR VALUES FROM ('2024-01-01') TO ('2025-01-01');
CREATE TABLE datosdiarios_2025 PARTITION OF DatosDiarios FOR VALUES FROM ('2025-01-01') TO ('2026-01-01');
CREATE TABLE datosdiarios_futuro PARTITION OF DatosDiarios FOR VALUES FROM ('2026-01-01') TO (MAXVALUE);

----------------------------
-- 7. Optimización
----------------------------
CREATE INDEX idx_datos_hora ON DatosHora USING BRIN (Fecha);
CREATE INDEX idx_datos_diarios ON DatosDiarios USING BRIN (Fecha);
VACUUM ANALYZE;