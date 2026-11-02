import type { LibraryEntry } from "../api/types";
import { PLATFORM_LABELS, STATUS_LABELS, formatPlaytime } from "../lib/labels";

interface Props {
  entry: LibraryEntry;
  onClick?: () => void;
}

export default function GameCard({ entry, onClick }: Props) {
  const { game } = entry;
  return (
    <button
      type="button"
      onClick={onClick}
      disabled={!onClick}
      className="group flex flex-col overflow-hidden rounded-xl border border-slate-800 bg-slate-900 text-left transition enabled:hover:-translate-y-0.5 enabled:hover:border-indigo-500/60 disabled:cursor-default"
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
        <span className="absolute left-2 top-2 rounded-md bg-slate-950/80 px-2 py-0.5 text-xs text-slate-200">
          {PLATFORM_LABELS[entry.platform]}
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
      </div>
    </button>
  );
}
