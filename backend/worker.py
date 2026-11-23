import time
from celery import Celery

celery_app = Celery(
    "tasks",
    broker="redis://localhost:6379/0",
    backend="redis://localhost:6379/0"
)

@celery_app.task
def procesar_notificacion_envio(codigo_rastreo: str, email_cliente: str):
    # Simulación de tarea en segundo plano (envío de email / webhook)
    time.sleep(3)
    print(f"Notificación enviada a {email_cliente} para el envío {codigo_rastreo}")
    return True