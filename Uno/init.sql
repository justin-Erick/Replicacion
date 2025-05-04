----------------------------
-- 1. Eliminar tablas existentes (para reinicios)
----------------------------
DROP TABLE IF EXISTS DatosHora CASCADE;
DROP TABLE IF EXISTS DatosDiarios CASCADE;
DROP TABLE IF EXISTS DatosMensuales CASCADE;
DROP TABLE IF EXISTS Metrica CASCADE;
DROP TABLE IF EXISTS Entidad CASCADE;
DROP TYPE IF EXISTS entidad_tipo CASCADE;
DROP TYPE IF EXISTS categoria_metrica CASCADE;
DROP TYPE IF EXISTS frecuencia_tipo CASCADE;

----------------------------
-- 2. Crear tipos personalizados
----------------------------
CREATE TYPE entidad_tipo AS ENUM (
    'Sistema', 'Agente', 'Recurso', 'CIIU', 'Embalse', 'Rio', 
    'Area', 'Subarea', 'MercadoComercializacion', 'RecursoComb'
);

CREATE TYPE categoria_metrica AS ENUM (
    'Demanda', 'Generación', 'Precios', 'Pérdidas', 'Sostenibilidad', 
    'Transacciones', 'Disponibilidad', 'Emisiones', 'Hidrología'
);

CREATE TYPE frecuencia_tipo AS ENUM ('Hourly', 'Daily', 'Monthly', 'Lists');

----------------------------
-- 3. Crear tablas principales
----------------------------
CREATE TABLE Entidad (
    EntidadID SERIAL PRIMARY KEY,
    Codigo VARCHAR(100) NOT NULL,  -- Ampliado para nombres largos
    Nombre VARCHAR(200),
    Tipo entidad_tipo NOT NULL,
    Filtro VARCHAR(100) DEFAULT 'No aplica',
    UNIQUE (Codigo, Tipo)
);

CREATE TABLE Metrica (
    MetricaID SERIAL PRIMARY KEY,
    MetricKey VARCHAR(50) NOT NULL UNIQUE,
    Nombre VARCHAR(150) NOT NULL,
    Categoria categoria_metrica NOT NULL,
    Unidad VARCHAR(20) NOT NULL,
    Url VARCHAR(255) NOT NULL,
    Filtro VARCHAR(100),
    Descripcion TEXT,
    Frecuencia frecuencia_tipo NOT NULL  -- Nueva columna para frecuencia
);

