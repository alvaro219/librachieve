import { useQuery } from "@tanstack/react-query";
import { useParams } from "react-router-dom";

import { usersApi } from "../api/endpoints";
import { useAuth } from "../auth/AuthContext";
import Avatar from "../components/Avatar";
import FriendButton from "../components/FriendButton";
import LibraryBrowser from "../components/LibraryBrowser";
import StatsView from "../components/StatsView";
import { formatDate } from "../lib/labels";

export default function ProfilePage() {
  const { username = "" } = useParams();
  const { user: me } = useAuth();
  const profile = useQuery({
    queryKey: ["profile", username],
    queryFn: () => usersApi.profile(username),
    retry: false,
  });
  const stats = useQuery({
    queryKey: ["stats", username],
    queryFn: () => usersApi.profileStats(username),
    enabled: profile.isSuccess,
  });

  if (profile.isLoading) return <p className="text-slate-400">Cargando perfil…</p>;
  if (profile.error) {
    return (
      <div className="card text-center text-slate-400">Este perfil no existe o es privado.</div>
    );
  }

  const user = profile.data!;
  return (
    <div className="space-y-8">
      <div className="flex flex-wrap items-center gap-4">
        <Avatar user={user} className="h-16 w-16 text-2xl" />
        <div className="flex-1">
          <h1 className="text-2xl font-bold">{user.username}</h1>
          <p className="text-sm text-slate-400">Miembro desde {formatDate(user.created_at)}</p>
        </div>
        {me && me.id !== user.id && <FriendButton userId={user.id} username={user.username} />}
      </div>
      {stats.data && <StatsView stats={stats.data} />}
      <LibraryBrowser username={user.username} />
    </div>
  );
}
