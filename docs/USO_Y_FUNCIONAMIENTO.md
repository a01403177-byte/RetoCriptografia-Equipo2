# Uso y Funcionamiento

Esta version es una demo local muy simple. La meta es mostrar que el control de identidades funciona, no simular un IAM completo.

## Que se simplifico

- No usa autenticacion externa.
- No usa JWT.
- No depende de MySQL para la demo.
- No necesita migraciones manuales.

## Que se mantiene

- Identidad local.
- Un rol por usuario.
- Permisos por rol.
- Estados `pending`, `active`, `revoked`, `expired`.
- Auditoria de acciones.

## Como arranca

1. FastAPI levanta la app.
2. SQLAlchemy crea las tablas automaticamente.
3. Se insertan roles, permisos y usuarios demo si la base esta vacia.
4. El dashboard se sirve desde `GET /`.

## Flujo de la interfaz

1. Seleccionas con que usuario actuar.
2. La app calcula sus permisos.
3. Si es administrador, puede crear usuarios, activar, revocar o cambiar rol.
4. Cada accion deja un evento en la bitacora.

## Usuarios demo iniciales

- `Admin Demo`
- `Ana Humanitaria`
- `Luis Externo`

## Archivos clave

- [app/main.py](/Users/javier/Documents/New%20project/app/main.py): interfaz y rutas.
- [app/services.py](/Users/javier/Documents/New%20project/app/services.py): seed, permisos, usuarios y auditoria.
- [app/models.py](/Users/javier/Documents/New%20project/app/models.py): tablas.
- [app/db.py](/Users/javier/Documents/New%20project/app/db.py): base local.

## Uso rapido

```bash
pip install -e .
uvicorn app.main:app --reload
```

Luego abre `http://127.0.0.1:8000`.
