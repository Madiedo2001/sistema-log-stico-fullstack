import uuid
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import psycopg2
from psycopg2.extras import RealDictCursor
from worker import procesar_notificacion_envio

app = FastAPI(title="API Sistema Logístico")

# 1. Configurar CORS para permitir que el Frontend (React/Next.js) se conecte sin bloqueos
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DB_CONFIG = {
    "dbname": "logistica_db",
    "user": "admin",
    "password": "adminpassword",
    "host": "localhost",
    "port": "5432"
}

def get_db_connection():
    return psycopg2.connect(**DB_CONFIG)

# Endpoint raíz para verificación de estado (Health Check / Pytest)
@app.get("/")
def read_root():
    return {"status": "ok", "message": "API Sistema Logístico activa"}

# 2. Endpoint para inyectar datos de prueba (Seed)
@app.post("/api/generar-datos-prueba")
def generar_datos():
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Generar sufijo único para evitar errores de restricción UNIQUE
        uid = uuid.uuid4().hex[:6]
        email_unico = f"contacto_{uid}@acme.com"
        codigo_rastreo = f"TRK-{uid.upper()}"

        # Crear usuario cliente
        cursor.execute("""
            INSERT INTO usuarios (nombre, email, password_hash, rol) 
            VALUES (%s, %s, 'hash123', 'cliente') 
            RETURNING id;
        """, (f'Empresa ACME {uid}', email_unico))
        cliente_id = cursor.fetchone()[0]

        # Crear paquete asociado
        cursor.execute("""
            INSERT INTO paquetes (cliente_id, descripcion, peso_kg, direccion_origen, direccion_destino) 
            VALUES (%s, 'Lote de Teclados Mecánicos', 15.5, 'Bodega Central', 'Sucursal Norte') 
            RETURNING id;
        """, (cliente_id,))
        paquete_id = cursor.fetchone()[0]

        # Crear envío asociado
        cursor.execute("""
            INSERT INTO envios (paquete_id, estado, codigo_rastreo) 
            VALUES (%s, 'pendiente', %s);
        """, (paquete_id, codigo_rastreo))
        
        # Disparar tarea en segundo plano mediante Redis + Celery
        procesar_notificacion_envio.delay(codigo_rastreo, email_unico)

        conn.commit()
        return {
            "mensaje": "Datos de prueba generados exitosamente",
            "codigo_rastreo": codigo_rastreo,
            "email": email_unico
        }
    except Exception as e:
        if conn:
            conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

# 3. Endpoint para consultar los envíos (El que consumirá el Frontend)
@app.get("/api/envios")
def obtener_envios():
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute("""
            SELECT e.codigo_rastreo, e.estado, p.descripcion, p.peso_kg, p.direccion_destino, u.nombre as cliente
            FROM envios e
            JOIN paquetes p ON e.paquete_id = p.id
            JOIN usuarios u ON p.cliente_id = u.id
            ORDER BY e.fecha_actualizacion DESC;
        """)
        envios = cursor.fetchall()
        return envios
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()