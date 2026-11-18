import { useTranslation } from "react-i18next";

import type { Game } from "../api/types";
import i18n from "../i18n";
import { formatNumber } from "../lib/labels";

/** Metacritic-like bands. The number is always shown, so colour is never the only cue. */
export function scoreTone(score: number | null | undefined): string {
  if (score === null || score === undefined) return "border-slate-700 text-slate-500";
  if (score >= 75) return "border-emerald-500/60 bg-emerald-500/10 text-emerald-300";
  if (score >= 50) return "border-amber-500/60 bg-amber-500/10 text-amber-300";
  return "border-red-500/60 bg-red-500/10 text-red-300";
}

const votes = (n: number | null | undefined) =>
  n ? i18n.t("ratings.votes", { count: n, formatted: formatNumber(n) }) : i18n.t("ratings.noVotes");

function ScoreTile({
  label,
  score,
  detail,
  title,
}: {
  label: string;
  score: number | null | undefined;
  detail: string;
  title: string;
}) {
  const value = score === null || score === undefined ? null : Math.round(score);
  return (
    <div
      title={title}
      className={`flex min-w-[5.5rem] flex-1 flex-col items-center rounded-lg border px-2 py-2 ${scoreTone(value)}`}
    >
      <span className="text-[11px] uppercase tracking-wide text-slate-400">{label}</span>
      <span className="text-2xl font-bold tabular-nums">{value ?? "—"}</span>
      <span className="text-[11px] text-slate-500">{detail}</span>
    </div>
  );
}

/** Own score + Librachieve users + IGDB community + critics, like Playnite. */
export function RatingSummary({
  game,
  userRating,
  ownerLabel,
}: {
  game: Game;
  userRating: number | null;
  ownerLabel?: string;
}) {
  const { t } = useTranslation();
  const owner = ownerLabel ?? t("ratings.yourScore");
  return (
    <div className="flex flex-wrap gap-2">
      <ScoreTile
        label={owner}
        score={userRating}
        detail={t("ratings.outOf100")}
        title={`${owner} (0-100)`}
      />
      <ScoreTile
        label={t("ratings.users")}
        score={game.community_rating}
        detail={votes(game.community_rating_count)}
        title={t("ratings.usersHint")}
      />
      <ScoreTile
        label={t("ratings.community")}
        score={game.igdb_rating}
        detail={votes(game.igdb_rating_count)}
        title={t("ratings.communityHint")}
      />
      <ScoreTile
        label={t("ratings.critics")}
        score={game.critic_rating}
        detail={
          game.critic_rating_count
            ? t("ratings.reviews", { count: game.critic_rating_count })
            : t("ratings.noReviews")
        }
        title={t("ratings.criticsHint")}
      />
    </div>
  );
}

/** 0-100 slider + number field; null means "not rated". */
export function RatingInput({
  value,
  onChange,
}: {
  value: number | null;
  onChange: (value: number | null) => void;
}) {
  const { t } = useTranslation();
  const set = (raw: string) => {
    if (raw === "") return onChange(null);
    const n = Math.round(Number(raw));
    if (!Number.isNaN(n)) onChange(Math.min(100, Math.max(0, n)));
  };
  return (
    <div className="text-sm">
      <div className="mb-1 flex items-center justify-between">
        <label htmlFor="rating-number" className="text-slate-300">
          {t("ratings.yourRating")}
        </label>
        {value !== null && (
          <button
            type="button"
            onClick={() => onChange(null)}
            className="text-xs text-slate-400 hover:text-white"
          >
            {t("ratings.clear")}
          </button>
        )}
      </div>
      <div className="flex items-center gap-3">
        <input
          type="range"
          min={0}
          max={100}
          step={1}
          value={value ?? 50}
          onChange={(e) => set(e.target.value)}
          aria-label={t("ratings.sliderLabel")}
          className={`h-2 flex-1 cursor-pointer accent-indigo-500 ${value === null ? "opacity-40" : ""}`}
        />
        <input
          id="rating-number"
          className={`input w-20 text-center font-semibold tabular-nums ${scoreTone(value)}`}
          inputMode="numeric"
          placeholder="—"
          value={value ?? ""}
          onChange={(e) => set(e.target.value.replace(/[^0-9]/g, ""))}
        />
      </div>
      {value === null && (
        <p className="mt-1 text-xs text-slate-500">{t("ratings.unrated")}</p>
      )}
    </div>
  );
}
