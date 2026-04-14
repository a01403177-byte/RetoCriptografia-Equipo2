# Uso y Funcionamiento

Esta version es intencionalmente minima.

## Idea central

- El proveedor externo autentica.
- La tabla `users` decide si la persona puede operar.
- Cada usuario tiene un solo rol.
- Los permisos se resuelven desde ese rol.

## Flujo

1. El frontend obtiene un JWT del proveedor externo.
2. Lo envia al backend en `Authorization: Bearer <token>`.
3. El backend valida el token.
4. Busca usuario local por `auth_sub`.
5. Si no existe, intenta primer binding por `email`.
6. Si el usuario estaba `pending`, lo activa.
7. Si el estado no es `active`, bloquea acceso.
8. Carga permisos del rol y permite o niega la accion.

## Archivos clave

- [app/main.py](/Users/javier/Documents/New%20project/app/main.py): endpoints y startup.
- [app/deps.py](/Users/javier/Documents/New%20project/app/deps.py): autenticacion y permisos.
- [app/services.py](/Users/javier/Documents/New%20project/app/services.py): logica de identidad, autorizacion y auditoria.
- [app/models.py](/Users/javier/Documents/New%20project/app/models.py): modelos SQLAlchemy.
- [sql/schema.sql](/Users/javier/Documents/New%20project/sql/schema.sql): esquema inicial.

## Uso rapido

```bash
uvicorn app.main:app --reload
```

Luego consulta:

- `GET /health`
- `GET /api/me`

Para las rutas protegidas necesitas un JWT valido y un preregistro local.
