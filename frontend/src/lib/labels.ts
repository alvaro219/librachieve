import type { GameStatus, Platform, SyncJobStatus } from "../api/types";

// All user-facing enum labels live here so the UI can be translated in one place.

export const STATUS_ORDER: GameStatus[] = [
  "playing",
  "backlog",
  "completed",
  "dropped",
  "wishlist",
  "other",
];

export const STATUS_LABELS: Record<GameStatus, string> = {
  backlog: "Pendientes",
  playing: "Jugando",
  completed: "Completados",
  dropped: "Abandonados",
  wishlist: "Deseados",
  other: "Otros",
};

export const PLATFORM_LABELS: Record<Platform, string> = {
  steam: "Steam",
  epic: "Epic Games",
  gog: "GOG",
  amazon: "Amazon Games",
  other: "Otra",
};

export const PLATFORMS: Platform[] = ["steam", "epic", "gog", "amazon", "other"];

export const SYNC_STATUS_LABELS: Record<SyncJobStatus, string> = {
  pending: "En cola",
  running: "En curso",
  success: "Completada",
  failed: "Fallida",
  reverted: "Deshecha",
};

export function formatPlaytime(minutes: number): string {
  if (minutes <= 0) return "Sin jugar";
  if (minutes < 60) return `${minutes} min`;
  const hours = minutes / 60;
  return `${hours < 10 ? hours.toFixed(1).replace(".", ",") : Math.round(hours)} h`;
}

export function formatDate(iso: string | null): string {
  if (!iso) return "—";
  return new Date(iso).toLocaleDateString("es-ES", {
    year: "numeric",
    month: "short",
    day: "numeric",
  });
}
