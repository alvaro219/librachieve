import { useSyncExternalStore } from "react";

/** Chrome/Edge (desktop and Android) event that lets us show our own "Install" button */
interface BeforeInstallPromptEvent extends Event {
  prompt: () => Promise<void>;
  userChoice: Promise<{ outcome: "accepted" | "dismissed" }>;
}

let deferred: BeforeInstallPromptEvent | null = null;
let installed = false;
/** Installed on this device, but we're in a browser tab right now */
let installedElsewhere = false;
const listeners = new Set<() => void>();
const notify = () => listeners.forEach((l) => l());

const standalone = () =>
  window.matchMedia("(display-mode: standalone)").matches ||
  // iOS Safari
  (navigator as Navigator & { standalone?: boolean }).standalone === true;

/** Call once at startup: the browser fires these before any page component mounts. */
export function setupPwa() {
  window.addEventListener("beforeinstallprompt", (e) => {
    e.preventDefault(); // no mini-infobar: we offer it in Ajustes
    deferred = e as BeforeInstallPromptEvent;
    notify();
  });
  window.addEventListener("appinstalled", () => {
    deferred = null;
    installed = true;
    notify();
  });
  // Chromium only; needs "related_applications" (webapp) in the manifest
  const nav = navigator as Navigator & { getInstalledRelatedApps?: () => Promise<unknown[]> };
  nav
    .getInstalledRelatedApps?.()
    .then((apps) => {
      installedElsewhere = apps.length > 0;
      notify();
    })
    .catch(() => undefined);
  // Dev runs on Vite's server: a worker there would serve stale modules
  if (import.meta.env.PROD && "serviceWorker" in navigator) {
    window.addEventListener("load", () => {
      navigator.serviceWorker.register("/sw.js").catch(() => undefined);
    });
  }
}

export type InstallState =
  | "installed" // running as the app, or just installed
  | "elsewhere" // installed, but opened in a browser tab
  | "available" // the browser lets us show the prompt
  | "ios" // Safari on iPhone/iPad: only by hand (Share → Add to Home Screen)
  | "manual"; // other browsers: from the browser's menu, if supported

function snapshot(): InstallState {
  if (installed || standalone()) return "installed";
  if (installedElsewhere) return "elsewhere";
  if (deferred) return "available";
  if (/iphone|ipad|ipod/i.test(navigator.userAgent)) return "ios";
  return "manual";
}

export function useInstall() {
  const state = useSyncExternalStore((l) => {
    listeners.add(l);
    return () => listeners.delete(l);
  }, snapshot);

  const install = async () => {
    if (!deferred) return;
    const event = deferred;
    deferred = null; // a prompt can only be used once
    await event.prompt();
    const { outcome } = await event.userChoice;
    if (outcome === "accepted") installed = true;
    notify();
  };

  return { state, install };
}
