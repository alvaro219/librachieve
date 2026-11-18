import { useMutation } from "@tanstack/react-query";
import { useState } from "react";
import { Trans, useTranslation } from "react-i18next";
import { Link, useSearchParams } from "react-router-dom";

import { authApi, usersApi } from "../api/endpoints";
import { useAuth } from "../auth/AuthContext";
import LanguageSelect from "../components/LanguageSelect";
import { useInstall } from "../lib/pwa";

const STEAM_MESSAGES = {
  linked: { text: "settings.steamLinked", ok: true },
  taken: { text: "settings.steamTaken", ok: false },
  expired: { text: "settings.steamExpired", ok: false },
} as const;

function AppSection() {
  const { t } = useTranslation();
  const { state, install } = useInstall();
  return (
    <section className="card space-y-3">
      <h2 className="font-semibold">{t("settings.app.title")}</h2>
      {state === "installed" ? (
        <p className="text-sm text-emerald-300">✓ {t("settings.app.installed")}</p>
      ) : state === "elsewhere" ? (
        <p className="text-sm text-slate-300">
          <span className="text-emerald-300">✓ {t("settings.app.elsewhereTitle")}</span>{" "}
          {t("settings.app.elsewhere")}
        </p>
      ) : (
        <>
          <p className="text-sm text-slate-400">
            {t("settings.app.pitch")}
          </p>
          {state === "available" ? (
            <button className="btn-primary" onClick={() => void install()}>
              {t("settings.app.install")}
            </button>
          ) : state === "ios" ? (
            <p className="text-sm text-slate-300">
              <Trans i18nKey="settings.app.ios" components={{ strong: <strong /> }} />
            </p>
          ) : (
            <p className="text-sm text-slate-300">
              <Trans i18nKey="settings.app.manual" components={{ strong: <strong /> }} />
            </p>
          )}
        </>
      )}
    </section>
  );
}

function PasswordSection({
  hasPassword,
  onChanged,
}: {
  hasPassword: boolean;
  onChanged: () => void;
}) {
  const { t } = useTranslation();
  const [current, setCurrent] = useState("");
  const [next, setNext] = useState("");
  const [repeat, setRepeat] = useState("");
  const change = useMutation({
    mutationFn: usersApi.changePassword,
    onSuccess: () => {
      setCurrent("");
      setNext("");
      setRepeat("");
      onChanged();
    },
  });
  const mismatch = repeat !== "" && next !== repeat;

  return (
    <section className="card space-y-3">
      <h2 className="font-semibold">{t("settings.password.title")}</h2>
      {!hasPassword && (
        <p className="text-sm text-slate-400">
          {t("settings.password.steamOnly")}
        </p>
      )}
      <form
        className="grid gap-3 sm:max-w-sm"
        onSubmit={(e) => {
          e.preventDefault();
          change.mutate({
            current_password: hasPassword ? current : undefined,
            new_password: next,
          });
        }}
      >
        {hasPassword && (
          <input
            className="input"
            type="password"
            autoComplete="current-password"
            placeholder={t("settings.password.current")}
            value={current}
            required
            onChange={(e) => setCurrent(e.target.value)}
          />
        )}
        <input
          className="input"
          type="password"
          autoComplete="new-password"
          placeholder={t("settings.password.new")}
          minLength={8}
          maxLength={128}
          value={next}
          required
          onChange={(e) => setNext(e.target.value)}
        />
        <input
          className="input"
          type="password"
          autoComplete="new-password"
          placeholder={t("settings.password.repeat")}
          value={repeat}
          required
          onChange={(e) => setRepeat(e.target.value)}
        />
        {mismatch && <p className="text-sm text-amber-300">{t("settings.password.mismatch")}</p>}
        {change.error && <p className="text-sm text-red-400">{change.error.message}</p>}
        {change.isSuccess && <p className="text-sm text-emerald-400">✓ {t("settings.password.saved")}</p>}
        <button
          className="btn-primary justify-self-start"
          disabled={change.isPending || mismatch || next.length < 8}
        >
          {hasPassword ? t("settings.password.change") : t("settings.password.create")}
        </button>
      </form>
    </section>
  );
}

