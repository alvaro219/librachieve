import { useState, type FormEvent } from "react";
import { Trans, useTranslation } from "react-i18next";
import { Link, Navigate, useNavigate } from "react-router-dom";

import { useAuth } from "../auth/AuthContext";
import AuthShell, { SteamButton } from "./AuthShell";

export default function RegisterPage() {
  const { user, register } = useAuth();
  const { t } = useTranslation();
  const navigate = useNavigate();
  const [form, setForm] = useState({ username: "", email: "", password: "" });
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  if (user) return <Navigate to="/" replace />;

  const submit = async (e: FormEvent) => {
    e.preventDefault();
    setBusy(true);
    setError(null);
    try {
      await register(form.username, form.email, form.password);
      navigate("/import", { replace: true });
    } catch (err) {
      setError(err instanceof Error ? err.message : t("auth.registerFailed"));
    } finally {
      setBusy(false);
    }
  };

  return (
    <AuthShell title={t("auth.registerTitle")}>
      <form onSubmit={submit} className="space-y-3">
        <input
          className="input"
          placeholder={t("auth.username")}
          autoComplete="username"
          pattern="[A-Za-z0-9_\-]{3,32}"
          title={t("auth.usernameRule")}
          value={form.username}
          onChange={(e) => setForm({ ...form, username: e.target.value })}
          required
        />
        <input
          className="input"
          type="email"
          placeholder={t("auth.email")}
          autoComplete="email"
          value={form.email}
          onChange={(e) => setForm({ ...form, email: e.target.value })}
          required
        />
        <input
          className="input"
          type="password"
          placeholder={t("auth.passwordNew")}
          autoComplete="new-password"
          minLength={8}
          value={form.password}
          onChange={(e) => setForm({ ...form, password: e.target.value })}
          required
        />
        {error && <p className="text-sm text-red-400">{error}</p>}
        <p className="text-xs text-slate-400">
          <Trans
            i18nKey="auth.acceptPrivacy"
            components={{
              link: <Link to="/privacidad" className="text-indigo-400 hover:underline" />,
            }}
          />
        </p>
        <button className="btn-primary w-full" disabled={busy}>
          {t("auth.createAccount")}
        </button>
      </form>
      <SteamButton />
      <p className="text-center text-sm text-slate-400">
        {t("auth.haveAccount")}{" "}
        <Link to="/login" className="text-indigo-400 hover:underline">
          {t("auth.logIn")}
        </Link>
      </p>
    </AuthShell>
  );
}
