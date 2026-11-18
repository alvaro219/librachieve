import { keepPreviousData, useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { Link, Navigate } from "react-router-dom";

import { adminApi } from "../api/endpoints";
import type { AdminUser } from "../api/types";
import { useAuth } from "../auth/AuthContext";
import Avatar from "../components/Avatar";
import PlatformIcon from "../components/PlatformIcon";
import { formatDate, formatNumber } from "../lib/labels";

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
        {value === undefined ? "—" : formatNumber(value)}
      </p>
    </div>
  );
}

function UserActions({ user, self }: { user: AdminUser; self: boolean }) {
  const { t } = useTranslation();
  const queryClient = useQueryClient();
  const onSuccess = () => {
    void queryClient.invalidateQueries({ queryKey: ["admin"] });
  };
  const setRole = useMutation({
    mutationFn: () => adminApi.setRole(user.id, user.role === "admin" ? "user" : "admin"),
    onSuccess,
  });
  const remove = useMutation({ mutationFn: () => adminApi.deleteUser(user.id), onSuccess });
  if (self) return <span className="block text-right text-xs text-slate-500">{t("admin.you")}</span>;
  const busy = setRole.isPending || remove.isPending;

  return (
    <span className="flex justify-end gap-2">
      <button
        className="btn-secondary px-2.5 py-1 text-xs"
        disabled={busy}
        onClick={() =>
          confirm(
            user.role === "admin"
              ? t("admin.confirmDemote", { name: user.username })
              : t("admin.confirmPromote", { name: user.username }),
          ) && setRole.mutate()
        }
      >
        {user.role === "admin" ? t("admin.demote") : t("admin.promote")}
      </button>
      <button
        className="btn-danger px-2.5 py-1 text-xs"
        disabled={busy}
        onClick={() =>
          confirm(t("admin.confirmDelete", { name: user.username })) && remove.mutate()
        }
      >
        {t("admin.delete")}
      </button>
    </span>
  );
}

export default function AdminPage() {
  const { user } = useAuth();
  const { t } = useTranslation();
  const [input, setInput] = useState("");
  const [q, setQ] = useState("");
  const [offset, setOffset] = useState(0);
  useEffect(() => {
    const timer = setTimeout(() => {
      setQ(input.trim());
      setOffset(0);
    }, 300);
    return () => clearTimeout(timer);
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
      <h1 className="text-2xl font-bold">{t("nav.admin")}</h1>

      <div className="grid grid-cols-2 gap-3 sm:grid-cols-4 lg:grid-cols-7">
        <Stat label={t("admin.stats.users")} value={o?.users} />
        <Stat label={t("admin.stats.active")} value={o?.active_users_30d} />
        <Stat label={t("admin.stats.steam")} value={o?.steam_users} />
        <Stat label={t("stats.games")} value={o?.games} />
        <Stat label={t("admin.stats.noMetadata")} value={o?.games_without_metadata} warn />
        <Stat label={t("admin.stats.inLibraries")} value={o?.library_entries} />
        <Stat label={t("admin.stats.errors")} value={o?.failed_jobs_24h} warn />
      </div>

      <section className="card flex flex-wrap items-center justify-between gap-3">
        <div>
          <h2 className="font-semibold">{t("admin.igdb.title")}</h2>
          <p className="text-sm text-slate-400">
            {t("admin.igdb.hint")}
          </p>
        </div>
        <span className="flex items-center gap-3">
          {reenrich.data && (
            <span className="text-sm text-emerald-400">
              ✓ {t("admin.igdb.queued", { count: reenrich.data.enqueued })}
            </span>
          )}
          <button
            className="btn-secondary"
            disabled={reenrich.isPending || !o?.games_without_metadata}
            onClick={() => reenrich.mutate()}
          >
            {t("admin.igdb.run")}
          </button>
        </span>
      </section>

      <section className="card space-y-4">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <h2 className="font-semibold">
            {t("admin.stats.users")} <span className="text-slate-500">({total})</span>
          </h2>
          <input
            className="input sm:max-w-xs"
            placeholder={t("admin.search")}
            value={input}
            onChange={(e) => setInput(e.target.value)}
          />
        </div>
        {users.error && <p className="text-sm text-red-400">{users.error.message}</p>}
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead className="text-slate-400">
              <tr>
                <th className="pb-2 font-medium">{t("admin.user")}</th>
                <th className="pb-2 font-medium">{t("auth.email")}</th>
                <th className="pb-2 text-right font-medium">{t("stats.games")}</th>
                <th className="pb-2 pl-6 font-medium">{t("admin.joined")}</th>
                <th className="pb-2 pl-4 font-medium">{t("admin.lastSeen")}</th>
                <th className="pb-2" />
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800">
              {users.data?.items.map((u) => (
                <tr key={u.id}>
                  <td className="py-2 pr-4">
                    <span className="flex items-center gap-2">
                      <Avatar user={u} className="h-7 w-7 text-xs" />
                      <Link to={`/u/${u.username}`} className="font-medium hover:underline">
                        {u.username}
                      </Link>
                      {u.steam_id && (
                        <PlatformIcon
                          platform="steam"
                          title={t("admin.steamLinked")}
                          className="h-3.5 w-3.5"
                        />
                      )}
                      {u.role === "admin" && (
                        <span className="rounded bg-indigo-500/20 px-1.5 text-xs text-indigo-300">
                          admin
                        </span>
                      )}
                      {!u.is_public && <span className="text-xs text-slate-500">{t("admin.private")}</span>}
                    </span>
                  </td>
                  <td className="pr-4 text-slate-400">{u.email ?? "—"}</td>
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
              {t("admin.range", { from: offset + 1, to: Math.min(offset + PAGE, total), total })}
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
