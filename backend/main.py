from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import psycopg2
from psycopg2.extras import RealDictCursor

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

# 2. Endpoint para inyectar datos de prueba (Seed)
@app.post("/api/generar-datos-prueba")
def generar_datos():
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        # Crear un usuario cliente
        cursor.execute("""
            INSERT INTO usuarios (nombre, email, password_hash, rol) 
            VALUES ('Empresa ACME', 'contacto@acme.com', 'hash123', 'cliente') 
            RETURNING id;
        """)
        cliente_id = cursor.fetchone()[0]

        # Crear un paquete asociado al cliente
        cursor.execute("""
            INSERT INTO paquetes (cliente_id, descripcion, peso_kg, direccion_origen, direccion_destino) 
            VALUES (%s, 'Lote de Teclados Mecánicos', 15.5, 'Bodega Central', 'Sucursal Norte') 
            RETURNING id;
        """, (cliente_id,))
        paquete_id = cursor.fetchone()[0]

        # Crear el envío asociado al paquete
        cursor.execute("""
            INSERT INTO envios (paquete_id, estado, codigo_rastreo) 
            VALUES (%s, 'pendiente', 'TRK-987654321');
        """, (paquete_id,))
        
        conn.commit()
        return {"mensaje": "Datos de prueba generados exitosamente"}
    except Exception as e:
        conn.rollback()
        return {"error": str(e)}
    finally:
        cursor.close()
        conn.close()

# 3. Endpoint para consultar los envíos (El que consumirá el Frontend)
@app.get("/api/envios")
def obtener_envios():
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
    cursor.close()
    conn.close()
    return envios