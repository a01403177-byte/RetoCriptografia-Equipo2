Proyecto de ciberseguridad para Casa Monarca enfocado en integridad, firma digital, cifrado y control de accesos usando herramientas de código abierto.

# Integrantes

  Ana Lidia Hernández Díaz A00838643 

  Ana Paula García ValverdeA01174572 

  María Fernanda Montoya López A01743214 

  Javier Rojas Orrante A01352213 
  
  Xavier Lago Hicks A01403177

Implementacion minima del gestor de identidades usando FastAPI, SQLAlchemy y MySQL.

## Incluye

- Autenticacion externa con JWT.
- Identidad local en MySQL.
- Un rol por usuario.
- Autorizacion por permisos del rol.
- Revocacion y expiracion.
- Auditoria de eventos clave.

## Arranque

1. Crea `.env` a partir de [.env.example](/Users/javier/Documents/New%20project/.env.example).
2. Ejecuta el SQL de [sql/schema.sql](/Users/javier/Documents/New%20project/sql/schema.sql).
3. Instala dependencias con `pip install -e .`.
4. Inicia el servidor con `uvicorn app.main:app --reload`.

## Rutas

- `GET /health`
- `GET /api/me`
- `POST /api/users`
- `GET /api/users`
- `GET /api/users/{id}`
- `PUT /api/users/{id}`
- `POST /api/users/{id}/activate`
- `POST /api/users/{id}/revoke`
- `POST /api/users/{id}/reactivate`
- `POST /api/users/{id}/role`
- `GET /api/audit-logs`

## Documentacion

- Guia tecnica: [docs/USO_Y_FUNCIONAMIENTO.md](/Users/javier/Documents/New%20project/docs/USO_Y_FUNCIONAMIENTO.md)
