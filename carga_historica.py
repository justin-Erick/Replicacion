import os
import json
import pandas as pd
import requests
import psycopg2
from psycopg2 import sql
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta

# Configuración de la base de datos
DB_CONFIG = {
    'host': os.environ.get('DB_HOST', 'localhost'),
    'port': os.environ.get('DB_PORT', 5432),
    'dbname': os.environ.get('DB_NAME', 'mi_db'),
    'user': os.environ.get('DB_USER', 'admin'),
    'password': os.environ.get('DB_PASSWORD', 'adminpassword')
}

# Definir métricas directamente en el código para evitar problemas con el Excel
METRICAS = [
    {"MetricId": "DemaReal", "Entities": ["Sistema", "Agente"], "Unit": "kWh", "Url": "http://servapibi.xm.com.co/hourly", 
     "Filters": {"Agente": "Codigo Comercializador", "Sistema": None}},
    {"MetricId": "DemaComeNoReg", "Entities": ["Agente", "Sistema", "CIIU"], "Unit": "kWh", "Url": "http://servapibi.xm.com.co/hourly", 
     "Filters": {"Agente": "Codigo Comercializador", "Sistema": None, "CIIU": None}},
    {"MetricId": "Gene", "Entities": ["Sistema", "Recurso"], "Unit": "kWh", "Url": "http://servapibi.xm.com.co/hourly", 
     "Filters": {"Recurso": "Codigo Submercado Generación", "Sistema": None}},
    {"MetricId": "DispoReal", "Entities": ["Recurso"], "Unit": "kW", "Url": "http://servapibi.xm.com.co/hourly", 
     "Filters": {"Recurso": "Codigo Submercado Generación"}},
    {"MetricId": "PrecBolsNaci", "Entities": ["Sistema"], "Unit": "COP/kWh", "Url": "http://servapibi.xm.com.co/hourly", 
     "Filters": {"Sistema": None}},
    {"MetricId": "CostMargDesp", "Entities": ["Sistema"], "Unit": "COP/MWh", "Url": "http://servapibi.xm.com.co/hourly", 
     "Filters": {"Sistema": None}},
    {"MetricId": "PerdidasEner", "Entities": ["Sistema", "Agente"], "Unit": "kWh", "Url": "http://servapibi.xm.com.co/hourly", 
     "Filters": {"Sistema": None, "Agente": "Codigo Comercializador"}},
    {"MetricId": "EmisionCO2Eq", "Entities": ["Recurso"], "Unit": "gCO2e/kWh", "Url": "http://servapibi.xm.com.co/hourly", 
     "Filters": {"Recurso": "Codigo Submercado Generación"}},
    {"MetricId": "factorEmisionCO2e", "Entities": ["Sistema"], "Unit": "gCO2e/kWh", "Url": "http://servapibi.xm.com.co/hourly", 
     "Filters": {"Sistema": None}},
    {"MetricId": "CompBolsNaciEner", "Entities": ["Sistema", "Agente"], "Unit": "MkWh", "Url": "http://servapibi.xm.com.co/hourly", 
     "Filters": {"Sistema": None, "Agente": "Codigo Agente"}},
    {"MetricId": "VentContEner", "Entities": ["Sistema", "Agente"], "Unit": "kWh", "Url": "http://servapibi.xm.com.co/hourly", 
     "Filters": {"Sistema": None, "Agente": "Codigo Agente"}}
]

# Definir rango de fechas para extracción de datos
fecha_fin = datetime.today().date()
fecha_ini = fecha_fin - relativedelta(years=3) 

# Función para verificar y crear entidades automáticamente
def verificar_crear_entidad(tipo_entidad, codigo, nombre=None):
    if nombre is None:
        nombre = f"{tipo_entidad} - {codigo}"
    
    try:
        # Verificar si la entidad existe
        cursor.execute(
            sql.SQL("SELECT EntidadID FROM Entidad WHERE Tipo = %s AND Codigo = %s"),
            (tipo_entidad, codigo)
        )
        res = cursor.fetchone()
        
        if res:
            return res[0]  # La entidad existe, devolver su ID
        
        # Si no existe, crearla
        cursor.execute("""
            INSERT INTO Entidad (Codigo, Nombre, Tipo, Filtro)
            VALUES (%s, %s, %s, %s)
            RETURNING EntidadID
        """, (codigo, nombre, tipo_entidad, 'No aplica'))
        
        entidad_id = cursor.fetchone()[0]
        conn.commit()
        print(f"Entidad creada: {tipo_entidad} - {codigo}")
        return entidad_id
    
    except Exception as e:
        print(f"Error al verificar/crear entidad {tipo_entidad} - {codigo}: {e}")
        conn.rollback()
        return None

# Conectar a la base de datos
try:
    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()
    print("Conexión exitosa a la base de datos")
