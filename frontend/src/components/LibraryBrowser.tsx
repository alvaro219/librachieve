import { keepPreviousData, useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";

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
import i18n from "../i18n";
import {
  PLATFORMS,
  PLATFORM_LABELS,
  STATUS_LABELS,
  STATUS_ORDER,
  genreLabel,
} from "../lib/labels";
import AddGameDialog from "./AddGameDialog";
import EntryEditor from "./EntryEditor";
import GameDetail from "./GameDetail";
import GameCard from "./GameCard";

const PAGE_SIZE = 60;

type RatingSource = "igdb" | "community" | "critic" | "user";

// Same names as the score tiles in the game view
const RATING_SOURCES: RatingSource[] = ["igdb", "community", "critic", "user"];
const RATING_NAMES = {
  igdb: "ratings.community",
  community: "ratings.users",
  critic: "ratings.critics",
  user: "ratings.yourScore",
} as const satisfies Record<RatingSource, string>;
const ratingLabel = (source: RatingSource, own: boolean) =>
  i18n.t(source === "user" && !own ? "ratings.theirScore" : RATING_NAMES[source]);

const RATING_FILTER_KEYS = {
  igdb: "minIgdbRating",
  community: "minCommunityRating",
  critic: "minCriticRating",
  user: "minUserRating",
} as const satisfies Record<RatingSource, keyof LibraryFilter>;

const MIN_RATINGS = [50, 60, 70, 75, 80, 90];

type SortValue = `${SortField}:${SortDirection}`;

const GENERAL_SORTS = [
  { value: "TITLE:ASC", label: "library.sort.title" },
  { value: "PLAYTIME:DESC", label: "library.sort.playtime" },
  { value: "LAST_PLAYED:DESC", label: "library.sort.lastPlayed" },
  { value: "ADDED_AT:DESC", label: "library.sort.added" },
  { value: "RELEASE_DATE:DESC", label: "library.sort.release" },
  { value: "ACHIEVEMENTS:DESC", label: "library.sort.achievements" },
] as const satisfies readonly { value: SortValue; label: string }[];

const RATING_SORT_FIELDS: Record<RatingSource, SortField> = {
  igdb: "IGDB_RATING",
  community: "COMMUNITY_RATING",
  critic: "CRITIC_RATING",
  user: "USER_RATING",
};

interface Props {
  /** View someone else's public library (read-only). Omit for your own. */
  username?: string;
}

export default function LibraryBrowser({ username }: Props) {
  const { t } = useTranslation();
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
  const [sort, setSort] = useState<SortValue>("TITLE:ASC");
  const [page, setPage] = useState(0);
  const [editing, setEditing] = useState<LibraryEntry | null>(null);
  const [viewing, setViewing] = useState<LibraryEntry | null>(null);
  const [adding, setAdding] = useState(false);
  const [showFilters, setShowFilters] = useState(false); // mobile: toolbar folded by default

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
  const activeFilters = [platform, genre, minRating !== null, favoritesOnly].filter(Boolean).length;

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
        {tab(null, t("library.all"))}
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

      <div className="flex items-center gap-2 sm:gap-3">
        <input
          className="input min-w-0 flex-1"
          type="search"
          placeholder={t("library.search")}
          value={searchInput}
          onChange={(e) => setSearchInput(e.target.value)}
        />
        <button
          type="button"
          className={`btn-secondary shrink-0 px-3 md:hidden ${
            activeFilters ? "border-indigo-500/70 text-indigo-200" : ""
          }`}
          onClick={() => setShowFilters((v) => !v)}
          aria-expanded={showFilters}
        >
          {t("library.filters")}
          {activeFilters > 0 && ` (${activeFilters})`}
        </button>
        {editable && (
          <button
            className="btn-primary shrink-0 px-3 sm:px-4"
            onClick={() => setAdding(true)}
            title={t("addGame.title")}
          >
            +<span className="hidden sm:inline"> {t("addGame.title")}</span>
          </button>
        )}
      </div>

      <div
        className={`${showFilters ? "flex" : "hidden"} flex-wrap items-center justify-between gap-x-6 gap-y-3 rounded-xl border border-slate-800 bg-slate-900/40 p-3 md:flex`}
      >
        <div className="flex w-full flex-wrap items-center gap-2 md:w-auto">
          <span className="mr-1 hidden text-xs font-semibold uppercase tracking-wide text-slate-500 md:inline">
            {t("library.filter")}
          </span>
          <select
            className="input w-full sm:w-auto"
            value={platform}
            onChange={(e) => setPlatform(e.target.value as Platform | "")}
            aria-label={t("addGame.platform")}
          >
            <option value="">{t("library.allPlatforms")}</option>
            {PLATFORMS.map((p) => (
              <option key={p} value={p}>
                {PLATFORM_LABELS[p]}
              </option>
            ))}
          </select>
          <select
            className="input w-full sm:w-auto sm:max-w-[13rem]"
            value={genre}
            onChange={(e) => setGenre(e.target.value)}
            aria-label={t("library.genre")}
          >
            <option value="">{t("library.allGenres")}</option>
            {genres.data?.map((g) => (
              <option key={g.genre} value={g.genre}>
                {genreLabel(g.genre)} ({g.games})
              </option>
            ))}
          </select>
          <div
            className={`flex w-full items-center rounded-lg border bg-slate-900 pl-3 text-sm sm:w-auto ${
              minRating !== null ? "border-indigo-500/70" : "border-slate-700"
            }`}
          >
            <span className="text-slate-400">{t("library.score")}</span>
            <select
              className="min-w-0 flex-1 cursor-pointer bg-slate-900 px-2 py-2 text-slate-100 focus:outline-none sm:flex-none"
              value={ratingSource}
              onChange={(e) => setRatingSource(e.target.value as RatingSource)}
              aria-label={t("library.scoreSource")}
            >
              {RATING_SOURCES.map((r) => (
                <option key={r} value={r}>
                  {ratingLabel(r, editable)}
                </option>
              ))}
            </select>
            <select
              className="min-w-0 flex-1 cursor-pointer rounded-r-lg border-l border-slate-700 bg-slate-900 px-2 py-2 text-slate-100 focus:outline-none sm:flex-none"
              value={minRating ?? ""}
              onChange={(e) => setMinRating(e.target.value ? Number(e.target.value) : null)}
              aria-label={t("library.minScore")}
            >
              <option value="">{t("library.anyScore")}</option>
              {MIN_RATINGS.map((n) => (
                <option key={n} value={n}>
                  {t("library.orMore", { n })}
                </option>
              ))}
            </select>
          </div>
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
            {favoritesOnly ? "★" : "☆"} {t("library.favorites")}
          </button>
          {activeFilters > 0 && (
            <button
              type="button"
              className="px-2 text-sm text-slate-400 underline-offset-2 hover:text-white hover:underline"
              onClick={() => {
                setPlatform("");
                setGenre("");
                setMinRating(null);
                setFavoritesOnly(false);
              }}
            >
              {t("library.clear")}
            </button>
          )}
        </div>

        <label className="flex w-full items-center gap-2 md:w-auto">
          <span className="shrink-0 text-xs font-semibold uppercase tracking-wide text-slate-500">
            {t("library.sortBy")}
          </span>
          <select
            className="input min-w-0 flex-1 md:w-auto md:flex-none"
            value={sort}
            onChange={(e) => setSort(e.target.value as SortValue)}
          >
            <optgroup label={t("library.sort.general")}>
              {GENERAL_SORTS.map((s) => (
                <option key={s.value} value={s.value}>
                  {t(s.label)}
                </option>
              ))}
            </optgroup>
            <optgroup label={t("library.sort.scores")}>
              {RATING_SOURCES.map((r) => (
                <option key={r} value={`${RATING_SORT_FIELDS[r]}:DESC`}>
                  {ratingLabel(r, editable)}
                </option>
              ))}
            </optgroup>
          </select>
        </label>
      </div>

      <p className="text-sm text-slate-400">
        {t("stats.gamesCount", { count: total })}
      </p>

      {library.error && <p className="text-red-400">{library.error.message}</p>}
      {library.isLoading && <p className="text-slate-400">{t("library.loading")}</p>}
      {library.data && library.data.items.length === 0 && (
        <div className="card text-center text-slate-400">
          {editable
            ? t("library.emptyOwn")
            : t("library.emptyOther")}
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
            {t("library.previous")}
          </button>
          <span className="text-sm text-slate-400">
            {page + 1} / {pages}
          </span>
          <button
            className="btn-secondary"
            disabled={page + 1 >= pages}
            onClick={() => setPage((p) => p + 1)}
          >
            {t("library.next")}
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
