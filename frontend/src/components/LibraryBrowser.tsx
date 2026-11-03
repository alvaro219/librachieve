import { keepPreviousData, useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useEffect, useState } from "react";

import {
  fetchCustomFolders,
  fetchGenres,
  fetchLibrary,
  type LibraryFilter,
  type SortDirection,
  type SortField,
} from "../api/graphql";
import { libraryApi } from "../api/endpoints";
import type { GameStatus, LibraryEntry, Platform } from "../api/types";
import { PLATFORMS, PLATFORM_LABELS, STATUS_LABELS, STATUS_ORDER } from "../lib/labels";
import AddGameDialog from "./AddGameDialog";
import EntryEditor from "./EntryEditor";
import GameDetail from "./GameDetail";
import GameCard from "./GameCard";

const PAGE_SIZE = 60;

type RatingSource = "igdb" | "community" | "critic" | "user";

// Same labels as the score tiles in the game view
const RATING_SOURCES: { value: RatingSource; label: string }[] = [
  { value: "igdb", label: "la comunidad" },
  { value: "community", label: "los usuarios" },
  { value: "critic", label: "la crítica" },
  { value: "user", label: "mi nota" },
];

const RATING_FILTER_KEYS = {
  igdb: "minIgdbRating",
  community: "minCommunityRating",
  critic: "minCriticRating",
  user: "minUserRating",
} as const satisfies Record<RatingSource, keyof LibraryFilter>;

const MIN_RATINGS = [50, 60, 70, 75, 80, 90];

const SORTS: { value: `${SortField}:${SortDirection}`; label: string }[] = [
  { value: "TITLE:ASC", label: "Título (A-Z)" },
  { value: "PLAYTIME:DESC", label: "Más jugados" },
  { value: "LAST_PLAYED:DESC", label: "Jugados recientemente" },
  { value: "ADDED_AT:DESC", label: "Añadidos recientemente" },
  { value: "RELEASE_DATE:DESC", label: "Lanzamiento (nuevos)" },
  { value: "ACHIEVEMENTS:DESC", label: "Más logros (%)" },
  { value: "USER_RATING:DESC", label: "Mi nota" },
  { value: "COMMUNITY_RATING:DESC", label: "Nota de usuarios" },
  { value: "CRITIC_RATING:DESC", label: "Nota de la crítica" },
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
  const [favoritesOnly, setFavoritesOnly] = useState(false);
  const [genre, setGenre] = useState("");
  const [minRating, setMinRating] = useState<number | null>(null);
  const [ratingSource, setRatingSource] = useState<RatingSource>("igdb");
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
  useEffect(
    () => setPage(0),
    [status, folder, platform, favoritesOnly, genre, minRating, ratingSource, search, sort],
  );

  const filter: LibraryFilter = {
    statuses: status ? [status] : undefined,
    platforms: platform ? [platform] : undefined,
    search: search || undefined,
    favoritesOnly: favoritesOnly || undefined,
    customFolder: status === "other" && folder ? folder : undefined,
    genres: genre ? [genre] : undefined,
    ...(minRating !== null ? { [RATING_FILTER_KEYS[ratingSource]]: minRating } : {}),
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

  const genres = useQuery({
    queryKey: ["genres", username ?? "me"],
    queryFn: () => fetchGenres(username),
  });

  const folders = useQuery({
    queryKey: ["customFolders"],
    queryFn: fetchCustomFolders,
    enabled: editable,
  });

  const queryClient = useQueryClient();
  const toggleFavorite = useMutation({
    mutationFn: (entry: LibraryEntry) =>
      libraryApi.update(entry.id, { is_favorite: !entry.is_favorite }),
    onSuccess: () => void queryClient.invalidateQueries({ queryKey: ["library"] }),
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
        <button
          type="button"
          onClick={() => setFavoritesOnly((v) => !v)}
          aria-pressed={favoritesOnly}
          className={`rounded-lg border px-3 py-2 text-sm transition ${
            favoritesOnly
              ? "border-amber-400/70 bg-amber-400/10 text-amber-200"
              : "border-slate-700 bg-slate-900 text-slate-300 hover:bg-slate-800"
          }`}
        >
          {favoritesOnly ? "★" : "☆"} Favoritos
        </button>
        <select
          className="input w-auto max-w-[14rem]"
          value={genre}
          onChange={(e) => setGenre(e.target.value)}
          aria-label="Género"
        >
          <option value="">Todos los géneros</option>
          {genres.data?.map((g) => (
            <option key={g.genre} value={g.genre}>
              {g.genre} ({g.games})
            </option>
          ))}
        </select>
        <select
          className="input w-auto"
          value={minRating ?? ""}
          onChange={(e) => setMinRating(e.target.value ? Number(e.target.value) : null)}
          aria-label="Nota mínima"
        >
          <option value="">Cualquier nota</option>
          {MIN_RATINGS.map((n) => (
            <option key={n} value={n}>
              Nota {n}+
            </option>
          ))}
        </select>
        {minRating !== null && (
          <select
            className="input w-auto"
            value={ratingSource}
            onChange={(e) => setRatingSource(e.target.value as RatingSource)}
            aria-label="Fuente de la nota"
          >
            {RATING_SOURCES.map((r) => (
              <option key={r.value} value={r.value}>
                de {r.label}
              </option>
            ))}
          </select>
        )}
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
            onToggleFavorite={editable ? () => toggleFavorite.mutate(entry) : undefined}
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
