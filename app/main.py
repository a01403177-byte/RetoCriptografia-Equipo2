from contextlib import asynccontextmanager
from datetime import datetime
from html import escape
from urllib.parse import urlencode

from fastapi import Depends, FastAPI, Form, HTTPException, Query
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session

from app.config import settings
from app.db import Base, engine
from app.deps import get_db
from app.schemas import AuditLogOut, MeOut, UserOut
from app.services import AuditService, AuthorizationService, BootstrapService, UserService


@asynccontextmanager
async def lifespan(_: FastAPI):
    Base.metadata.create_all(bind=engine)
    with Session(bind=engine) as db:
        BootstrapService.seed(db)
    yield


app = FastAPI(title=settings.app_name, lifespan=lifespan)


def parse_end_date(value: str) -> datetime | None:
    cleaned = value.strip()
    if not cleaned:
        return None
    return datetime.fromisoformat(cleaned)


def get_actor_or_404(db: Session, actor_id: int | None):
    actor = UserService.get_actor(db, actor_id)
    if not actor:
        raise HTTPException(status_code=404, detail="No actor available")
    return actor


def require_actor_permission(db: Session, actor, resource: str, action: str) -> None:
    if AuthorizationService.authorize(db, actor, resource, action):
        return

    AuditService.log(
        db,
        event_type="access_denied",
        actor_user_id=actor.id,
        target_user_id=actor.id,
        action=action,
        resource=resource,
        result="failure",
    )
    raise HTTPException(status_code=403, detail="Action not allowed for current demo user")


def redirect_home(actor_id: int) -> RedirectResponse:
    return RedirectResponse(url=f"/?{urlencode({'as_user': actor_id})}", status_code=303)


