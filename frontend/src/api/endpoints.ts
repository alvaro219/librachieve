import { api } from "./client";
import type {
  Achievement,
  IgdbSearchResult,
  LibraryEntry,
  LibraryEntryCreate,
  LibraryEntryUpdate,
  Platform,
  SyncJob,
  TokenResponse,
  UserMe,
  UserPublic,
  UserStats,
  UserUpdate,
} from "./types";

export const authApi = {
  login: (login: string, password: string) =>
    api<TokenResponse>("/api/auth/login", { json: { login, password } }),
  register: (username: string, email: string, password: string) =>
    api<TokenResponse>("/api/auth/register", { json: { username, email, password } }),
  logout: () => api<void>("/api/auth/logout", { method: "POST" }),
  steamLinkUrl: () => api<{ url: string }>("/api/auth/steam/link-url", { method: "POST" }),
};

export const usersApi = {
  me: () => api<UserMe>("/api/users/me"),
  updateMe: (body: UserUpdate) => api<UserMe>("/api/users/me", { method: "PATCH", json: body }),
  deleteMe: () => api<void>("/api/users/me", { method: "DELETE" }),
  myStats: () => api<UserStats>("/api/users/me/stats"),
  profile: (username: string) => api<UserPublic>(`/api/users/${encodeURIComponent(username)}`),
  profileStats: (username: string) =>
    api<UserStats>(`/api/users/${encodeURIComponent(username)}/stats`),
};

export const libraryApi = {
  add: (body: LibraryEntryCreate) => api<LibraryEntry>("/api/library", { json: body }),
  update: (id: number, body: LibraryEntryUpdate) =>
    api<LibraryEntry>(`/api/library/${id}`, { method: "PATCH", json: body }),
  remove: (id: number) => api<void>(`/api/library/${id}`, { method: "DELETE" }),
  achievements: (id: number) => api<Achievement[]>(`/api/library/${id}/achievements`),
};

export const gamesApi = {
  search: (q: string) =>
    api<IgdbSearchResult[]>(`/api/games/search?${new URLSearchParams({ q, limit: "8" })}`),
};

export const syncApi = {
  steam: () => api<SyncJob>("/api/sync/steam", { method: "POST" }),
  importFile: (platform: Platform, file: File) => {
    const form = new FormData();
    form.append("file", file);
    return api<SyncJob>(`/api/sync/import/${platform}`, { form });
  },
  jobs: () => api<SyncJob[]>("/api/sync/jobs"),
};
