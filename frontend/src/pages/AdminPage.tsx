import { keepPreviousData, useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useEffect, useState } from "react";
import { Link, Navigate } from "react-router-dom";

import { adminApi } from "../api/endpoints";
import type { AdminUser } from "../api/types";
import { useAuth } from "../auth/AuthContext";
import Avatar from "../components/Avatar";
import PlatformIcon from "../components/PlatformIcon";
import { formatDate } from "../lib/labels";

const PAGE = 50;

function Stat({
  label,
  value,
  warn,
}: {
  label: string;
  value: number | undefined;
  warn?: boolean;
}) {
  return (
    <div className="card p-4">
      <p className="text-xs uppercase tracking-wide text-slate-400">{label}</p>
      <p className={`text-2xl font-bold tabular-nums ${warn && value ? "text-amber-300" : ""}`}>
        {value?.toLocaleString("es-ES") ?? "—"}
      </p>
    </div>
  );
}

function UserActions({ user, self }: { user: AdminUser; self: boolean }) {
  const queryClient = useQueryClient();
  const onSuccess = () => {
    void queryClient.invalidateQueries({ queryKey: ["admin"] });
  };
  const setRole = useMutation({
    mutationFn: () => adminApi.setRole(user.id, user.role === "admin" ? "user" : "admin"),
    onSuccess,
  });
  const remove = useMutation({ mutationFn: () => adminApi.deleteUser(user.id), onSuccess });
  if (self) return <span className="block text-right text-xs text-slate-500">Tú</span>;
  const busy = setRole.isPending || remove.isPending;

  return (
    <span className="flex justify-end gap-2">
      <button
        className="btn-secondary px-2.5 py-1 text-xs"
        disabled={busy}
        onClick={() =>
          confirm(
            user.role === "admin"
              ? `¿Quitar el rol de administrador a ${user.username}?`
              : `¿Hacer administrador a ${user.username}? Podrá gestionar todas las cuentas.`,
          ) && setRole.mutate()
        }
      >
        {user.role === "admin" ? "Quitar admin" : "Hacer admin"}
      </button>
      <button
        className="btn-danger px-2.5 py-1 text-xs"
        disabled={busy}
        onClick={() =>
          confirm(
            `¿Eliminar la cuenta de ${user.username}? Se borran su biblioteca, notas y amigos. ` +
              "No se puede deshacer.",
          ) && remove.mutate()
        }
      >
        Eliminar
      </button>
    </span>
  );
}

export default function AdminPage() {
  const { user } = useAuth();
  const [input, setInput] = useState("");
  const [q, setQ] = useState("");
  const [offset, setOffset] = useState(0);
  useEffect(() => {
    const t = setTimeout(() => {
      setQ(input.trim());
      setOffset(0);
    }, 300);
    return () => clearTimeout(t);
  }, [input]);

  const isAdmin = user?.role === "admin";
  const overview = useQuery({
    queryKey: ["admin", "overview"],
    queryFn: adminApi.overview,
    enabled: isAdmin,
  });
  const users = useQuery({
    queryKey: ["admin", "users", q, offset],
    queryFn: () => adminApi.users(q, offset),
    enabled: isAdmin,
    placeholderData: keepPreviousData,
  });
  const reenrich = useMutation({ mutationFn: adminApi.reenrich });

  if (!isAdmin) return <Navigate to="/" replace />;
  const o = overview.data;
  const total = users.data?.total ?? 0;

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">Administración</h1>

      <div className="grid grid-cols-2 gap-3 sm:grid-cols-4 lg:grid-cols-7">
        <Stat label="Usuarios" value={o?.users} />
        <Stat label="Activos 30 días" value={o?.active_users_30d} />
        <Stat label="Con Steam" value={o?.steam_users} />
        <Stat label="Juegos" value={o?.games} />
        <Stat label="Sin datos IGDB" value={o?.games_without_metadata} warn />
        <Stat label="En bibliotecas" value={o?.library_entries} />
        <Stat label="Errores 24 h" value={o?.failed_jobs_24h} warn />
      </div>

      <section className="card flex flex-wrap items-center justify-between gap-3">
        <div>
          <h2 className="font-semibold">Metadatos de IGDB</h2>
          <p className="text-sm text-slate-400">
            Vuelve a buscar en IGDB los juegos que todavía no tienen portada ni datos.
          </p>
        </div>
        <span className="flex items-center gap-3">
          {reenrich.data && (
            <span className="text-sm text-emerald-400">
              ✓ {reenrich.data.enqueued} juegos en cola
            </span>
          )}
          <button
            className="btn-secondary"
            disabled={reenrich.isPending || !o?.games_without_metadata}
            onClick={() => reenrich.mutate()}
          >
            Volver a buscar
          </button>
        </span>
      </section>

      <section className="card space-y-4">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <h2 className="font-semibold">
            Usuarios <span className="text-slate-500">({total})</span>
          </h2>
          <input
            className="input sm:max-w-xs"
            placeholder="Buscar por nombre o email…"
            value={input}
            onChange={(e) => setInput(e.target.value)}
          />
        </div>
        {users.error && <p className="text-sm text-red-400">{users.error.message}</p>}
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead className="text-slate-400">
              <tr>
                <th className="pb-2 font-medium">Usuario</th>
                <th className="pb-2 font-medium">Email</th>
                <th className="pb-2 text-right font-medium">Juegos</th>
                <th className="pb-2 pl-6 font-medium">Alta</th>
                <th className="pb-2 pl-4 font-medium">Última visita</th>
                <th className="pb-2" />
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800">
              {users.data?.items.map((u) => (
                <tr key={u.id}>
                  <td className="py-2">
                    <span className="flex items-center gap-2">
                      <Avatar user={u} className="h-7 w-7 text-xs" />
                      <Link to={`/u/${u.username}`} className="font-medium hover:underline">
                        {u.username}
                      </Link>
                      {u.steam_id && (
                        <PlatformIcon
                          platform="steam"
                          title="Steam vinculado"
                          className="h-3.5 w-3.5"
                        />
                      )}
                      {u.role === "admin" && (
                        <span className="rounded bg-indigo-500/20 px-1.5 text-xs text-indigo-300">
                          admin
                        </span>
                      )}
                      {!u.is_public && <span className="text-xs text-slate-500">privado</span>}
                    </span>
                  </td>
                  <td className="text-slate-400">{u.email ?? "—"}</td>
                  <td className="text-right tabular-nums">{u.games}</td>
                  <td className="whitespace-nowrap pl-6 text-slate-400">{formatDate(u.created_at)}</td>
                  <td className="whitespace-nowrap pl-4 text-slate-400">
                    {u.last_seen_at ? formatDate(u.last_seen_at) : "—"}
                  </td>
                  <td className="py-1.5 pl-3">
                    <UserActions user={u} self={u.id === user.id} />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        {total > PAGE && (
          <div className="flex items-center justify-end gap-3 text-sm">
            <span className="text-slate-400">
              {offset + 1}–{Math.min(offset + PAGE, total)} de {total}
            </span>
            <button
              className="btn-secondary px-3 py-1"
              disabled={offset === 0}
              onClick={() => setOffset(offset - PAGE)}
            >
              ←
            </button>
            <button
              className="btn-secondary px-3 py-1"
              disabled={offset + PAGE >= total}
              onClick={() => setOffset(offset + PAGE)}
            >
              →
            </button>
          </div>
        )}
      </section>
    </div>
  );
}
