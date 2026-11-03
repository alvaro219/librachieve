import type { LibraryEntry } from "../api/types";
import { STATUS_LABELS, formatPlaytime } from "../lib/labels";
import PlatformIcon from "./PlatformIcon";
import { scoreTone } from "./Ratings";

interface Props {
  entry: LibraryEntry;
  onClick?: () => void;
  /** Shows a star toggle on the cover (own library only). */
  onToggleFavorite?: () => void;
}

export default function GameCard({ entry, onClick, onToggleFavorite }: Props) {
  const { game } = entry;
  return (
    <div className="group relative flex">
    <button
      type="button"
      onClick={onClick}
      disabled={!onClick}
      className="flex w-full flex-col overflow-hidden rounded-xl border border-slate-800 bg-slate-900 text-left transition enabled:hover:-translate-y-0.5 enabled:hover:border-indigo-500/60 disabled:cursor-default"
    >
      <div className="relative aspect-[3/4] w-full bg-slate-800">
        {game.cover_url ? (
          <img
            src={game.cover_url}
            alt=""
            loading="lazy"
            className="h-full w-full object-cover"
          />
        ) : (
          <div className="flex h-full items-center justify-center p-4 text-center text-sm font-semibold text-slate-400">
            {game.title}
          </div>
        )}
        {entry.user_rating !== null && (
          <span
            title={`Tu nota: ${entry.user_rating}`}
            className={`absolute bottom-2 right-2 rounded-md border bg-slate-950/85 px-1.5 py-0.5 text-sm font-bold tabular-nums ${scoreTone(entry.user_rating)}`}
          >
            {entry.user_rating}
          </span>
        )}
        <span className="absolute left-2 top-2 flex h-8 w-8 items-center justify-center rounded-full bg-slate-950/80 text-slate-100">
          <PlatformIcon platform={entry.platform} className="h-[18px] w-[18px]" />
        </span>
      </div>
      <div className="flex flex-1 flex-col gap-1 p-3">
        <h3 className="line-clamp-2 text-sm font-semibold text-slate-100">{game.title}</h3>
        <div className="mt-auto flex items-center justify-between text-xs text-slate-400">
          <span>
            {entry.status === "other" && entry.custom_folder
              ? entry.custom_folder
              : STATUS_LABELS[entry.status]}
          </span>
          <span>{formatPlaytime(entry.playtime_minutes)}</span>
        </div>
        {entry.achievements_total > 0 && (
          <div
            className="mt-1"
            title={`${entry.achievements_unlocked} de ${entry.achievements_total} logros`}
          >
            <div className="mb-1 flex justify-between text-[11px] text-slate-400">
              <span>🏆 {entry.achievements_unlocked}/{entry.achievements_total}</span>
              {entry.achievements_unlocked === entry.achievements_total && (
                <span className="font-semibold text-amber-300">100 %</span>
              )}
            </div>
            <div className="h-1 rounded-full bg-slate-800">
              <div
                className="h-1 rounded-full bg-series-1"
                style={{
                  width: `${(entry.achievements_unlocked / entry.achievements_total) * 100}%`,
                }}
              />
            </div>
          </div>
        )}
      </div>
    </button>
    {onToggleFavorite ? (
      <button
        type="button"
        onClick={onToggleFavorite}
        aria-pressed={entry.is_favorite}
        title={entry.is_favorite ? "Quitar de favoritos" : "Añadir a favoritos"}
        className={`absolute right-2 top-2 flex h-8 w-8 items-center justify-center rounded-full bg-slate-950/80 text-lg leading-none transition hover:scale-110 ${
          entry.is_favorite ? "text-amber-300" : "text-slate-400 opacity-0 group-hover:opacity-100 focus:opacity-100"
        }`}
      >
        {entry.is_favorite ? "★" : "☆"}
      </button>
    ) : (
      entry.is_favorite && (
        <span
          title="Favorito"
          className="absolute right-2 top-2 flex h-8 w-8 items-center justify-center rounded-full bg-slate-950/80 text-lg leading-none text-amber-300"
        >
          ★
        </span>
      )
    )}
    </div>
  );
}