// Mirrors backend/app/schemas/*.py. Keep in sync when the Pydantic models change.

export type UserRole = "user" | "admin";
export type GameStatus = "backlog" | "playing" | "completed" | "dropped" | "wishlist" | "other";
export type Platform = "steam" | "epic" | "gog" | "amazon" | "other";
export type SyncJobStatus = "pending" | "running" | "success" | "failed" | "reverted";

export interface TokenResponse {
  access_token: string;
  token_type: "bearer";
  expires_in: number;
}

export interface UserPublic {
  id: number;
  username: string;
  avatar_url: string | null;
  is_public: boolean;
  created_at: string;
}

export interface UserMe extends UserPublic {
  email: string | null;
  role: UserRole;
  steam_id: string | null;
}

export interface UserUpdate {
  username?: string;
  is_public?: boolean;
}

export interface GenreStat {
  genre: string;
  playtime_minutes: number;
  games: number;
}

export interface PlatformStat {
  platform: Platform;
  games: number;
}

export interface UserStats {
  total_games: number;
  total_playtime_minutes: number;
  completed_games: number;
  completion_ratio: number;
  games_by_status: Record<GameStatus, number>;
  achievements_unlocked: number;
  achievements_total: number;
  perfect_games: number;
  top_genres: GenreStat[];
  games_by_platform: PlatformStat[];
}

export interface Game {
  id: number;
  title: string;
  igdb_id: number | null;
  steam_appid: number | null;
  cover_url: string | null;
  summary: string | null;
  release_date: string | null;
  genres: string[];
}

export interface IgdbSearchResult {
  igdb_id: number;
  title: string;
  cover_url: string | null;
  release_date: string | null;
  genres: string[];
  summary: string | null;
}

export interface LibraryEntry {
  id: number;
  platform: Platform;
  status: GameStatus;
  custom_folder: string | null;
  playtime_minutes: number;
  is_favorite: boolean;
  last_played_at: string | null;
  added_at: string;
  achievements_unlocked: number;
  achievements_total: number;
  game: Game;
}

export interface Achievement {
  id: number;
  name: string;
  description: string | null;
  icon_url: string | null;
  icon_locked_url: string | null;
  hidden: boolean;
  /** Share of all players who unlocked it, 0-100 */
  global_percent: number | null;
  unlocked: boolean;
  unlocked_at: string | null;
}

export interface LibraryEntryCreate {
  game_id?: number;
  igdb_id?: number;
  title?: string;
  platform?: Platform;
  status?: GameStatus;
  custom_folder?: string | null;
  playtime_minutes?: number;
}

export interface LibraryEntryUpdate {
  status?: GameStatus;
  is_favorite?: boolean;
  custom_folder?: string | null;
  playtime_minutes?: number;
}

export interface SyncJob {
  id: number;
  platform: Platform;
  status: SyncJobStatus;
  imported_count: number;
  error: string | null;
  created_at: string;
  finished_at: string | null;
  /** Only the newest completed file import can be undone */
  undoable: boolean;
}
