import { useQuery } from "@tanstack/react-query";
import { useEffect, useState, type ReactNode } from "react";
import { Link } from "react-router-dom";

import { usersApi } from "../api/endpoints";
import type { Friend, UserSummary } from "../api/types";
import Avatar from "../components/Avatar";
import FriendButton, { useFriendActions, useFriends } from "../components/FriendButton";
import { formatDate } from "../lib/labels";

function UserRow({
  user,
  detail,
  actions,
}: {
  user: UserSummary;
  detail?: string;
  actions: ReactNode;
}) {
  return (
    <li className="flex items-center gap-3 py-3">
      <Avatar user={user} />
      <div className="min-w-0 flex-1">
        {user.is_public ? (
          <Link
            to={`/u/${user.username}`}
            className="font-medium hover:text-indigo-300 hover:underline"
          >
            {user.username}
          </Link>
        ) : (
          <span className="font-medium">{user.username}</span>
        )}
        <p className="text-xs text-slate-500">
          {[user.is_public ? null : "Perfil privado", detail].filter(Boolean).join(" · ")}
        </p>
      </div>
      {actions}
    </li>
  );
}

function Search() {
  const [input, setInput] = useState("");
  const [q, setQ] = useState("");
  useEffect(() => {
    const t = setTimeout(() => setQ(input.trim()), 300);
    return () => clearTimeout(t);
  }, [input]);

  const results = useQuery({
    queryKey: ["userSearch", q],
    queryFn: () => usersApi.search(q),
    enabled: q.length >= 2,
  });

  return (
    <section className="card space-y-3">
      <h2 className="font-semibold">Buscar usuarios</h2>
      <input
        className="input"
        placeholder="Nombre de usuario…"
        value={input}
        onChange={(e) => setInput(e.target.value)}
      />
      <p className="text-xs text-slate-500">
        Los perfiles privados solo aparecen si escribes su nombre exacto.
      </p>
      {q.length >= 2 &&
        (results.isLoading ? (
          <p className="text-sm text-slate-400">Buscando…</p>
        ) : results.data?.length ? (
          <ul className="divide-y divide-slate-800">
            {results.data.map((u) => (
              <UserRow
                key={u.id}
                user={u}
                actions={<FriendButton userId={u.id} username={u.username} />}
              />
            ))}
          </ul>
        ) : (
          <p className="text-sm text-slate-400">Nadie con ese nombre.</p>
        ))}
    </section>
  );
}

function FriendList({
  title,
  items,
  empty,
  children,
}: {
  title: string;
  items: Friend[];
  empty?: string;
  children: (f: Friend) => ReactNode;
}) {
  if (!items.length && !empty) return null;
  return (
    <section className="card">
      <h2 className="font-semibold">
        {title} {items.length > 0 && <span className="text-slate-500">({items.length})</span>}
      </h2>
      {items.length ? (
        <ul className="divide-y divide-slate-800">{items.map(children)}</ul>
      ) : (
        <p className="mt-2 text-sm text-slate-400">{empty}</p>
      )}
    </section>
  );
}

export default function FriendsPage() {
  const friends = useFriends();
  const { accept, remove } = useFriendActions();
  const busy = accept.isPending || remove.isPending;
  const data = friends.data ?? { friends: [], incoming: [], outgoing: [] };

  return (
    <div className="mx-auto max-w-3xl space-y-6">
      <h1 className="text-2xl font-bold">Amigos</h1>

      <FriendList title="Solicitudes recibidas" items={data.incoming}>
        {(f) => (
          <UserRow
            key={f.id}
            user={f.user}
            detail={`desde el ${formatDate(f.created_at)}`}
            actions={
              <span className="flex gap-2">
                <button
                  className="btn-primary px-3 py-1.5"
                  disabled={busy}
                  onClick={() => accept.mutate(f.id)}
                >
                  Aceptar
                </button>
                <button
                  className="btn-secondary px-3 py-1.5"
                  disabled={busy}
                  onClick={() => remove.mutate(f.id)}
                >
                  Rechazar
                </button>
              </span>
            }
          />
        )}
      </FriendList>

      <FriendList
        title="Tus amigos"
        items={data.friends}
        empty={
          friends.isLoading
            ? "Cargando…"
            : "Todavía no tienes amigos. Búscalos abajo por su nombre."
        }
      >
        {(f) => (
          <UserRow
            key={f.id}
            user={f.user}
            detail={f.accepted_at ? `amigos desde el ${formatDate(f.accepted_at)}` : undefined}
            actions={
              <button
                className="btn-secondary px-3 py-1.5 text-xs"
                disabled={busy}
                onClick={() =>
                  confirm(`¿Quitar a ${f.user.username} de tus amigos?`) && remove.mutate(f.id)
                }
              >
                Quitar
              </button>
            }
          />
        )}
      </FriendList>

      <Search />

      <FriendList title="Solicitudes enviadas" items={data.outgoing}>
        {(f) => (
          <UserRow
            key={f.id}
            user={f.user}
            detail={`enviada el ${formatDate(f.created_at)}`}
            actions={
              <button
                className="btn-secondary px-3 py-1.5 text-xs"
                disabled={busy}
                onClick={() => remove.mutate(f.id)}
              >
                Cancelar
              </button>
            }
          />
        )}
      </FriendList>
    </div>
  );
}
