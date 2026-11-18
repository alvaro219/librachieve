import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useEffect, useState, type ReactNode } from "react";
import { useTranslation } from "react-i18next";
import { Link } from "react-router-dom";

import { friendsApi, usersApi } from "../api/endpoints";
import type { Friend, UserSummary } from "../api/types";
import { useAuth } from "../auth/AuthContext";
import Avatar from "../components/Avatar";
import FriendButton, { relationTo, useFriendActions, useFriends } from "../components/FriendButton";
import PlatformIcon from "../components/PlatformIcon";
import { formatDate } from "../lib/labels";

function SteamFriends() {
  const { t } = useTranslation();
  const queryClient = useQueryClient();
  const found = useQuery({
    queryKey: ["steamFriends"], // not under "friends": friend actions must not re-ask Steam
    queryFn: friendsApi.steam,
    staleTime: 10 * 60_000, // each load asks Steam
    retry: false,
  });
  const addAll = useMutation({
    mutationFn: friendsApi.addSteam,
    onSuccess: () => void queryClient.invalidateQueries({ queryKey: ["friends"] }),
  });
  // The buttons read the live friends list, so count from it too
  const friends = useFriends();
  const missing =
    found.data?.filter((u) => relationTo(friends.data, u.id).state !== "friends").length ?? 0;

  return (
    <section className="card space-y-3">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h2 className="flex items-center gap-2 font-semibold">
          <PlatformIcon platform="steam" title="" className="h-5 w-5" />
          {t("friendsPage.steamTitle")}
        </h2>
        {missing > 0 && (
          <button
            className="btn-primary px-3 py-1.5"
            disabled={addAll.isPending}
            onClick={() => addAll.mutate()}
          >
            {t("friendsPage.addAll", { count: missing })}
          </button>
        )}
      </div>
      {found.isLoading && <p className="text-sm text-slate-400">{t("friendsPage.askingSteam")}</p>}
      {found.error && <p className="text-sm text-amber-300">{found.error.message}</p>}
      {addAll.error && <p className="text-sm text-red-400">{addAll.error.message}</p>}
      {found.data &&
        (found.data.length ? (
          <ul className="divide-y divide-slate-800">
            {found.data.map((u) => (
              <UserRow
                key={u.id}
                user={u}
                actions={<FriendButton userId={u.id} username={u.username} />}
              />
            ))}
          </ul>
        ) : (
          <p className="text-sm text-slate-400">
            {t("friendsPage.noneOnSteam")}
          </p>
        ))}
      <p className="text-xs text-slate-500">
        {t("friendsPage.steamNote")}
      </p>
    </section>
  );
}

function UserRow({
  user,
  detail,
  actions,
}: {
  user: UserSummary;
  detail?: string;
  actions: ReactNode;
}) {
  const { t } = useTranslation();
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
          {[user.is_public ? null : t("friendsPage.privateProfile"), detail].filter(Boolean).join(" · ")}
        </p>
      </div>
      {actions}
    </li>
  );
}

function Search() {
  const { t } = useTranslation();
  const [input, setInput] = useState("");
  const [q, setQ] = useState("");
  useEffect(() => {
    const timer = setTimeout(() => setQ(input.trim()), 300);
    return () => clearTimeout(timer);
  }, [input]);

  const results = useQuery({
    queryKey: ["userSearch", q],
    queryFn: () => usersApi.search(q),
    enabled: q.length >= 2,
  });

  return (
    <section className="card space-y-3">
      <h2 className="font-semibold">{t("friendsPage.searchTitle")}</h2>
      <input
        className="input"
        placeholder={t("friendsPage.searchPlaceholder")}
        value={input}
        onChange={(e) => setInput(e.target.value)}
      />
      <p className="text-xs text-slate-500">
        {t("friendsPage.searchHint")}
      </p>
      {q.length >= 2 &&
        (results.isLoading ? (
          <p className="text-sm text-slate-400">{t("common.searching")}</p>
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
          <p className="text-sm text-slate-400">{t("friendsPage.noResults")}</p>
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
  const { user } = useAuth();
  const { t } = useTranslation();
  const friends = useFriends();
  const { accept, remove } = useFriendActions();
  const busy = accept.isPending || remove.isPending;
  const data = friends.data ?? { friends: [], incoming: [], outgoing: [] };

  return (
    <div className="mx-auto max-w-3xl space-y-6">
      <h1 className="text-2xl font-bold">{t("nav.friends")}</h1>

      <FriendList title={t("friendsPage.incoming")} items={data.incoming}>
        {(f) => (
          <UserRow
            key={f.id}
            user={f.user}
            detail={t("friendsPage.since", { date: formatDate(f.created_at) })}
            actions={
              <span className="flex gap-2">
                <button
                  className="btn-primary px-3 py-1.5"
                  disabled={busy}
                  onClick={() => accept.mutate(f.id)}
                >
                  {t("friends.accept")}
                </button>
                <button
                  className="btn-secondary px-3 py-1.5"
                  disabled={busy}
                  onClick={() => remove.mutate(f.id)}
                >
                  {t("friends.reject")}
                </button>
              </span>
            }
          />
        )}
      </FriendList>

      <FriendList
        title={t("friendsPage.yourFriends")}
        items={data.friends}
        empty={
          friends.isLoading
            ? t("common.loading")
            : t("friendsPage.noFriends")
        }
      >
        {(f) => (
          <UserRow
            key={f.id}
            user={f.user}
            detail={
              f.accepted_at
                ? t("friendsPage.friendsSince", { date: formatDate(f.accepted_at) })
                : undefined
            }
            actions={
              <button
                className="btn-secondary px-3 py-1.5 text-xs"
                disabled={busy}
                onClick={() =>
                  confirm(t("friends.confirmRemove", { name: f.user.username })) && remove.mutate(f.id)
                }
              >
                {t("entry.remove")}
              </button>
            }
          />
        )}
      </FriendList>

      {user?.steam_id ? (
        <SteamFriends />
      ) : (
        <p className="text-sm text-slate-400">
          <Link to="/settings" className="text-indigo-400 hover:underline">
            {t("friendsPage.linkSteam")}
          </Link>{" "}
          {t("friendsPage.linkSteamHint")}
        </p>
      )}

      <Search />

      <FriendList title={t("friendsPage.outgoing")} items={data.outgoing}>
        {(f) => (
          <UserRow
            key={f.id}
            user={f.user}
            detail={t("friendsPage.sentOn", { date: formatDate(f.created_at) })}
            actions={
              <button
                className="btn-secondary px-3 py-1.5 text-xs"
                disabled={busy}
                onClick={() => remove.mutate(f.id)}
              >
                {t("common.cancel")}
              </button>
            }
          />
        )}
      </FriendList>
    </div>
  );
}