export default function SettingsPage() {
  const { user, setUser, logout } = useAuth();
  const { t } = useTranslation();
  const [params] = useSearchParams();
  const [username, setUsername] = useState(user!.username);
  const steamMsg = STEAM_MESSAGES[(params.get("steam") ?? "") as keyof typeof STEAM_MESSAGES];

  const update = useMutation({
    mutationFn: usersApi.updateMe,
    onSuccess: setUser,
  });
  const linkSteam = useMutation({
    mutationFn: authApi.steamLinkUrl,
    onSuccess: ({ url }) => window.location.assign(url),
  });
  const deleteAccount = useMutation({
    mutationFn: usersApi.deleteMe,
    onSuccess: () => void logout(),
  });

  if (!user) return null;

  return (
    <div className="mx-auto max-w-2xl space-y-6">
      <div className="flex items-center justify-between gap-4">
        <h1 className="text-2xl font-bold">{t("nav.settings")}</h1>
        {/* On wide screens "Salir" lives in the header */}
        <button onClick={() => void logout()} className="btn-secondary px-3 py-1.5 md:hidden">
          {t("settings.logout")}
        </button>
      </div>

      {steamMsg && (
        <p
          className={`rounded-lg border p-3 text-sm ${
            steamMsg.ok
              ? "border-emerald-700 bg-emerald-950/40 text-emerald-300"
              : "border-red-800 bg-red-950/40 text-red-300"
          }`}
        >
          {steamMsg.ok ? "✓ " : "✕ "}
          {t(steamMsg.text)}
        </p>
      )}

      <section className="card space-y-4">
        <h2 className="font-semibold">{t("settings.profile")}</h2>
        <form
          className="flex gap-3"
          onSubmit={(e) => {
            e.preventDefault();
            update.mutate({ username });
          }}
        >
          <input
            className="input"
            value={username}
            pattern="[A-Za-z0-9_\-]{3,32}"
            onChange={(e) => setUsername(e.target.value)}
          />
          <button className="btn-primary" disabled={update.isPending || username === user.username}>
            {t("common.save")}
          </button>
        </form>

        <label className="flex items-center justify-between gap-4">
          <span>
            <span className="block text-sm font-medium">{t("settings.public")}</span>
            <span className="text-xs text-slate-400">
              {t("settings.publicHint")}{" "}
              <Link to={`/u/${user.username}`} className="text-indigo-400 hover:underline">
                /u/{user.username}
              </Link>
            </span>
          </span>
          <input
            type="checkbox"
            className="h-5 w-5 accent-indigo-500"
            checked={user.is_public}
            disabled={update.isPending}
            onChange={(e) => update.mutate({ is_public: e.target.checked })}
          />
        </label>
        {update.error && <p className="text-sm text-red-400">{update.error.message}</p>}
      </section>

      <PasswordSection
        hasPassword={user.has_password}
        onChanged={() => setUser({ ...user, has_password: true })}
      />

      <section className="card space-y-3">
        <h2 className="font-semibold">Steam</h2>
        {user.steam_id ? (
          <p className="text-sm text-slate-400">{t("settings.steamLinkedId", { id: user.steam_id })}</p>
        ) : (
          <button
            className="btn-secondary"
            disabled={linkSteam.isPending}
            onClick={() => linkSteam.mutate()}
          >
            {t("settings.linkSteam")}
          </button>
        )}
      </section>

      <section className="card flex items-center justify-between gap-4">
        <h2 className="font-semibold">{t("common.language")}</h2>
        <LanguageSelect className="text-sm" />
      </section>

      <AppSection />

      <section className="card space-y-3 border-red-900/60">
        <h2 className="font-semibold text-red-300">{t("settings.danger")}</h2>
        <p className="text-sm text-slate-400">
          {t("settings.deleteHint")}
        </p>
        <button
          className="btn-danger"
          disabled={deleteAccount.isPending}
          onClick={() =>
            confirm(t("settings.deleteConfirm")) &&
            deleteAccount.mutate()
          }
        >
          {t("settings.delete")}
        </button>
      </section>
    </div>
  );
}
