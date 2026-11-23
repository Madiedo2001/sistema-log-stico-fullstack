import json
import uuid
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import psycopg2
from psycopg2.extras import RealDictCursor
import redis
from worker import procesar_notificacion_envio

app = FastAPI(title="API Sistema Logístico")

# Conexión al cliente de Redis para caché
redis_client = redis.Redis(host="localhost", port=6379, db=0, decode_responses=True)

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

@app.get("/")
def read_root():
    return {"status": "ok", "message": "API Sistema Logístico activa"}

@app.post("/api/generar-datos-prueba")
def generar_datos():
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        uid = uuid.uuid4().hex[:6]
        email_unico = f"contacto_{uid}@acme.com"
        codigo_rastreo = f"TRK-{uid.upper()}"

        cursor.execute("""
            INSERT INTO usuarios (nombre, email, password_hash, rol) 
            VALUES (%s, %s, 'hash123', 'cliente') 
            RETURNING id;
        """, (f'Empresa ACME {uid}', email_unico))
        cliente_id = cursor.fetchone()[0]

        cursor.execute("""
            INSERT INTO paquetes (cliente_id, descripcion, peso_kg, direccion_origen, direccion_destino) 
            VALUES (%s, 'Lote de Teclados Mecánicos', 15.5, 'Bodega Central', 'Sucursal Norte') 
            RETURNING id;
        """, (cliente_id,))
        paquete_id = cursor.fetchone()[0]

        cursor.execute("""
            INSERT INTO envios (paquete_id, estado, codigo_rastreo) 
            VALUES (%s, 'pendiente', %s);
        """, (paquete_id, codigo_rastreo))
        
        # Disparar tarea en segundo plano
        procesar_notificacion_envio.delay(codigo_rastreo, email_unico)

        conn.commit()

        # Invalidate el caché de envíos en Redis
        redis_client.delete("cache:envios")

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

@app.get("/api/envios")
def obtener_envios():
    # 1. Intentar obtener datos del caché de Redis
    datos_cache = redis_client.get("cache:envios")
    if datos_cache:
        return json.loads(datos_cache)

    # 2. Si no están en caché, consultar PostgreSQL
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

        # 3. Guardar en Redis con expiración de 60 segundos
        redis_client.setex("cache:envios", 60, json.dumps(envios, default=str))

        return envios
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()