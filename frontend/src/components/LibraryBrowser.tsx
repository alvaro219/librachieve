import { keepPreviousData, useQuery } from "@tanstack/react-query";
import { useEffect, useState } from "react";

import {
  fetchCustomFolders,
  fetchLibrary,
  type LibraryFilter,
  type SortDirection,
  type SortField,
} from "../api/graphql";
import type { GameStatus, LibraryEntry, Platform } from "../api/types";
import { PLATFORMS, PLATFORM_LABELS, STATUS_LABELS, STATUS_ORDER } from "../lib/labels";
import AddGameDialog from "./AddGameDialog";
import EntryEditor from "./EntryEditor";
import GameDetail from "./GameDetail";
import GameCard from "./GameCard";

const PAGE_SIZE = 60;

const SORTS: { value: `${SortField}:${SortDirection}`; label: string }[] = [
  { value: "TITLE:ASC", label: "Título (A-Z)" },
  { value: "PLAYTIME:DESC", label: "Más jugados" },
  { value: "LAST_PLAYED:DESC", label: "Jugados recientemente" },
  { value: "ADDED_AT:DESC", label: "Añadidos recientemente" },
  { value: "RELEASE_DATE:DESC", label: "Lanzamiento (nuevos)" },
  { value: "ACHIEVEMENTS:DESC", label: "Más logros (%)" },
];

interface Props {
  /** View someone else's public library (read-only). Omit for your own. */
  username?: string;
}

export default function LibraryBrowser({ username }: Props) {
  const editable = !username;
  const [status, setStatus] = useState<GameStatus | null>(null);
  const [folder, setFolder] = useState<string | null>(null);
  const [platform, setPlatform] = useState<Platform | "">("");
  const [searchInput, setSearchInput] = useState("");
  const [search, setSearch] = useState("");
  const [sort, setSort] = useState<(typeof SORTS)[number]["value"]>("TITLE:ASC");
  const [page, setPage] = useState(0);
  const [editing, setEditing] = useState<LibraryEntry | null>(null);
  const [viewing, setViewing] = useState<LibraryEntry | null>(null);
  const [adding, setAdding] = useState(false);

  useEffect(() => {
    const t = setTimeout(() => setSearch(searchInput.trim()), 300);
    return () => clearTimeout(t);
  }, [searchInput]);

  // Any filter change goes back to the first page.
  useEffect(() => setPage(0), [status, folder, platform, search, sort]);

  const filter: LibraryFilter = {
    statuses: status ? [status] : undefined,
    platforms: platform ? [platform] : undefined,
    search: search || undefined,
    customFolder: status === "other" && folder ? folder : undefined,
  };
  const [field, direction] = sort.split(":") as [SortField, SortDirection];

  const library = useQuery({
    queryKey: ["library", username ?? "me", filter, sort, page],
    queryFn: () =>
      fetchLibrary({
        username,
        filter,
        sort: { field, direction },
        limit: PAGE_SIZE,
        offset: page * PAGE_SIZE,
      }),
    placeholderData: keepPreviousData,
  });

  const folders = useQuery({
    queryKey: ["customFolders"],
    queryFn: fetchCustomFolders,
    enabled: editable,
  });

  const total = library.data?.total ?? 0;
  const pages = Math.ceil(total / PAGE_SIZE);

  const tab = (value: GameStatus | null, label: string) => (
    <button
      key={label}
      onClick={() => {
        setStatus(value);
        setFolder(null);
      }}
      className={`whitespace-nowrap rounded-full px-4 py-1.5 text-sm transition ${
        status === value
          ? "bg-indigo-600 text-white"
          : "bg-slate-900 text-slate-300 hover:bg-slate-800"
      }`}
    >
      {label}
    </button>
  );

  return (
    <div className="space-y-6">
      <div className="flex gap-2 overflow-x-auto pb-1">
        {tab(null, "Todos")}
        {STATUS_ORDER.map((s) => tab(s, STATUS_LABELS[s]))}
      </div>

      {editable && status === "other" && (folders.data?.length ?? 0) > 0 && (
        <div className="flex flex-wrap gap-2">
          {folders.data!.map((f) => (
            <button
              key={f}
              onClick={() => setFolder(folder === f ? null : f)}
              className={`rounded-lg border px-3 py-1 text-xs ${
                folder === f
                  ? "border-indigo-500 text-white"
                  : "border-slate-700 text-slate-400 hover:text-white"
              }`}
            >
              📁 {f}
            </button>
          ))}
        </div>
      )}

      <div className="flex flex-wrap items-center gap-3">
        <input
          className="input max-w-xs"
          placeholder="Buscar por título…"
          value={searchInput}
          onChange={(e) => setSearchInput(e.target.value)}
        />
        <select
          className="input w-auto"
          value={platform}
          onChange={(e) => setPlatform(e.target.value as Platform | "")}
        >
          <option value="">Todas las plataformas</option>
          {PLATFORMS.map((p) => (
            <option key={p} value={p}>
              {PLATFORM_LABELS[p]}
            </option>
          ))}
        </select>
        <select
          className="input w-auto"
          value={sort}
          onChange={(e) => setSort(e.target.value as typeof sort)}
        >
          {SORTS.map((s) => (
            <option key={s.value} value={s.value}>
              {s.label}
            </option>
          ))}
        </select>
        <span className="text-sm text-slate-400">{total} juegos</span>
        {editable && (
          <button className="btn-primary ml-auto" onClick={() => setAdding(true)}>
            + Añadir juego
          </button>
        )}
      </div>

      {library.error && <p className="text-red-400">{library.error.message}</p>}
      {library.isLoading && <p className="text-slate-400">Cargando biblioteca…</p>}
      {library.data && library.data.items.length === 0 && (
        <div className="card text-center text-slate-400">
          {editable
            ? "No hay juegos aquí. Importa tu biblioteca o añade juegos a mano."
            : "Esta biblioteca no tiene juegos con estos filtros."}
        </div>
      )}

      <div
        className={`grid grid-cols-2 gap-4 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6 ${
          library.isPlaceholderData ? "opacity-60" : ""
        }`}
      >
        {library.data?.items.map((entry) => (
          <GameCard
            key={entry.id}
            entry={entry}
            onClick={() => (editable ? setEditing(entry) : setViewing(entry))}
          />
        ))}
      </div>

      {pages > 1 && (
        <div className="flex items-center justify-center gap-3">
          <button
            className="btn-secondary"
            disabled={page === 0}
            onClick={() => setPage((p) => p - 1)}
          >
            Anterior
          </button>
          <span className="text-sm text-slate-400">
            {page + 1} / {pages}
          </span>
          <button
            className="btn-secondary"
            disabled={page + 1 >= pages}
            onClick={() => setPage((p) => p + 1)}
          >
            Siguiente
          </button>
        </div>
      )}

      {editing && (
        <EntryEditor
          entry={editing}
          folders={folders.data ?? []}
          onClose={() => setEditing(null)}
        />
      )}
      {viewing && <GameDetail entry={viewing} onClose={() => setViewing(null)} />}
      {adding && <AddGameDialog onClose={() => setAdding(false)} />}
    </div>
  );
}
