import { useQuery } from "@tanstack/react-query";
import { useParams } from "react-router-dom";

import { usersApi } from "../api/endpoints";
import LibraryBrowser from "../components/LibraryBrowser";
import StatsView from "../components/StatsView";
import { formatDate } from "../lib/labels";

export default function ProfilePage() {
  const { username = "" } = useParams();
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
      <div className="card text-center text-slate-400">
        Este perfil no existe o es privado.
      </div>
    );
  }

  const user = profile.data!;
  return (
    <div className="space-y-8">
      <div className="flex items-center gap-4">
        {user.avatar_url ? (
          <img src={user.avatar_url} alt="" className="h-16 w-16 rounded-full" />
        ) : (
          <div className="flex h-16 w-16 items-center justify-center rounded-full bg-indigo-600 text-2xl font-bold">
            {user.username[0]?.toUpperCase()}
          </div>
        )}
        <div>
          <h1 className="text-2xl font-bold">{user.username}</h1>
          <p className="text-sm text-slate-400">Miembro desde {formatDate(user.created_at)}</p>
        </div>
      </div>
      {stats.data && <StatsView stats={stats.data} />}
      <LibraryBrowser username={user.username} />
    </div>
  );
}
