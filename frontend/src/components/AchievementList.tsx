import { useQuery } from "@tanstack/react-query";
import { useMemo, useState } from "react";

import { libraryApi } from "../api/endpoints";
import type { Achievement } from "../api/types";
import { formatDate } from "../lib/labels";

type Filter = "all" | "unlocked" | "locked";

function formatPercent(p: number): string {
  return `${p < 10 ? p.toFixed(1).replace(".", ",") : Math.round(p)} %`;
}

function AchievementRow({ a }: { a: Achievement }) {
  const [revealed, setRevealed] = useState(false);
  const concealed = a.hidden && !a.unlocked && !revealed;
  const icon = a.unlocked ? a.icon_url : (a.icon_locked_url ?? a.icon_url);
  const rare = a.global_percent !== null && a.global_percent < 10;

  return (
    <li className="flex items-center gap-3 rounded-lg p-2 hover:bg-slate-800/60">
      {icon ? (
        <img
          src={icon}
          alt=""
          loading="lazy"
          className={`h-10 w-10 shrink-0 rounded ${a.unlocked ? "" : "opacity-60"}`}
        />
      ) : (
        <div className="h-10 w-10 shrink-0 rounded bg-slate-800" />
      )}
      <div className="min-w-0 flex-1">
        <p className={`text-sm font-medium ${a.unlocked ? "text-slate-100" : "text-slate-300"}`}>
          {concealed ? "Logro oculto" : a.name}
          {rare && (
            <span className="ml-2 rounded bg-amber-500/15 px-1.5 py-0.5 text-[10px] font-semibold uppercase text-amber-300">
              Raro
            </span>
          )}
        </p>
        <p className="truncate text-xs text-slate-400">
          {concealed ? (
            <button onClick={() => setRevealed(true)} className="text-indigo-400 hover:underline">
              Mostrar (puede contener spoilers)
            </button>
          ) : (
            (a.description ?? "")
          )}
        </p>
      </div>
      <div className="shrink-0 text-right text-xs">
        {a.unlocked ? (
          <p className="text-emerald-400">
            ✓ {a.unlocked_at ? formatDate(a.unlocked_at) : "Obtenido"}
          </p>
        ) : (
          <p className="text-slate-500">Pendiente</p>
        )}
        {a.global_percent !== null && (
          <p className="text-slate-500" title="Porcentaje de jugadores que lo tienen">
            {formatPercent(a.global_percent)} jugadores
          </p>
        )}
      </div>
    </li>
  );
}

export default function AchievementList({ entryId }: { entryId: number }) {
  const [filter, setFilter] = useState<Filter>("all");
  const query = useQuery({
    queryKey: ["achievements", entryId],
    queryFn: () => libraryApi.achievements(entryId),
  });

  const all = useMemo(() => query.data ?? [], [query.data]);
  const unlocked = all.filter((a) => a.unlocked).length;
  const visible = useMemo(() => {
    if (filter === "unlocked") {
      return all
        .filter((a) => a.unlocked)
        .sort((x, y) => (y.unlocked_at ?? "").localeCompare(x.unlocked_at ?? ""));
    }
    if (filter === "locked") {
      // Easiest first: the ones most players already have
      return all
        .filter((a) => !a.unlocked)
        .sort((x, y) => (y.global_percent ?? -1) - (x.global_percent ?? -1));
    }
    return all;
  }, [all, filter]);

  if (query.isLoading) return <p className="text-sm text-slate-400">Cargando logros…</p>;
  if (query.error) return <p className="text-sm text-red-400">{query.error.message}</p>;
  if (all.length === 0) {
    return (
      <p className="text-sm text-slate-400">
        Este juego no tiene logros, o aún no se han sincronizado. Los logros de Steam se
        actualizan al pulsar «Sincronizar con Steam» en Importar.
      </p>
    );
  }

  const pct = Math.round((unlocked / all.length) * 100);
  const chip = (value: Filter, label: string) => (
    <button
      onClick={() => setFilter(value)}
      className={`rounded-full px-3 py-1 text-xs transition ${
        filter === value ? "bg-indigo-600 text-white" : "bg-slate-800 text-slate-300 hover:bg-slate-700"
      }`}
    >
      {label}
    </button>
  );

  return (
    <div className="space-y-3">
      <div>
        <div className="mb-1 flex justify-between text-sm">
          <span className="text-slate-300">
            {unlocked} de {all.length} logros
          </span>
          <span className="tabular-nums text-slate-200">{pct} %</span>
        </div>
        <div className="h-2 rounded-full bg-slate-800">
          <div className="h-2 rounded-full bg-series-1" style={{ width: `${pct}%` }} />
        </div>
      </div>
      <div className="flex gap-2">
        {chip("all", `Todos (${all.length})`)}
        {chip("unlocked", `Obtenidos (${unlocked})`)}
        {chip("locked", `Pendientes (${all.length - unlocked})`)}
      </div>
      <ul className="max-h-[50vh] space-y-1 overflow-y-auto pr-1">
        {visible.map((a) => (
          <AchievementRow key={a.id} a={a} />
        ))}
      </ul>
    </div>
  );
}
