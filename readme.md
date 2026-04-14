# Gestor de Identidades Demo

Version minima para demostrar funcionamiento con interfaz web.

## Que hace

- Crea usuarios demo.
- Cambia roles.
- Activa o revoca cuentas.
- Calcula permisos efectivos por rol.
- Registra auditoria basica.

## Como correrlo

1. Copia [.env.example](/Users/javier/Documents/New%20project/.env.example) a `.env` si quieres cambiar puerto o ruta de base.
2. Instala dependencias con `pip install -e .`.
3. Ejecuta `uvicorn app.main:app --reload`.
4. Abre [http://127.0.0.1:8000](http://127.0.0.1:8000).

La app crea automaticamente una base SQLite local y carga datos demo la primera vez.

## Rutas utiles

- `GET /`
- `GET /health`
- `GET /api/me?as_user=1`
- `GET /api/users?as_user=1`
- `GET /api/audit-logs?as_user=1`

## Documentacion

- [docs/USO_Y_FUNCIONAMIENTO.md](/Users/javier/Documents/New%20project/docs/USO_Y_FUNCIONAMIENTO.md)