except Exception as e:
    print(f"Error de conexión a la base de datos: {e}")
    exit(1)

def get_metrica_id(metric_id):
    """Obtiene el ID de una métrica desde la base de datos"""
    try:
        cursor.execute("SELECT MetricaID FROM Metrica WHERE MetricKey = %s", (metric_id,))
        res = cursor.fetchone()
        return res[0] if res else None
    except Exception as e:
        print(f"Error al obtener MetricaID para {metric_id}: {e}")
        return None

def insertar_dato(fecha, valores, metric_id, entidad_tipo, codigo_entidad):
    """Inserta un dato en la tabla correspondiente según su frecuencia"""
    entidad_id = verificar_crear_entidad(entidad_tipo, codigo_entidad)
    metrica_id = get_metrica_id(metric_id)
    
    if not entidad_id:
        print(f"No se pudo obtener/crear entidad: {entidad_tipo} - {codigo_entidad}")
        return
    
    if not metrica_id:
        print(f"Métrica no encontrada: {metric_id}")
        return
    
    valores_json = json.dumps(valores) if isinstance(valores, dict) else json.dumps({"value": valores})
    
    try:
        # Determinar la tabla según la frecuencia
        if "Hour" in str(valores):
            cursor.execute("""
                INSERT INTO DatosHora (MetricaID, EntidadID, Fecha, Valores)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT DO NOTHING
            """, (metrica_id, entidad_id, fecha, valores_json))
        else:
            cursor.execute("""
                INSERT INTO DatosDiarios (MetricaID, EntidadID, Fecha, Valores)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT DO NOTHING
            """, (metrica_id, entidad_id, fecha, valores_json))
        
    except Exception as e:
        print(f"Error al insertar dato {metric_id} para {entidad_tipo}:{codigo_entidad}: {e}")
        conn.rollback()

def procesar_metrica(metrica):
    """Procesa una métrica, consultando a la API y almacenando resultados"""
    metric_id = metrica["MetricId"]
    entities = metrica["Entities"]
    url = metrica["Url"]
    
    print(f"Procesando métrica: {metric_id}")
    
    for entity_type in entities:
        print(f"  Procesando entidad: {entity_type}")
        filtro = metrica["Filters"].get(entity_type)
        
        fecha_actual = fecha_ini
        while fecha_actual <= fecha_fin:
            # Procesamos por meses para evitar sobrecarga
            fecha_mes_fin = min(fecha_actual + relativedelta(months=1) - timedelta(days=1), fecha_fin)
            
            print(f"    Periodo: {fecha_actual} a {fecha_mes_fin}")
            
            payload = {
                "MetricId": metric_id,
                "StartDate": fecha_actual.strftime('%Y-%m-%d'),
                "EndDate": fecha_mes_fin.strftime('%Y-%m-%d'),
                "Entity": entity_type,
                "Filter": [filtro] if filtro else []
            }

            try:
                print(f"    Enviando solicitud: {json.dumps(payload)}")
                response = requests.post(url, json=payload, timeout=60)
                
                if response.status_code != 200:
                    print(f"    Error en la API: {response.status_code} - {response.text}")
                    fecha_actual = fecha_mes_fin + timedelta(days=1)
                    continue
                
                data = response.json()
                
                if not data.get("Items"):
                    print("    No se encontraron datos en la respuesta")
                    fecha_actual = fecha_mes_fin + timedelta(days=1)
                    continue
                
                print(f"    Procesando {len(data.get('Items', []))} elementos de datos")
                
                for item in data.get("Items", []):
                    fecha = item["Date"]
                    
                    # Procesamos datos horarios
                    for registro in item.get("HourlyEntities", []):
                        codigo = registro.get("Code", "SIN")  # Default para Sistema
                        valores = registro.get("Values", {})
                        insertar_dato(fecha, valores, metric_id, entity_type, codigo)
                    
                    # Procesamos datos diarios
                    for registro in item.get("DailyEntities", []):
                        codigo = registro.get("Code", "SIN")  # Default para Sistema
                        valores = registro.get("Values", {})
                        insertar_dato(fecha, valores, metric_id, entity_type, codigo)
                
                conn.commit()
                print(f"    Datos para {fecha_actual} a {fecha_mes_fin} procesados correctamente")
            
            except Exception as e:
                print(f"    Error en {metric_id} ({entity_type}): {e}")
                conn.rollback()

            fecha_actual = fecha_mes_fin + timedelta(days=1)

def main():
    """Función principal que ejecuta el proceso de carga"""
    try:
        for metrica in METRICAS:
            procesar_metrica(metrica)
        print("Proceso completado exitosamente.")
    except Exception as e:
        print(f"Error general: {e}")
    finally:
        cursor.close()
        conn.close()
        print("Conexión a la base de datos cerrada.")

if __name__ == "__main__":
    main()