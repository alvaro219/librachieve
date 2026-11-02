import { useState, type FormEvent } from "react";
import { Link, Navigate, useNavigate } from "react-router-dom";

import { useAuth } from "../auth/AuthContext";
import AuthShell, { SteamButton } from "./AuthShell";

export default function RegisterPage() {
  const { user, register } = useAuth();
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
      setError(err instanceof Error ? err.message : "Error al registrarse");
    } finally {
      setBusy(false);
    }
  };

  return (
    <AuthShell title="Crear cuenta">
      <form onSubmit={submit} className="space-y-3">
        <input
          className="input"
          placeholder="Nombre de usuario"
          autoComplete="username"
          pattern="[A-Za-z0-9_\-]{3,32}"
          title="3-32 caracteres: letras, números, _ o -"
          value={form.username}
          onChange={(e) => setForm({ ...form, username: e.target.value })}
          required
        />
        <input
          className="input"
          type="email"
          placeholder="Email"
          autoComplete="email"
          value={form.email}
          onChange={(e) => setForm({ ...form, email: e.target.value })}
          required
        />
        <input
          className="input"
          type="password"
          placeholder="Contraseña (mín. 8 caracteres)"
          autoComplete="new-password"
          minLength={8}
          value={form.password}
          onChange={(e) => setForm({ ...form, password: e.target.value })}
          required
        />
        {error && <p className="text-sm text-red-400">{error}</p>}
        <p className="text-xs text-slate-400">
          Al crear la cuenta aceptas la{" "}
          <Link to="/privacidad" className="text-indigo-400 hover:underline">
            política de privacidad
          </Link>
          .
        </p>
        <button className="btn-primary w-full" disabled={busy}>
          Crear cuenta
        </button>
      </form>
      <SteamButton />
      <p className="text-center text-sm text-slate-400">
        ¿Ya tienes cuenta?{" "}
        <Link to="/login" className="text-indigo-400 hover:underline">
          Inicia sesión
        </Link>
      </p>
    </AuthShell>
  );
}
