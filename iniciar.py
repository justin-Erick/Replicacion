import os
import psycopg2
from psycopg2 import sql

# Configuración de la base de datos
DB_CONFIG = {
    'host': os.environ.get('DB_HOST', 'localhost'),
    'port': os.environ.get('DB_PORT', 5432),
    'dbname': os.environ.get('DB_NAME', 'mi_db'),
    'user': os.environ.get('DB_USER', 'admin'),
    'password': os.environ.get('DB_PASSWORD', 'adminpassword')
}

# Lista de entidades a insertar
ENTIDADES = [
    # Sistema (principal)
    {'codigo': 'SIN', 'nombre': 'Sistema Interconectado Nacional', 'tipo': 'Sistema', 'filtro': 'No aplica'},
    
    # Algunos ejemplos de Agentes (puedes ampliar esta lista)
    {'codigo': 'EPMG', 'nombre': 'EPM Generación', 'tipo': 'Agente', 'filtro': 'No aplica'},
    {'codigo': 'ISAG', 'nombre': 'ISAGEN', 'tipo': 'Agente', 'filtro': 'No aplica'},
    {'codigo': 'CHVG', 'nombre': 'CHIVOR', 'tipo': 'Agente', 'filtro': 'No aplica'},
    {'codigo': 'ENDG', 'nombre': 'ENDESA', 'tipo': 'Agente', 'filtro': 'No aplica'},
    {'codigo': 'GEEG', 'nombre': 'GENSA', 'tipo': 'Agente', 'filtro': 'No aplica'},
    
    # Algunos ejemplos de Recursos (puedes ampliar esta lista)
    {'codigo': 'GUAT', 'nombre': 'Guatapé', 'tipo': 'Recurso', 'filtro': 'No aplica'},
    {'codigo': 'CHIV', 'nombre': 'Chivor', 'tipo': 'Recurso', 'filtro': 'No aplica'},
    {'codigo': 'PORG', 'nombre': 'Porce III', 'tipo': 'Recurso', 'filtro': 'No aplica'},
    {'codigo': 'TBSA', 'nombre': 'Termobarranquilla', 'tipo': 'Recurso', 'filtro': 'No aplica'},
    {'codigo': 'TASI', 'nombre': 'Tasajero', 'tipo': 'Recurso', 'filtro': 'No aplica'},
    
    # Algunos ejemplos de CIIU (puedes ampliar esta lista)
    {'codigo': 'A', 'nombre': 'Agricultura, ganadería, caza y silvicultura', 'tipo': 'CIIU', 'filtro': 'No aplica'},
    {'codigo': 'B', 'nombre': 'Pesca', 'tipo': 'CIIU', 'filtro': 'No aplica'},
    {'codigo': 'C', 'nombre': 'Explotación de minas y canteras', 'tipo': 'CIIU', 'filtro': 'No aplica'},
    {'codigo': 'D', 'nombre': 'Industrias manufactureras', 'tipo': 'CIIU', 'filtro': 'No aplica'},
]

