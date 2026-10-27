# Sistema de Gestión Logística - Full-Stack

Plataforma integral para el monitoreo y gestión de envíos logísticos. Este proyecto demuestra una arquitectura moderna dividida en microservicios, abarcando desde la infraestructura y persistencia de datos hasta una interfaz de usuario reactiva.

## 🛠️ Stack Tecnológico

*   **Infraestructura:** Docker & Docker Compose
*   **Base de Datos:** PostgreSQL (Uso de UUIDs y tipos ENUM para integridad transaccional)
*   **Backend:** Python 3 + FastAPI (API RESTful de alto rendimiento)
*   **Frontend:** Next.js (React) + Tailwind CSS (Renderizado del lado del cliente y diseño responsive)

## 🚀 Características Principales

*   **Modelado Relacional Seguro:** Arquitectura de base de datos diseñada para evitar la inyección de estados inválidos mediante `ENUMs`.
*   **API Documentada:** Generación automática de documentación interactiva (Swagger UI) integrada en FastAPI.
*   **Trazabilidad:** Tablas diseñadas para soportar historiales inmutables (logs) de los cambios de estado de cada envío.
*   **Interfaz Moderna:** Panel de control asíncrono que consume la API REST para mostrar el estado de los paquetes en tiempo real.

## ⚙️ Instrucciones de Ejecución Local

### 1. Levantar la Base de Datos (Docker)
```bash
docker-compose up -d