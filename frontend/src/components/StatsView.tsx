import type { UserStats } from "../api/types";
import { PLATFORM_LABELS, STATUS_LABELS, STATUS_ORDER, formatPlaytime } from "../lib/labels";
import BarList from "./BarList";

function StatTile({ label, value, hint }: { label: string; value: string; hint?: string }) {
  return (
    <div className="card">
      <p className="text-sm text-slate-400">{label}</p>
      <p className="mt-1 text-3xl font-semibold tabular-nums text-slate-50">{value}</p>
      {hint && <p className="mt-1 text-xs text-slate-500">{hint}</p>}
    </div>
  );
}

export default function StatsView({ stats }: { stats: UserStats }) {
  const owned = stats.total_games - (stats.games_by_status.wishlist ?? 0);
  return (
    <div className="space-y-6">
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <StatTile label="Juegos" value={String(stats.total_games)} hint={`${owned} en propiedad`} />
        <StatTile
          label="Tiempo de juego"
          value={formatPlaytime(stats.total_playtime_minutes)}
          hint={`${Math.round(stats.total_playtime_minutes / 60)} horas en total`}
        />
        <StatTile
          label="Ratio de completados"
          value={`${Math.round(stats.completion_ratio * 100)} %`}
          hint={`${stats.completed_games} de ${owned} (sin contar deseados)`}
        />
        <StatTile label="Jugando ahora" value={String(stats.games_by_status.playing ?? 0)} />
        <StatTile
          label="Logros obtenidos"
          value={String(stats.achievements_unlocked)}
          hint={`de ${stats.achievements_total} disponibles`}
        />
        <StatTile
          label="Progreso de logros"
          value={`${stats.achievements_total ? Math.round((stats.achievements_unlocked / stats.achievements_total) * 100) : 0} %`}
          hint={`${stats.achievements_total - stats.achievements_unlocked} pendientes`}
        />
        <StatTile
          label="Juegos al 100 %"
          value={String(stats.perfect_games)}
          hint="Con todos los logros"
        />
      </div>

      <div className="grid items-start gap-6 lg:grid-cols-3">
        <section className="card">
          <h2 className="mb-4 font-semibold">Géneros más jugados (horas)</h2>
          <BarList
            emptyText="Aún no hay géneros: se rellenan desde IGDB al importar."
            data={stats.top_genres.map((g) => ({
              label: g.genre,
              value: g.playtime_minutes,
              display: formatPlaytime(g.playtime_minutes),
              detail: `${g.games} juegos`,
            }))}
          />
        </section>
        <section className="card">
          <h2 className="mb-4 font-semibold">Juegos por plataforma</h2>
          <BarList
            emptyText="Sin juegos todavía."
            data={stats.games_by_platform.map((p) => ({
              label: PLATFORM_LABELS[p.platform],
              value: p.games,
            }))}
          />
        </section>
        <section className="card">
          <h2 className="mb-4 font-semibold">Juegos por categoría</h2>
          <BarList
            emptyText="Sin juegos todavía."
            data={STATUS_ORDER.map((s) => ({
              label: STATUS_LABELS[s],
              value: stats.games_by_status[s] ?? 0,
            }))}
          />
        </section>
      </div>
    </div>
  );
}
