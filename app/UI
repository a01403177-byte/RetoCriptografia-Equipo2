import React, { useMemo, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";

export default function IdentityDemoUI() {
  const [baseUrl, setBaseUrl] = useState("http://127.0.0.1:8000");
  const [token, setToken] = useState("");

  const [health, setHealth] = useState(null);
  const [me, setMe] = useState(null);
  const [users, setUsers] = useState([]);
  const [auditLogs, setAuditLogs] = useState([]);
  const [loading, setLoading] = useState({});
  const [message, setMessage] = useState("");

  const [newUser, setNewUser] = useState({
    email: "",
    full_name: "",
    user_type: "internal",
    role_id: 1,
    end_date: "",
  });

  const headers = useMemo(() => {
    const base = { "Content-Type": "application/json" };
    if (token.trim()) base.Authorization = `Bearer ${token.trim()}`;
    return base;
  }, [token]);

  const callApi = async (path, options = {}) => {
    const response = await fetch(`${baseUrl}${path}`, {
      ...options,
      headers: {
        ...headers,
        ...(options.headers || {}),
      },
    });

    const text = await response.text();
    let data = null;
    try {
      data = text ? JSON.parse(text) : null;
    } catch {
      data = text;
    }

    if (!response.ok) {
      throw new Error(
        typeof data === "object" && data?.detail
          ? data.detail
          : `Error ${response.status}`
      );
    }

    return data;
  };

  const withLoading = async (key, fn) => {
    setLoading((prev) => ({ ...prev, [key]: true }));
    setMessage("");
    try {
      await fn();
    } catch (error) {
      setMessage(error.message || "Ocurrió un error");
    } finally {
      setLoading((prev) => ({ ...prev, [key]: false }));
    }
  };

  const checkHealth = () =>
    withLoading("health", async () => {
      const data = await callApi("/health");
      setHealth(data);
      setMessage("Health check correcto");
    });

  const fetchMe = () =>
    withLoading("me", async () => {
      const data = await callApi("/api/me");
      setMe(data);
      setMessage("Sesión validada correctamente");
    });

  const fetchUsers = () =>
    withLoading("users", async () => {
      const data = await callApi("/api/users");
      setUsers(Array.isArray(data) ? data : []);
      setMessage("Usuarios cargados");
    });

  const fetchAuditLogs = () =>
    withLoading("audit", async () => {
      const data = await callApi("/api/audit-logs?limit=20");
      setAuditLogs(Array.isArray(data) ? data : []);
      setMessage("Logs de auditoría cargados");
    });

  const createUser = () =>
    withLoading("createUser", async () => {
      const payload = {
        ...newUser,
        role_id: Number(newUser.role_id),
        end_date: newUser.end_date ? new Date(newUser.end_date).toISOString() : null,
      };

      const data = await callApi("/api/users", {
        method: "POST",
        body: JSON.stringify(payload),
      });

      setMessage(`Usuario creado: ${data.email}`);
      setNewUser({
        email: "",
        full_name: "",
        user_type: "internal",
        role_id: 1,
        end_date: "",
      });
      await fetchUsers();
    });

  return (
    <div className="min-h-screen bg-slate-50 p-6">
      <div className="mx-auto max-w-6xl space-y-6">
        <div className="rounded-3xl bg-white p-6 shadow-sm border">
          <h1 className="text-3xl font-semibold tracking-tight">Demo UI - Gestor de Identidades</h1>
          <p className="mt-2 text-sm text-slate-600">
            Interfaz básica para comprobar que tu API funciona con health check, autenticación,
            usuarios y auditoría.
          </p>
        </div>

        <Card className="rounded-3xl shadow-sm">
          <CardHeader>
            <CardTitle>Configuración</CardTitle>
          </CardHeader>
          <CardContent className="grid gap-4 md:grid-cols-2">
            <div className="space-y-2">
              <Label>Base URL del backend</Label>
              <Input
                value={baseUrl}
                onChange={(e) => setBaseUrl(e.target.value)}
                placeholder="http://127.0.0.1:8000"
              />
            </div>
            <div className="space-y-2">
              <Label>Bearer token</Label>
              <Input
                value={token}
                onChange={(e) => setToken(e.target.value)}
                placeholder="Pega aquí tu JWT"
              />
            </div>
          </CardContent>
        </Card>

        <div className="grid gap-6 lg:grid-cols-2">
          <Card className="rounded-3xl shadow-sm">
            <CardHeader>
              <CardTitle>Pruebas rápidas</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              <div className="flex flex-wrap gap-2">
                <Button onClick={checkHealth} disabled={loading.health}>Probar /health</Button>
                <Button variant="outline" onClick={fetchMe} disabled={loading.me}>Probar /api/me</Button>
                <Button variant="outline" onClick={fetchUsers} disabled={loading.users}>Listar usuarios</Button>
                <Button variant="outline" onClick={fetchAuditLogs} disabled={loading.audit}>Ver auditoría</Button>
              </div>

              {message && (
                <div className="rounded-2xl border bg-slate-50 p-3 text-sm text-slate-700">
                  {message}
                </div>
              )}

              <div className="rounded-2xl border p-4">
                <p className="text-sm font-medium">Estado del servicio</p>
                <p className="mt-2 text-sm text-slate-600">
                  {health ? JSON.stringify(health) : "Aún no se ha probado /health"}
                </p>
              </div>
            </CardContent>
          </Card>

          <Card className="rounded-3xl shadow-sm">
            <CardHeader>
              <CardTitle>Usuario autenticado</CardTitle>
            </CardHeader>
            <CardContent>
              {!me ? (
                <p className="text-sm text-slate-600">Todavía no se ha consultado /api/me.</p>
              ) : (
                <div className="space-y-3 text-sm">
                  <div><span className="font-medium">Nombre:</span> {me.user?.full_name}</div>
                  <div><span className="font-medium">Email:</span> {me.user?.email}</div>
                  <div><span className="font-medium">Status:</span> <Badge>{me.user?.status}</Badge></div>
                  <div><span className="font-medium">Rol:</span> {me.role?.name} ({me.role?.code})</div>
                  <div>
                    <span className="font-medium">Permisos:</span>
                    <div className="mt-2 flex flex-wrap gap-2">
                      {(me.permissions || []).map((perm, index) => (
                        <Badge key={index} variant="secondary">{perm.resource}:{perm.action}</Badge>
                      ))}
                    </div>
                  </div>
                </div>
              )}
            </CardContent>
          </Card>
        </div>

        <div className="grid gap-6 lg:grid-cols-2">
          <Card className="rounded-3xl shadow-sm">
            <CardHeader>
              <CardTitle>Crear usuario</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <Label>Email</Label>
                <Input
                  value={newUser.email}
                  onChange={(e) => setNewUser((prev) => ({ ...prev, email: e.target.value }))}
                  placeholder="nuevo@correo.com"
                />
              </div>

              <div className="space-y-2">
                <Label>Nombre completo</Label>
                <Input
                  value={newUser.full_name}
                  onChange={(e) => setNewUser((prev) => ({ ...prev, full_name: e.target.value }))}
                  placeholder="Nombre Apellido"
                />
              </div>

              <div className="grid gap-4 md:grid-cols-2">
                <div className="space-y-2">
                  <Label>Tipo de usuario</Label>
                  <select
                    className="w-full rounded-xl border px-3 py-2 text-sm"
                    value={newUser.user_type}
                    onChange={(e) => setNewUser((prev) => ({ ...prev, user_type: e.target.value }))}
                  >
                    <option value="internal">internal</option>
                    <option value="external">external</option>
                  </select>
                </div>

                <div className="space-y-2">
                  <Label>Role ID</Label>
                  <Input
                    type="number"
                    value={newUser.role_id}
                    onChange={(e) => setNewUser((prev) => ({ ...prev, role_id: e.target.value }))}
                  />
                </div>
              </div>

              <div className="space-y-2">
                <Label>Fecha de expiración (opcional)</Label>
                <Input
                  type="datetime-local"
                  value={newUser.end_date}
                  onChange={(e) => setNewUser((prev) => ({ ...prev, end_date: e.target.value }))}
                />
              </div>

              <Button onClick={createUser} disabled={loading.createUser} className="w-full">
                Crear usuario
              </Button>
            </CardContent>
          </Card>

          <Card className="rounded-3xl shadow-sm">
            <CardHeader>
              <CardTitle>Usuarios</CardTitle>
            </CardHeader>
            <CardContent>
              {users.length === 0 ? (
                <p className="text-sm text-slate-600">No hay usuarios cargados todavía.</p>
              ) : (
                <div className="space-y-3">
                  {users.map((user) => (
                    <div key={user.id} className="rounded-2xl border p-4 text-sm">
                      <div className="flex items-start justify-between gap-4">
                        <div>
                          <p className="font-medium">{user.full_name}</p>
                          <p className="text-slate-600">{user.email}</p>
                        </div>
                        <Badge>{user.status}</Badge>
                      </div>
                      <div className="mt-3 grid gap-1 text-slate-600">
                        <p>ID: {user.id}</p>
                        <p>Tipo: {user.user_type}</p>
                        <p>Role ID: {user.role_id}</p>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </div>

        <Card className="rounded-3xl shadow-sm">
          <CardHeader>
            <CardTitle>Últimos logs de auditoría</CardTitle>
          </CardHeader>
          <CardContent>
            {auditLogs.length === 0 ? (
              <p className="text-sm text-slate-600">No se han cargado logs todavía.</p>
            ) : (
              <div className="space-y-3">
                {auditLogs.map((log) => (
                  <div key={log.id} className="rounded-2xl border p-4 text-sm">
                    <div className="flex flex-wrap items-center gap-2">
                      <Badge variant="secondary">{log.event_type}</Badge>
                      <Badge>{log.result}</Badge>
                    </div>
                    <div className="mt-2 text-slate-600">
                      <p>Acción: {log.action}</p>
                      <p>Recurso: {log.resource || "-"}</p>
                      <p>Actor: {log.actor_user_id ?? "-"}</p>
                      <p>Target: {log.target_user_id ?? "-"}</p>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