def render_dashboard(actor, users, roles, permissions, logs) -> str:
    permission_text = ", ".join(f"{item['resource']}:{item['action']}" for item in permissions) or "sin permisos"

    actor_options = "".join(
        f"<option value='{user.id}' {'selected' if user.id == actor.id else ''}>{escape(user.full_name)} ({escape(user.status)})</option>"
        for user in users
    )
    create_role_options = "".join(
        f"<option value='{role.id}'>{escape(role.name)}</option>"
        for role in roles
    )

    can_create = any(item["resource"] == "users" and item["action"] == "create" for item in permissions)
    can_activate = any(item["resource"] == "users" and item["action"] == "activate" for item in permissions)
    can_revoke = any(item["resource"] == "users" and item["action"] == "revoke" for item in permissions)
    can_reactivate = any(item["resource"] == "users" and item["action"] == "reactivate" for item in permissions)
    can_change_role = any(item["resource"] == "users" and item["action"] == "change_role" for item in permissions)

    rows = []
    for user in users:
        status_forms = []
        if can_activate:
            status_forms.append(
                f"""
                <form method="post" action="/ui/users/{user.id}/status">
                  <input type="hidden" name="actor_id" value="{actor.id}">
                  <input type="hidden" name="status" value="active">
                  <button type="submit">Activar</button>
                </form>
                """
            )
        if can_revoke:
            status_forms.append(
                f"""
                <form method="post" action="/ui/users/{user.id}/status">
                  <input type="hidden" name="actor_id" value="{actor.id}">
                  <input type="hidden" name="status" value="revoked">
                  <button type="submit">Revocar</button>
                </form>
                """
            )
        if can_reactivate:
            status_forms.append(
                f"""
                <form method="post" action="/ui/users/{user.id}/status">
                  <input type="hidden" name="actor_id" value="{actor.id}">
                  <input type="hidden" name="status" value="active">
                  <button type="submit">Reactivar</button>
                </form>
                """
            )

        role_form = "rol fijo"
        if can_change_role:
            role_form = f"""
            <form method="post" action="/ui/users/{user.id}/role" class="inline-form">
              <input type="hidden" name="actor_id" value="{actor.id}">
              <select name="role_id">
                {''.join(f"<option value='{role.id}' {'selected' if role.id == user.role_id else ''}>{escape(role.name)}</option>" for role in roles)}
              </select>
              <button type="submit">Cambiar rol</button>
            </form>
            """

        rows.append(
            f"""
            <tr>
              <td>{escape(user.full_name)}</td>
              <td>{escape(user.email)}</td>
              <td>{escape(user.role.name)}</td>
              <td><span class="status status-{escape(user.status)}">{escape(user.status)}</span></td>
              <td>{escape(user.end_date.isoformat(sep=' ', timespec='minutes')) if user.end_date else 'sin vencimiento'}</td>
              <td class="actions">{''.join(status_forms) or 'sin acciones'}</td>
              <td>{role_form}</td>
            </tr>
            """
        )

    create_form = ""
    if can_create:
        create_form = f"""
        <section class="panel">
          <h2>Crear preregistro</h2>
          <form method="post" action="/ui/users" class="stack">
            <input type="hidden" name="actor_id" value="{actor.id}">
            <label>Nombre completo<input name="full_name" required></label>
            <label>Correo<input name="email" type="email" required></label>
            <label>Rol<select name="role_id">{create_role_options}</select></label>
            <label>Expira opcionalmente<input name="end_date" type="datetime-local"></label>
            <button type="submit">Crear usuario</button>
          </form>
        </section>
        """

    log_items = "".join(
        f"<li><strong>{escape(log.event_type)}</strong> · {escape(log.result)} · objetivo {log.target_user_id or '-'}</li>"
        for log in logs
    ) or "<li>Sin eventos todavia.</li>"

    return f"""
    <!doctype html>
    <html lang="es">
      <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <title>{escape(settings.app_name)}</title>
        <style>
          :root {{
            --bg: #f5efe2;
            --card: #fffdf8;
            --ink: #1f2b37;
            --line: #dfd4c0;
            --accent: #a64b2a;
            --ok: #287346;
            --warn: #aa6a1f;
            --bad: #922f2f;
          }}
          * {{ box-sizing: border-box; }}
          body {{ margin: 0; background: linear-gradient(180deg, #efe3d0, var(--bg)); color: var(--ink); font-family: Georgia, serif; }}
          main {{ max-width: 1120px; margin: 0 auto; padding: 28px 18px 52px; }}
          .hero, .panel {{ background: var(--card); border: 1px solid var(--line); border-radius: 20px; box-shadow: 0 12px 32px rgba(31, 43, 55, 0.08); }}
          .hero {{ padding: 26px; }}
          .panel {{ padding: 18px; }}
          .grid {{ display: grid; gap: 18px; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); margin-top: 18px; }}
          .stack {{ display: grid; gap: 10px; }}
          label {{ display: grid; gap: 6px; font-size: 14px; }}
          input, select, button {{ font: inherit; padding: 10px 12px; border-radius: 10px; border: 1px solid #c9bca9; }}
          button {{ background: var(--accent); color: #fff; border: none; cursor: pointer; }}
          table {{ width: 100%; border-collapse: collapse; }}
          th, td {{ border-bottom: 1px solid #efe4d3; padding: 12px 10px; vertical-align: top; text-align: left; }}
          .status {{ display: inline-block; padding: 4px 10px; border-radius: 999px; font-weight: 700; font-size: 12px; }}
          .status-active {{ background: #ddf3e4; color: var(--ok); }}
          .status-pending {{ background: #fff0dc; color: var(--warn); }}
          .status-revoked, .status-expired {{ background: #f8dfdf; color: var(--bad); }}
          .actions form {{ margin-bottom: 8px; }}
          .inline-form {{ display: grid; gap: 8px; }}
          ul {{ margin: 0; padding-left: 18px; }}
          @media (max-width: 760px) {{
            table, thead, tbody, tr, th, td {{ display: block; }}
            thead {{ display: none; }}
            td {{ padding: 10px 0; }}
          }}
        </style>
      </head>
      <body>
        <main>
          <section class="hero">
            <h1>Gestor de identidades demo</h1>
            <p>Version minima para demostrar altas, roles, revocacion, expiracion y bitacora sin depender de integraciones externas.</p>
            <form method="get" action="/" class="stack" style="max-width: 360px;">
              <label>Actuar como
                <select name="as_user">{actor_options}</select>
              </label>
              <button type="submit">Cambiar usuario actual</button>
            </form>
          </section>

          <section class="grid">
            <article class="panel">
              <h2>Usuario actual</h2>
              <p><strong>{escape(actor.full_name)}</strong><br>{escape(actor.email)}</p>
              <p>Rol: <strong>{escape(actor.role.name)}</strong></p>
              <p>Estado: <span class="status status-{escape(actor.status)}">{escape(actor.status)}</span></p>
              <p>Permisos: {escape(permission_text)}</p>
            </article>
            <article class="panel">
              <h2>Resumen</h2>
              <p>Usuarios: <strong>{len(users)}</strong></p>
              <p>Roles: <strong>{len(roles)}</strong></p>
              <p>Eventos visibles: <strong>{len(logs)}</strong></p>
            </article>
          </section>

          {create_form}

          <section class="panel">
            <h2>Usuarios</h2>
            <table>
              <thead>
                <tr>
                  <th>Nombre</th>
                  <th>Correo</th>
                  <th>Rol</th>
                  <th>Estado</th>
                  <th>Expira</th>
                  <th>Cuenta</th>
                  <th>Rol</th>
                </tr>
              </thead>
              <tbody>{''.join(rows)}</tbody>
            </table>
          </section>

          <section class="panel">
            <h2>Auditoria reciente</h2>
            <ul>{log_items}</ul>
          </section>
        </main>
      </body>
    </html>
    """


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/", response_class=HTMLResponse)
def dashboard(as_user: int | None = Query(default=None), db: Session = Depends(get_db)):
    actor = get_actor_or_404(db, as_user)
    users = UserService.list_users(db)
    roles = UserService.list_roles(db)
    permissions = AuthorizationService.get_permissions(db, actor)
    logs = AuditService.list_recent(db)
    return HTMLResponse(render_dashboard(actor, users, roles, permissions, logs))


