import { useState, type FormEvent } from "react";
import { Link, Navigate, useLocation, useNavigate, useSearchParams } from "react-router-dom";

import { useAuth } from "../auth/AuthContext";
import AuthShell, { SteamButton } from "./AuthShell";

const STEAM_ERRORS: Record<string, string> = {
  SteamError: "No se pudo verificar el inicio de sesión con Steam.",
};

export default function LoginPage() {
  const { user, login } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [params] = useSearchParams();
  const [form, setForm] = useState({ login: "", password: "" });
  const [error, setError] = useState<string | null>(
    params.get("error") ? (STEAM_ERRORS[params.get("error")!] ?? STEAM_ERRORS.SteamError!) : null,
  );
  const [busy, setBusy] = useState(false);
  const from = (location.state as { from?: string } | null)?.from ?? "/";

  if (user) return <Navigate to={from} replace />;

  const submit = async (e: FormEvent) => {
    e.preventDefault();
    setBusy(true);
    setError(null);
    try {
      await login(form.login, form.password);
      navigate(from, { replace: true });
    } catch (err) {
      setError(err instanceof Error ? err.message : "Error al iniciar sesión");
    } finally {
      setBusy(false);
    }
  };

  return (
    <AuthShell title="Iniciar sesión">
      <form onSubmit={submit} className="space-y-3">
        <input
          className="input"
          placeholder="Usuario o email"
          autoComplete="username"
          value={form.login}
          onChange={(e) => setForm({ ...form, login: e.target.value })}
          required
        />
        <input
          className="input"
          type="password"
          placeholder="Contraseña"
          autoComplete="current-password"
          value={form.password}
          onChange={(e) => setForm({ ...form, password: e.target.value })}
          required
        />
        {error && <p className="text-sm text-red-400">{error}</p>}
        <button className="btn-primary w-full" disabled={busy}>
          Entrar
        </button>
      </form>
      <div className="flex items-center gap-3 text-xs text-slate-500">
        <div className="h-px flex-1 bg-slate-800" />o<div className="h-px flex-1 bg-slate-800" />
      </div>
      <SteamButton />
      <p className="text-center text-sm text-slate-400">
        ¿No tienes cuenta?{" "}
        <Link to="/register" className="text-indigo-400 hover:underline">
          Regístrate
        </Link>
      </p>
    </AuthShell>
  );
}
