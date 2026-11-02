import { ApiError, rawRequest, refreshSession } from "./client";
import type { GameStatus, LibraryEntry, Platform } from "./types";

// GraphQL is used only for library list queries with complex filtering (see CLAUDE.md).

export type SortField =
  | "TITLE"
  | "PLAYTIME"
  | "ADDED_AT"
  | "LAST_PLAYED"
  | "RELEASE_DATE"
  | "ACHIEVEMENTS";
export type SortDirection = "ASC" | "DESC";

export interface LibraryFilter {
  statuses?: GameStatus[];
  platforms?: Platform[];
  genres?: string[];
  search?: string;
  customFolder?: string;
  minPlaytimeMinutes?: number;
  maxPlaytimeMinutes?: number;
  releasedAfter?: string;
  releasedBefore?: string;
}

export interface LibraryQueryVariables {
  username?: string;
  filter?: LibraryFilter;
  sort?: { field: SortField; direction: SortDirection };
  limit?: number;
  offset?: number;
}

export interface LibraryQueryResult {
  items: LibraryEntry[];
  total: number;
}

async function gql<T>(query: string, variables: object = {}, retry = true): Promise<T> {
  const resp = await rawRequest("/graphql", { json: { query, variables } });
  const body = await resp.json().catch(() => ({}));
  // GraphQL reports auth failures as 200 + errors, so an expired token needs an explicit refresh.
  if (retry && body.errors?.[0]?.message === "Not authenticated" && (await refreshSession())) {
    return gql<T>(query, variables, false);
  }
  if (!resp.ok || body.errors?.length) {
    throw new ApiError(resp.status, body.errors?.[0]?.message ?? resp.statusText);
  }
  return body.data as T;
}

const LIBRARY_QUERY = /* GraphQL */ `
  query Library(
    $username: String
    $filter: LibraryFilter
    $sort: LibrarySort
    $limit: Int!
    $offset: Int!
  ) {
    library(username: $username, filter: $filter, sort: $sort, limit: $limit, offset: $offset) {
      total
      items {
        id
        platform
        status
        customFolder
        playtimeMinutes
        lastPlayedAt
        addedAt
        achievementsUnlocked
        achievementsTotal
        game {
          id
          title
          igdbId
          steamAppid
          coverUrl
          summary
          releaseDate
          genres
        }
      }
    }
  }
`;

interface GqlEntry {
  id: number;
  platform: string;
  status: string;
  customFolder: string | null;
  playtimeMinutes: number;
  lastPlayedAt: string | null;
  addedAt: string;
  achievementsUnlocked: number;
  achievementsTotal: number;
  game: {
    id: number;
    title: string;
    igdbId: number | null;
    steamAppid: number | null;
    coverUrl: string | null;
    summary: string | null;
    releaseDate: string | null;
    genres: string[];
  };
}

// GraphQL enums come back as upper-case member names; REST uses lower-case values.
function toEntry(e: GqlEntry): LibraryEntry {
  return {
    id: e.id,
    platform: e.platform.toLowerCase() as Platform,
    status: e.status.toLowerCase() as GameStatus,
    custom_folder: e.customFolder,
    playtime_minutes: e.playtimeMinutes,
    last_played_at: e.lastPlayedAt,
    added_at: e.addedAt,
    achievements_unlocked: e.achievementsUnlocked,
    achievements_total: e.achievementsTotal,
    game: {
      id: e.game.id,
      title: e.game.title,
      igdb_id: e.game.igdbId,
      steam_appid: e.game.steamAppid,
      cover_url: e.game.coverUrl,
      summary: e.game.summary,
      release_date: e.game.releaseDate,
      genres: e.game.genres,
    },
  };
}

export async function fetchLibrary(vars: LibraryQueryVariables): Promise<LibraryQueryResult> {
  const filter = vars.filter && {
    ...vars.filter,
    statuses: vars.filter.statuses?.map((s) => s.toUpperCase()),
    platforms: vars.filter.platforms?.map((p) => p.toUpperCase()),
  };
  const data = await gql<{ library: { total: number; items: GqlEntry[] } }>(LIBRARY_QUERY, {
    username: vars.username,
    filter,
    sort: vars.sort,
    limit: vars.limit ?? 60,
    offset: vars.offset ?? 0,
  });
  return { total: data.library.total, items: data.library.items.map(toEntry) };
}

export async function fetchCustomFolders(): Promise<string[]> {
  const data = await gql<{ customFolders: string[] }>("query { customFolders }");
  return data.customFolders;
}
