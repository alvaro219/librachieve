import { useQuery } from "@tanstack/react-query";

import { usersApi } from "../api/endpoints";
import StatsView from "../components/StatsView";

export default function StatsPage() {
  const stats = useQuery({ queryKey: ["stats", "me"], queryFn: usersApi.myStats });

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">Estadísticas</h1>
      {stats.isLoading && <p className="text-slate-400">Calculando…</p>}
      {stats.error && <p className="text-red-400">{stats.error.message}</p>}
      {stats.data && <StatsView stats={stats.data} />}
    </div>
  );
}
