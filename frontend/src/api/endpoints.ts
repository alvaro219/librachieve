import { api } from "./client";
import type {
  Achievement,
  AdminOverview,
  AdminUser,
  AdminUserPage,
  Friend,
  FriendsOverview,
  IgdbSearchResult,
  LibraryEntry,
  LibraryEntryCreate,
  LibraryEntryUpdate,
  PasswordChange,
  Platform,
  RatingResult,
  SyncJob,
  TokenResponse,
  UserMe,
  UserPublic,
  UserRole,
  UserSearchResult,
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
  changePassword: (body: PasswordChange) =>
    api<void>("/api/users/me/password", { method: "PUT", json: body }),
  search: (q: string) => api<UserSearchResult[]>(`/api/users/search?${new URLSearchParams({ q })}`),
  myStats: () => api<UserStats>("/api/users/me/stats"),
  profile: (username: string) => api<UserPublic>(`/api/users/${encodeURIComponent(username)}`),
  profileStats: (username: string) =>
    api<UserStats>(`/api/users/${encodeURIComponent(username)}/stats`),
};

export const friendsApi = {
  list: () => api<FriendsOverview>("/api/friends"),
  request: (username: string) => api<Friend>("/api/friends/requests", { json: { username } }),
  accept: (id: number) => api<Friend>(`/api/friends/${id}/accept`, { method: "POST" }),
  /** Your Steam friends who use Librachieve */
  steam: () => api<UserSearchResult[]>("/api/friends/steam"),
  /** Befriend all of them at once (no request: they're already friends on Steam) */
  addSteam: () => api<{ added: number }>("/api/friends/steam", { method: "POST" }),
  /** Reject or cancel a request, or remove a friend */
  remove: (id: number) => api<void>(`/api/friends/${id}`, { method: "DELETE" }),
};

export const adminApi = {
  overview: () => api<AdminOverview>("/api/admin/overview"),
  users: (q: string, offset: number) =>
    api<AdminUserPage>(
      `/api/admin/users?${new URLSearchParams({ q, offset: String(offset), limit: "50" })}`,
    ),
  setRole: (id: number, role: UserRole) =>
    api<AdminUser>(`/api/admin/users/${id}`, { method: "PATCH", json: { role } }),
  deleteUser: (id: number) => api<void>(`/api/admin/users/${id}`, { method: "DELETE" }),
  reenrich: () => api<{ enqueued: number }>("/api/admin/reenrich", { method: "POST" }),
};

export const libraryApi = {
  add: (body: LibraryEntryCreate) => api<LibraryEntry>("/api/library", { json: body }),
  update: (id: number, body: LibraryEntryUpdate) =>
    api<LibraryEntry>(`/api/library/${id}`, { method: "PATCH", json: body }),
  remove: (id: number) => api<void>(`/api/library/${id}`, { method: "DELETE" }),
  achievements: (id: number) => api<Achievement[]>(`/api/library/${id}/achievements`),
};

export const gamesApi = {
  rate: (gameId: number, score: number) =>
    api<RatingResult>(`/api/games/${gameId}/rating`, { method: "PUT", json: { score } }),
  unrate: (gameId: number) =>
    api<RatingResult>(`/api/games/${gameId}/rating`, { method: "DELETE" }),
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
  undo: (id: number) => api<SyncJob>(`/api/sync/jobs/${id}/undo`, { method: "POST" }),
};