def main():
    # Conectar a la base de datos
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        print("Conexión exitosa a la base de datos")
    except Exception as e:
        print(f"Error de conexión a la base de datos: {e}")
        return

    try:
        # Inicializar métricas
        print("Inicializando métricas...")
        
        metricas = [
            {
                'MetricKey': 'DemaReal', 
                'Nombre': 'Demanda Real', 
                'Categoria': 'Demanda', 
                'Unidad': 'kWh',
                'Url': 'http://servapibi.xm.com.co/hourly',
                'Filtro': 'Codigo Comercializador',
                'Descripcion': 'Demanda de energía real del sistema',
                'Frecuencia': 'Hourly',
                'EntidadTipo': 'Sistema'
            },
            {
                'MetricKey': 'DemaComeNoReg', 
                'Nombre': 'Demanda Comercial No Regulada', 
                'Categoria': 'Demanda', 
                'Unidad': 'kWh',
                'Url': 'http://servapibi.xm.com.co/hourly',
                'Filtro': 'Codigo Comercializador',
                'Descripcion': 'Demanda comercial no regulada',
                'Frecuencia': 'Hourly',
                'EntidadTipo': 'Sistema'
            },
            {
                'MetricKey': 'Gene', 
                'Nombre': 'Generación', 
                'Categoria': 'Generación', 
                'Unidad': 'kWh',
                'Url': 'http://servapibi.xm.com.co/hourly',
                'Filtro': 'Codigo Submercado Generación',
                'Descripcion': 'Generación de energía',
                'Frecuencia': 'Hourly',
                'EntidadTipo': 'Sistema'
            },
            {
                'MetricKey': 'DispoReal', 
                'Nombre': 'Disponibilidad Real', 
                'Categoria': 'Disponibilidad', 
                'Unidad': 'kW',
                'Url': 'http://servapibi.xm.com.co/hourly',
                'Filtro': 'Codigo Submercado Generación',
                'Descripcion': 'Disponibilidad real de recursos',
                'Frecuencia': 'Hourly',
                'EntidadTipo': 'Recurso'
            },
            {
                'MetricKey': 'PrecBolsNaci', 
                'Nombre': 'Precio Bolsa Nacional', 
                'Categoria': 'Precios', 
                'Unidad': 'COP/kWh',
                'Url': 'http://servapibi.xm.com.co/hourly',
                'Filtro': 'No aplica',
                'Descripcion': 'Precio de bolsa nacional',
                'Frecuencia': 'Hourly',
                'EntidadTipo': 'Sistema'
            },
            {
                'MetricKey': 'CostMargDesp', 
                'Nombre': 'Costo Marginal de Despacho', 
                'Categoria': 'Precios', 
                'Unidad': 'COP/MWh',
                'Url': 'http://servapibi.xm.com.co/hourly',
                'Filtro': 'No aplica',
                'Descripcion': 'Costo marginal de despacho',
                'Frecuencia': 'Hourly',
                'EntidadTipo': 'Sistema'
            },
            {
                'MetricKey': 'PerdidasEner', 
                'Nombre': 'Pérdidas de Energía', 
                'Categoria': 'Pérdidas', 
                'Unidad': 'kWh',
                'Url': 'http://servapibi.xm.com.co/hourly',
                'Filtro': 'Codigo Comercializador',
                'Descripcion': 'Pérdidas de energía en el sistema',
                'Frecuencia': 'Hourly',
                'EntidadTipo': 'Sistema'
            },
            {
                'MetricKey': 'EmisionCO2Eq', 
                'Nombre': 'Emisiones CO2 Equivalente', 
                'Categoria': 'Emisiones', 
                'Unidad': 'gCO2e/kWh',
                'Url': 'http://servapibi.xm.com.co/hourly',
                'Filtro': 'Codigo Submercado Generación',
                'Descripcion': 'Emisiones de CO2 equivalente por recurso',
                'Frecuencia': 'Hourly',
                'EntidadTipo': 'Recurso'
            },
            {
                'MetricKey': 'factorEmisionCO2e', 
                'Nombre': 'Factor de Emisión CO2e', 
                'Categoria': 'Emisiones', 
                'Unidad': 'gCO2e/kWh',
                'Url': 'http://servapibi.xm.com.co/hourly',
                'Filtro': 'No aplica',
                'Descripcion': 'Factor de emisión de CO2 equivalente del sistema',
                'Frecuencia': 'Hourly',
                'EntidadTipo': 'Sistema'
            },
            {
                'MetricKey': 'CompBolsNaciEner', 
                'Nombre': 'Compras en Bolsa Nacional de Energía', 
                'Categoria': 'Transacciones', 
                'Unidad': 'MkWh',
                'Url': 'http://servapibi.xm.com.co/hourly',
                'Filtro': 'Codigo Agente',
                'Descripcion': 'Compras en bolsa nacional de energía',
                'Frecuencia': 'Hourly',
                'EntidadTipo': 'Sistema'
            },
            {
                'MetricKey': 'VentContEner', 
                'Nombre': 'Ventas en Contratos de Energía', 
                'Categoria': 'Transacciones', 
                'Unidad': 'kWh',
                'Url': 'http://servapibi.xm.com.co/hourly',
                'Filtro': 'Codigo Agente',
                'Descripcion': 'Ventas en contratos de energía',
                'Frecuencia': 'Hourly',
                'EntidadTipo': 'Sistema'
            },
        ]
        
        for metrica in metricas:
            cursor.execute("""
                INSERT INTO Metrica (MetricKey, Nombre, Categoria, Unidad, Url, Filtro, Descripcion, Frecuencia, EntidadTipo)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (MetricKey, EntidadTipo) DO UPDATE 
                SET Nombre = EXCLUDED.Nombre,
                    Categoria = EXCLUDED.Categoria,
                    Unidad = EXCLUDED.Unidad,
                    Url = EXCLUDED.Url,
                    Filtro = EXCLUDED.Filtro,
                    Descripcion = EXCLUDED.Descripcion,
                    Frecuencia = EXCLUDED.Frecuencia
            """, (
                metrica['MetricKey'], 
                metrica['Nombre'], 
                metrica['Categoria'], 
                metrica['Unidad'],
                metrica['Url'],
                metrica['Filtro'],
                metrica['Descripcion'],
                metrica['Frecuencia'],
                metrica['EntidadTipo']
            ))
        
        conn.commit()
        print("Métricas inicializadas correctamente")
        
        # Insertar o actualizar entidades
        print("Inicializando entidades...")
        for entidad in ENTIDADES:
            cursor.execute("""
                INSERT INTO Entidad (Codigo, Nombre, Tipo, Filtro)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (Codigo, Tipo) DO UPDATE 
                SET Nombre = EXCLUDED.Nombre,
                    Filtro = EXCLUDED.Filtro
            """, (entidad['codigo'], entidad['nombre'], entidad['tipo'], entidad['filtro']))
        
        conn.commit()
        print("Entidades inicializadas correctamente")
        
    except Exception as e:
        print(f"Error al inicializar datos: {e}")
        conn.rollback()
    finally:
        cursor.close()
        conn.close()
        print("Conexión a la base de datos cerrada")

if __name__ == "__main__":
    main()