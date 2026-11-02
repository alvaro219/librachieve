import type { LibraryEntry } from "../api/types";
import { PLATFORM_LABELS, STATUS_LABELS, formatDate, formatPlaytime } from "../lib/labels";

export type GameTab = "details" | "achievements";

export function GameHeader({ entry }: { entry: LibraryEntry }) {
  const { game } = entry;
  return (
    <div className="mb-4 flex gap-4">
      {game.cover_url && (
        <img src={game.cover_url} alt="" className="h-32 w-24 shrink-0 rounded-lg object-cover" />
      )}
      <div className="space-y-1 text-sm text-slate-400">
        <p>
          {PLATFORM_LABELS[entry.platform]} · {STATUS_LABELS[entry.status]} ·{" "}
          {formatPlaytime(entry.playtime_minutes)}
        </p>
        {game.release_date && <p>Lanzamiento: {formatDate(game.release_date)}</p>}
        {game.genres.length > 0 && <p>{game.genres.join(" · ")}</p>}
        {entry.last_played_at && <p>Última partida: {formatDate(entry.last_played_at)}</p>}
      </div>
    </div>
  );
}

export function GameTabs({
  entry,
  tab,
  onChange,
}: {
  entry: LibraryEntry;
  tab: GameTab;
  onChange: (tab: GameTab) => void;
}) {
  const item = (value: GameTab, label: string) => (
    <button
      type="button"
      onClick={() => onChange(value)}
      className={`border-b-2 px-3 pb-2 text-sm transition ${
        tab === value
          ? "border-indigo-500 text-white"
          : "border-transparent text-slate-400 hover:text-slate-200"
      }`}
    >
      {label}
    </button>
  );
  return (
    <div className="mb-4 flex border-b border-slate-800">
      {item("details", "Detalles")}
      {item(
        "achievements",
        entry.achievements_total > 0
          ? `Logros (${entry.achievements_unlocked}/${entry.achievements_total})`
          : "Logros",
      )}
    </div>
  );
}