@app.get("/api/me", response_model=MeOut)
def api_me(as_user: int | None = Query(default=None), db: Session = Depends(get_db)):
    actor = get_actor_or_404(db, as_user)
    return {"user": actor, "role": actor.role, "permissions": AuthorizationService.get_permissions(db, actor)}


@app.get("/api/users", response_model=list[UserOut])
def api_users(as_user: int | None = Query(default=None), db: Session = Depends(get_db)):
    actor = get_actor_or_404(db, as_user)
    require_actor_permission(db, actor, "users", "view")
    return UserService.list_users(db)


@app.get("/api/audit-logs", response_model=list[AuditLogOut])
def api_audit_logs(as_user: int | None = Query(default=None), db: Session = Depends(get_db)):
    actor = get_actor_or_404(db, as_user)
    require_actor_permission(db, actor, "audit", "view")
    return AuditService.list_recent(db, limit=50)


@app.post("/ui/users")
def ui_create_user(
    actor_id: int = Form(...),
    full_name: str = Form(...),
    email: str = Form(...),
    role_id: int = Form(...),
    end_date: str = Form(default=""),
    db: Session = Depends(get_db),
):
    actor = get_actor_or_404(db, actor_id)
    require_actor_permission(db, actor, "users", "create")
    user = UserService.create_user(
        db,
        full_name=full_name,
        email=email,
        role_id=role_id,
        end_date=parse_end_date(end_date),
    )
    AuditService.log(
        db,
        event_type="user_created",
        actor_user_id=actor.id,
        target_user_id=user.id,
        action="create",
        resource="users",
        result="success",
    )
    return redirect_home(actor.id)


@app.post("/ui/users/{user_id}/status")
def ui_change_status(
    user_id: int,
    actor_id: int = Form(...),
    status: str = Form(...),
    db: Session = Depends(get_db),
):
    actor = get_actor_or_404(db, actor_id)
    target = UserService.get_user(db, user_id)
    if not target:
        raise HTTPException(status_code=404, detail="User not found")

    config = {
        "active": ("users", "activate", "user_activated"),
        "revoked": ("users", "revoke", "user_revoked"),
    }
    if status not in config:
        raise HTTPException(status_code=400, detail="Unsupported status")

    resource, action, event_type = config[status]
    if action == "activate" and target.status == "revoked":
        resource, action, event_type = ("users", "reactivate", "user_reactivated")

    require_actor_permission(db, actor, resource, action)
    updated = UserService.update_status(db, target, status)
    AuditService.log(
        db,
        event_type=event_type,
        actor_user_id=actor.id,
        target_user_id=updated.id,
        action=action,
        resource=resource,
        result="success",
    )
    return redirect_home(actor.id)


@app.post("/ui/users/{user_id}/role")
def ui_change_role(
    user_id: int,
    actor_id: int = Form(...),
    role_id: int = Form(...),
    db: Session = Depends(get_db),
):
    actor = get_actor_or_404(db, actor_id)
    target = UserService.get_user(db, user_id)
    if not target:
        raise HTTPException(status_code=404, detail="User not found")

    require_actor_permission(db, actor, "users", "change_role")
    updated = UserService.change_role(db, target, role_id)
    AuditService.log(
        db,
        event_type="role_changed",
        actor_user_id=actor.id,
        target_user_id=updated.id,
        action="change_role",
        resource="users",
        result="success",
        metadata={"role_id": role_id},
    )
    return redirect_home(actor.id)
