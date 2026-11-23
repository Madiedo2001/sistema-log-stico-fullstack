import json
import uuid
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import psycopg2
from psycopg2.extras import RealDictCursor
import redis

from worker import procesar_notificacion_envio
from auth import create_access_token, verify_password, require_roles, hash_password

app = FastAPI(title="API Sistema Logístico")

# Conexión al cliente de Redis para caché
redis_client = redis.Redis(host="localhost", port=6379, db=0, decode_responses=True)

# Configurar CORS
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

# Esquema para recepción de credenciales en Login
class LoginSchema(BaseModel):
    email: str
    password: str

# 1. Endpoint raíz (Health Check para Pytest y supervisión)
@app.get("/")
def read_root():
    return {"status": "ok", "message": "API Sistema Logístico activa"}

# 2. Endpoint de Autenticación (Login con JWT)
@app.post("/api/auth/login")
def login(credentials: LoginSchema):
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute("SELECT * FROM usuarios WHERE email = %s;", (credentials.email,))
        usuario = cursor.fetchone()

        if not usuario or not verify_password(credentials.password, usuario["password_hash"]):
            raise HTTPException(status_code=401, detail="Credenciales incorrectas")

        token = create_access_token({
            "sub": str(usuario["id"]),
            "email": usuario["email"],
            "rol": usuario["rol"]
        })
        return {
            "access_token": token,
            "token_type": "bearer",
            "rol": usuario["rol"]
        }
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

# 3. Endpoint para inyectar datos de prueba (Seed cifrado + Celery)
@app.post("/api/generar-datos-prueba")
def generar_datos():
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        uid = uuid.uuid4().hex[:6]
        email_unico = f"admin_{uid}@acme.com"
        codigo_rastreo = f"TRK-{uid.upper()}"
        
        # Cifrar contraseña para permitir login posterior
        hashed_password = hash_password("admin123")

        # Crear usuario administrador
        cursor.execute("""
            INSERT INTO usuarios (nombre, email, password_hash, rol) 
            VALUES (%s, %s, %s, 'admin') 
            RETURNING id;
        """, (f'Empresa ACME {uid}', email_unico, hashed_password))
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
        
        # Disparar tarea asíncrona en segundo plano mediante Redis + Celery
        procesar_notificacion_envio.delay(codigo_rastreo, email_unico)

        conn.commit()

        # Invalidar caché de envíos en Redis
        redis_client.delete("cache:envios")

        return {
            "mensaje": "Datos de prueba generados exitosamente",
            "codigo_rastreo": codigo_rastreo,
            "email": email_unico,
            "password_demo": "admin123",
            "rol": "admin"
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

# 4. Endpoint para consultar envíos (Con caché de lectura Redis)
@app.get("/api/envios")
def obtener_envios():
    # 1. Intentar obtener respuesta desde el caché en Redis
    datos_cache = redis_client.get("cache:envios")
    if datos_cache:
        return json.loads(datos_cache)

    # 2. Si no existe en caché, consultar PostgreSQL
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