CREATE TABLE DatosHora (
    DatoID BIGSERIAL,
    MetricaID INT NOT NULL,
    EntidadID INT NOT NULL,
    Fecha TIMESTAMP NOT NULL,  -- Cambiado a TIMESTAMP para precisión horaria
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
-- 4. Función para crear particiones automáticas
----------------------------
CREATE OR REPLACE FUNCTION crear_particiones_anuales()
RETURNS TRIGGER AS $$
DECLARE
    tabla_base TEXT := TG_ARGV[0];
    anio_actual INT := EXTRACT(YEAR FROM CURRENT_DATE);
BEGIN
    FOR i IN 0..3 LOOP  -- Crea particiones para los próximos 3 años
        EXECUTE format(
            'CREATE TABLE IF NOT EXISTS %s_%s PARTITION OF %s ' ||
            'FOR VALUES FROM (''%s-01-01'') TO (''%s-01-01'')',
            tabla_base, anio_actual + i, tabla_base, anio_actual + i, anio_actual + i + 1
        );
    END LOOP;
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

-- Triggers para creación automática de particiones
CREATE TRIGGER trig_particiones_datos_hora
AFTER INSERT ON DatosHora
FOR EACH STATEMENT EXECUTE FUNCTION crear_particiones_anuales('datoshora');

CREATE TRIGGER trig_particiones_datos_diarios
AFTER INSERT ON DatosDiarios
FOR EACH STATEMENT EXECUTE FUNCTION crear_particiones_anuales('datosdiarios');

----------------------------
-- 5. Función de inserción de datos mejorada
----------------------------
CREATE OR REPLACE FUNCTION insertar_datos_api(json_data JSONB)
RETURNS VOID AS $$
DECLARE
    metric_key TEXT;
    entity_type entidad_tipo;
    entity_code TEXT;
    fecha DATE;
    frecuencia frecuencia_tipo;
    filtro TEXT;
    entidad_values JSONB;
BEGIN
    -- Extraer metadatos
    metric_key := json_data->'Metric'->>'Id';
    frecuencia := (json_data->>'TipoFrecuencia')::frecuencia_tipo;
    entidad_values := json_data->'Items'->0->'Entities'->0->'Values';
    fecha := (json_data->'Items'->0->>'Date')::DATE;
    filtro := COALESCE(json_data->'Metric'->>'Filter', 'No aplica');

    -- Determinar tipo de entidad y código dinámicamente
    entity_type := (json_data->'Items'->0->'Entities'->0->>'Id')::entidad_tipo;
    
    entity_code := CASE
        WHEN entity_type = 'Embalse' THEN entidad_values->>'Nombre Embalse'
        WHEN entity_type = 'Agente' THEN entidad_values->>'Codigo Agente'
        WHEN entity_type = 'Recurso' THEN entidad_values->>'Codigo Submercado Generación'
        ELSE entidad_values->>'code'
    END;

    -- Validar existencia de métrica
    IF NOT EXISTS (SELECT 1 FROM Metrica WHERE MetricKey = metric_key) THEN
        RAISE EXCEPTION 'Métrica "%" no registrada en el sistema', metric_key;
    END IF;

    -- Insertar/actualizar entidad
    INSERT INTO Entidad (Codigo, Tipo, Filtro, Nombre)
    VALUES (entity_code, entity_type, filtro, entity_code)
    ON CONFLICT (Codigo, Tipo) 
    DO UPDATE SET Filtro = EXCLUDED.Filtro;

    -- Insertar en tabla correspondiente según frecuencia
    CASE frecuencia
        WHEN 'Hourly' THEN
            INSERT INTO DatosHora (MetricaID, EntidadID, Fecha, Valores)
            SELECT m.MetricaID, e.EntidadID, fecha, entidad_values
            FROM Metrica m
            JOIN Entidad e USING (Codigo, Tipo)
            WHERE m.MetricKey = metric_key;

        WHEN 'Daily' THEN
            INSERT INTO DatosDiarios (MetricaID, EntidadID, Fecha, Valores)
            SELECT m.MetricaID, e.EntidadID, fecha, entidad_values
            FROM Metrica m
            JOIN Entidad e USING (Codigo, Tipo)
            WHERE m.MetricKey = metric_key;

        ELSE
            RAISE NOTICE 'Frecuencia "%" no implementada', frecuencia;
    END CASE;

EXCEPTION WHEN others THEN
    RAISE NOTICE 'Error insertando datos: %', SQLERRM;
END;
$$ LANGUAGE plpgsql;

----------------------------
-- 6. Cargar datos iniciales desde Excel
----------------------------
-- Ejemplo para métrica de Generación
INSERT INTO Metrica (MetricKey, Nombre, Categoria, Unidad, Url, Frecuencia) VALUES
('Gene', 'Generación por Sistema', 'Generación', 'kWh', 'http://servapibi.xm.com.co/hourly', 'Hourly'),
('ENFICC', 'Energía Firme', 'Sostenibilidad', 'kWh', 'http://servapibi.xm.com.co/daily', 'Daily');

-- Ejemplo de entidad
INSERT INTO Entidad (Codigo, Tipo, Nombre) VALUES
('SIN', 'Sistema', 'Sistema Interconectado Nacional'),
('EMB01', 'Embalse', 'Embalse Hidroeléctrico Principal');

----------------------------
-- 7. Optimización final
----------------------------
CREATE INDEX idx_entidad_dinamico ON Entidad USING GIN (to_tsvector('spanish', Codigo || ' ' || Nombre));
VACUUM ANALYZE;