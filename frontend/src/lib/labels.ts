import type { GameStatus, Platform, SyncJobStatus } from "../api/types";
import i18n, { currentLocale } from "../i18n";

// All user-facing enum labels live here. The maps read the active language on every access,
// so `STATUS_LABELS[s]` is always translated (App re-renders the tree on language change).

const translatedMap = <K extends string>(prefix: string) =>
  new Proxy({} as Record<K, string>, {
    get: (_, key) => i18n.t(`${prefix}.${String(key)}` as never),
  });

export const STATUS_ORDER: GameStatus[] = [
  "playing",
  "backlog",
  "completed",
  "dropped",
  "wishlist",
  "other",
];

export const STATUS_LABELS = translatedMap<GameStatus>("enums.status");

export const PLATFORM_LABELS = translatedMap<Platform>("enums.platform");

export const PLATFORMS: Platform[] = ["steam", "epic", "gog", "amazon", "other"];

export const SYNC_STATUS_LABELS = translatedMap<SyncJobStatus>("enums.syncStatus");

export function formatNumber(n: number, maximumFractionDigits = 0): string {
  return n.toLocaleString(currentLocale(), { maximumFractionDigits });
}

export function formatPlaytime(minutes: number): string {
  if (minutes <= 0) return i18n.t("common.notPlayed");
  if (minutes < 60) return `${minutes} min`;
  const hours = minutes / 60;
  return `${hours < 10 ? formatNumber(hours, 1) : formatNumber(Math.round(hours))} h`;
}

export function formatDate(iso: string | null): string {
  if (!iso) return "—";
  return new Date(iso).toLocaleDateString(currentLocale(), {
    year: "numeric",
    month: "short",
    day: "numeric",
  });
}

/** IGDB genre names come in English; show them in the UI language (filters keep the original). */
export function genreLabel(genre: string): string {
  return i18n.t(`genres.${genre}` as never, { defaultValue: genre });
}
