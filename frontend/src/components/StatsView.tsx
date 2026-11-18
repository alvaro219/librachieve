import { useTranslation } from "react-i18next";

import type { UserStats } from "../api/types";
import {
  PLATFORM_LABELS,
  STATUS_LABELS,
  STATUS_ORDER,
  formatNumber,
  formatPlaytime,
  genreLabel,
} from "../lib/labels";
import BarList from "./BarList";
import PlatformIcon from "./PlatformIcon";

function StatTile({ label, value, hint }: { label: string; value: string; hint?: string }) {
  return (
    <div className="card p-4 sm:p-5">
      <p className="text-sm text-slate-400">{label}</p>
      <p className="mt-1 text-2xl sm:text-3xl font-semibold tabular-nums text-slate-50">{value}</p>
      {hint && <p className="mt-1 text-xs text-slate-500">{hint}</p>}
    </div>
  );
}

export default function StatsView({ stats }: { stats: UserStats }) {
  const { t } = useTranslation();
  const owned = stats.total_games - (stats.games_by_status.wishlist ?? 0);
  return (
    <div className="space-y-6">
      <div className="grid grid-cols-2 gap-3 sm:gap-4 lg:grid-cols-4">
        <StatTile
          label={t("stats.games")}
          value={formatNumber(stats.total_games)}
          hint={t("stats.owned", { count: owned })}
        />
        <StatTile
          label={t("stats.playtime")}
          value={formatPlaytime(stats.total_playtime_minutes)}
          hint={t("stats.hoursTotal", {
            count: Math.round(stats.total_playtime_minutes / 60),
            formatted: formatNumber(Math.round(stats.total_playtime_minutes / 60)),
          })}
        />
        <StatTile
          label={t("stats.completionRatio")}
          value={`${Math.round(stats.completion_ratio * 100)} %`}
          hint={t("stats.completedOf", { done: stats.completed_games, owned })}
        />
        <StatTile label={t("stats.playingNow")} value={String(stats.games_by_status.playing ?? 0)} />
        <StatTile
          label={t("stats.achievementsUnlocked")}
          value={formatNumber(stats.achievements_unlocked)}
          hint={t("stats.ofAvailable", { total: formatNumber(stats.achievements_total) })}
        />
        <StatTile
          label={t("stats.achievementProgress")}
          value={`${stats.achievements_total ? Math.round((stats.achievements_unlocked / stats.achievements_total) * 100) : 0} %`}
          hint={t("stats.remaining", {
            count: stats.achievements_total - stats.achievements_unlocked,
            formatted: formatNumber(stats.achievements_total - stats.achievements_unlocked),
          })}
        />
        <StatTile
          label={t("stats.perfectGames")}
          value={String(stats.perfect_games)}
          hint={t("stats.perfectHint")}
        />
      </div>

      <div className="grid items-start gap-6 lg:grid-cols-3">
        <section className="card">
          <h2 className="mb-4 font-semibold">{t("stats.topGenres")}</h2>
          <BarList
            emptyText={t("stats.noGenres")}
            data={stats.top_genres.map((g) => ({
              label: genreLabel(g.genre),
              value: g.playtime_minutes,
              display: formatPlaytime(g.playtime_minutes),
              detail: t("stats.gamesCount", { count: g.games }),
            }))}
          />
        </section>
        <section className="card">
          <h2 className="mb-4 font-semibold">{t("stats.byPlatform")}</h2>
          <BarList
            emptyText={t("stats.noGames")}
            data={stats.games_by_platform.map((p) => ({
              label: PLATFORM_LABELS[p.platform],
              icon: <PlatformIcon platform={p.platform} title="" className="h-4 w-4" />,
              value: p.games,
            }))}
          />
        </section>
        <section className="card">
          <h2 className="mb-4 font-semibold">{t("stats.byCategory")}</h2>
          <BarList
            emptyText={t("stats.noGames")}
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
