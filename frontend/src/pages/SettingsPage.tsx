import { useMutation } from "@tanstack/react-query";
import { useState } from "react";
import { Link, useSearchParams } from "react-router-dom";

import { authApi, usersApi } from "../api/endpoints";
import { useAuth } from "../auth/AuthContext";
import { useInstall } from "../lib/pwa";

const STEAM_MESSAGES: Record<string, { text: string; ok: boolean }> = {
  linked: { text: "Cuenta de Steam vinculada correctamente.", ok: true },
  taken: { text: "Esa cuenta de Steam ya está vinculada a otro usuario.", ok: false },
  expired: { text: "El enlace de vinculación caducó. Inténtalo de nuevo.", ok: false },
};

function AppSection() {
  const { state, install } = useInstall();
  return (
    <section className="card space-y-3">
      <h2 className="font-semibold">App para Windows y Android</h2>
      {state === "installed" ? (
        <p className="text-sm text-emerald-300">✓ Estás usando Librachieve como app.</p>
      ) : state === "elsewhere" ? (
        <p className="text-sm text-slate-300">
          <span className="text-emerald-300">✓ Ya la tienes instalada.</span> Ahora la estás viendo
          en el navegador: ábrela desde el menú Inicio o el escritorio (en el móvil, desde su icono)
          para usarla en su propia ventana.
        </p>
      ) : (
        <>
          <p className="text-sm text-slate-400">
            Instala Librachieve en tu ordenador o en el móvil: tendrá su propio icono y ventana, y
            se actualiza sola.
          </p>
          {state === "available" ? (
            <button className="btn-primary" onClick={() => void install()}>
              Instalar app
            </button>
          ) : state === "ios" ? (
            <p className="text-sm text-slate-300">
              En iPhone o iPad: abre la web en Safari, pulsa <strong>Compartir</strong> y luego{" "}
              <strong>Añadir a pantalla de inicio</strong>.
            </p>
          ) : (
            <p className="text-sm text-slate-300">
              Ábrela en Chrome, Edge o Brave y elige <strong>Instalar Librachieve</strong> en el menú del
              navegador (en Android, <strong>Añadir a pantalla de inicio</strong>).
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
      <h2 className="font-semibold">Contraseña</h2>
      {!hasPassword && (
        <p className="text-sm text-slate-400">
          Entras con Steam. Si creas una contraseña, también podrás entrar con tu nombre de usuario.
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
            placeholder="Contraseña actual"
            value={current}
            required
            onChange={(e) => setCurrent(e.target.value)}
          />
        )}
        <input
          className="input"
          type="password"
          autoComplete="new-password"
          placeholder="Nueva contraseña (mínimo 8 caracteres)"
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
          placeholder="Repite la nueva contraseña"
          value={repeat}
          required
          onChange={(e) => setRepeat(e.target.value)}
        />
        {mismatch && <p className="text-sm text-amber-300">Las contraseñas no coinciden.</p>}
        {change.error && <p className="text-sm text-red-400">{change.error.message}</p>}
        {change.isSuccess && <p className="text-sm text-emerald-400">✓ Contraseña guardada.</p>}
        <button
          className="btn-primary justify-self-start"
          disabled={change.isPending || mismatch || next.length < 8}
        >
          {hasPassword ? "Cambiar contraseña" : "Crear contraseña"}
        </button>
      </form>
    </section>
  );
}

export default function SettingsPage() {
  const { user, setUser, logout } = useAuth();
  const [params] = useSearchParams();
  const [username, setUsername] = useState(user!.username);
  const steamMsg = STEAM_MESSAGES[params.get("steam") ?? ""];

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
        <h1 className="text-2xl font-bold">Ajustes</h1>
        {/* On wide screens "Salir" lives in the header */}
        <button onClick={() => void logout()} className="btn-secondary px-3 py-1.5 md:hidden">
          Cerrar sesión
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
          {steamMsg.text}
        </p>
      )}

      <section className="card space-y-4">
        <h2 className="font-semibold">Perfil</h2>
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
            Guardar
          </button>
        </form>

        <label className="flex items-center justify-between gap-4">
          <span>
            <span className="block text-sm font-medium">Perfil público</span>
            <span className="text-xs text-slate-400">
              Cualquiera podrá ver tu biblioteca y estadísticas en{" "}
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
          <p className="text-sm text-slate-400">Vinculada: SteamID {user.steam_id}</p>
        ) : (
          <button
            className="btn-secondary"
            disabled={linkSteam.isPending}
            onClick={() => linkSteam.mutate()}
          >
            Vincular cuenta de Steam
          </button>
        )}
      </section>

      <AppSection />

      <section className="card space-y-3 border-red-900/60">
        <h2 className="font-semibold text-red-300">Zona peligrosa</h2>
        <p className="text-sm text-slate-400">
          Eliminar la cuenta borra tu biblioteca y tus estadísticas de forma permanente.
        </p>
        <button
          className="btn-danger"
          disabled={deleteAccount.isPending}
          onClick={() =>
            confirm("¿Seguro que quieres eliminar tu cuenta? No se puede deshacer.") &&
            deleteAccount.mutate()
          }
        >
          Eliminar cuenta
        </button>
      </section>
    </div>
  );
}
