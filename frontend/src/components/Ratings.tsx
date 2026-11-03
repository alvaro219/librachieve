import type { Game } from "../api/types";

/** Metacritic-like bands. The number is always shown, so colour is never the only cue. */
export function scoreTone(score: number | null | undefined): string {
  if (score === null || score === undefined) return "border-slate-700 text-slate-500";
  if (score >= 75) return "border-emerald-500/60 bg-emerald-500/10 text-emerald-300";
  if (score >= 50) return "border-amber-500/60 bg-amber-500/10 text-amber-300";
  return "border-red-500/60 bg-red-500/10 text-red-300";
}

const votes = (n: number | null | undefined) =>
  n ? `${n.toLocaleString("es-ES")} ${n === 1 ? "voto" : "votos"}` : "sin votos";

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
  ownerLabel = "Tu nota",
}: {
  game: Game;
  userRating: number | null;
  ownerLabel?: string;
}) {
  return (
    <div className="flex flex-wrap gap-2">
      <ScoreTile label={ownerLabel} score={userRating} detail="de 100" title={`${ownerLabel} (0-100)`} />
      <ScoreTile
        label="Usuarios"
        score={game.community_rating}
        detail={votes(game.community_rating_count)}
        title="Media de los usuarios de Librachieve"
      />
      <ScoreTile
        label="Comunidad"
        score={game.igdb_rating}
        detail={votes(game.igdb_rating_count)}
        title="Media de los usuarios de IGDB"
      />
      <ScoreTile
        label="Crítica"
        score={game.critic_rating}
        detail={game.critic_rating_count ? `${game.critic_rating_count} reseñas` : "sin reseñas"}
        title="Media de la crítica profesional (IGDB)"
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
  const set = (raw: string) => {
    if (raw === "") return onChange(null);
    const n = Math.round(Number(raw));
    if (!Number.isNaN(n)) onChange(Math.min(100, Math.max(0, n)));
  };
  return (
    <div className="text-sm">
      <div className="mb-1 flex items-center justify-between">
        <label htmlFor="rating-number" className="text-slate-300">
          Tu valoración
        </label>
        {value !== null && (
          <button
            type="button"
            onClick={() => onChange(null)}
            className="text-xs text-slate-400 hover:text-white"
          >
            Quitar nota
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
          aria-label="Tu valoración de 0 a 100"
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
        <p className="mt-1 text-xs text-slate-500">Sin valorar. Mueve la barra o escribe una nota.</p>
      )}
    </div>
  );
}
