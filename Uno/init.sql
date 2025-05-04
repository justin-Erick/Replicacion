-- Aquí puedes agregar scripts de inicialización de la base de datos
CREATE TABLE IF NOT EXISTS ejemplo (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL
);