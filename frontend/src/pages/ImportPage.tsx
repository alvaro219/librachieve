import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useRef, useState } from "react";

import { authApi, syncApi } from "../api/endpoints";
import type { Platform } from "../api/types";
import { useAuth } from "../auth/AuthContext";
import PlatformIcon from "../components/PlatformIcon";
import { PLATFORM_LABELS, SYNC_STATUS_LABELS, formatDate } from "../lib/labels";

const MANUAL_PLATFORMS: Platform[] = ["epic", "gog", "amazon", "other"];

const EXAMPLE_JSON = `[
  { "title": "Hades", "playtime_hours": 25, "status": "completed" },
  { "title": "Celeste", "playtime_minutes": 300 }
]`;
const EXAMPLE_CSV = `title,hours,status
Hades,25,completed
Celeste,5,playing`;

export default function ImportPage() {
  const { user } = useAuth();
  const queryClient = useQueryClient();
  const fileRef = useRef<HTMLInputElement>(null);
  const [platform, setPlatform] = useState<Platform>("epic");

  const jobs = useQuery({
    queryKey: ["syncJobs"],
    queryFn: syncApi.jobs,
    // Poll while a Steam sync is queued or running.
    refetchInterval: (q) =>
      q.state.data?.some((j) => j.status === "pending" || j.status === "running") ? 2000 : false,
  });

  const onImported = () => {
    void queryClient.invalidateQueries({ queryKey: ["syncJobs"] });
    void queryClient.invalidateQueries({ queryKey: ["library"] });
    void queryClient.invalidateQueries({ queryKey: ["stats"] });
  };

  const steamSync = useMutation({ mutationFn: syncApi.steam, onSuccess: onImported });
  const undo = useMutation({ mutationFn: syncApi.undo, onSuccess: onImported });
  const linkSteam = useMutation({
    mutationFn: authApi.steamLinkUrl,
    onSuccess: ({ url }) => window.location.assign(url),
  });
  const fileImport = useMutation({
    mutationFn: (file: File) => syncApi.importFile(platform, file),
    onSuccess: () => {
      onImported();
      if (fileRef.current) fileRef.current.value = "";
    },
  });

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">Importar biblioteca</h1>

      <div className="grid gap-6 lg:grid-cols-2">
        <section className="card space-y-4">
          <h2 className="flex items-center gap-2 text-lg font-semibold">
            <PlatformIcon platform="steam" title="" className="h-5 w-5" />
            Steam
          </h2>
          {user?.steam_id ? (
            <>
              <p className="text-sm text-slate-400">
                Cuenta vinculada (SteamID {user.steam_id}). La sincronización importa todos tus
                juegos y su tiempo de juego. Necesitas tener los «Detalles de juegos» como
                públicos en la privacidad de Steam.
              </p>
              <button
                className="btn-primary"
                disabled={steamSync.isPending}
                onClick={() => steamSync.mutate()}
              >
                Sincronizar con Steam
              </button>
            </>
          ) : (
            <>
              <p className="text-sm text-slate-400">
                Vincula tu cuenta de Steam para importar tus juegos automáticamente.
              </p>
              <button
                className="btn-primary"
                disabled={linkSteam.isPending}
                onClick={() => linkSteam.mutate()}
              >
                Vincular Steam
              </button>
            </>
          )}
          {(steamSync.error ?? linkSteam.error) && (
            <p className="text-sm text-red-400">{(steamSync.error ?? linkSteam.error)!.message}</p>
          )}
        </section>

        <section className="card space-y-4">
          <h2 className="flex items-center gap-2 text-lg font-semibold">
            <span className="flex gap-1.5 text-slate-200">
              {(["epic", "gog", "amazon"] as const).map((p) => (
                <PlatformIcon key={p} platform={p} title="" className="h-5 w-5" />
              ))}
            </span>
            Epic, GOG, Amazon u otras (JSON / CSV)
          </h2>
          <div className="rounded-lg border border-indigo-500/40 bg-indigo-500/10 p-3 text-sm text-slate-300">
            <p className="mb-1 font-medium text-indigo-200">
              Lo más fácil: exporta tu biblioteca con Playnite
            </p>
            <ol className="list-decimal space-y-0.5 pl-5">
              <li>
                Instala{" "}
                <a
                  href="https://playnite.link"
                  target="_blank"
                  rel="noreferrer"
                  className="text-indigo-300 underline"
                >
                  Playnite
                </a>{" "}
                (gratis) y conecta tus tiendas: Epic, GOG, Amazon…
              </li>
              <li>
                Añade un complemento exportador de biblioteca (por ejemplo «Library Exporter») y,
                en los campos a exportar, marca <strong>Nombre</strong> y{" "}
                <strong>Fuente</strong> (para que cada juego vaya a su tienda). Opcionales:{" "}
                <em>Estado de finalización</em>, <em>Tiempo jugado</em> y <em>Favorito</em>.
              </li>
              <li>Exporta a CSV y súbelo aquí. Da igual que Playnite esté en español o en inglés.</li>
            </ol>
            <p className="mt-1 text-xs text-slate-400">
              Si el fichero no tiene la columna Fuente, todos los juegos se asignan a la tienda que
              elijas abajo. Para actualizar, vuelve a exportar y subir: no se duplica nada y, si el
              fichero trae estado, se aplica.
            </p>
          </div>
          <div className="flex flex-wrap gap-3">
            <select
              className="input w-auto"
              value={platform}
              onChange={(e) => setPlatform(e.target.value as Platform)}
            >
              {MANUAL_PLATFORMS.map((p) => (
                <option key={p} value={p}>
                  {PLATFORM_LABELS[p]}
                </option>
              ))}
            </select>
            <input
              ref={fileRef}
              type="file"
              accept=".json,.csv,.tsv,application/json,text/csv"
              className="text-sm text-slate-300 file:mr-3 file:rounded-lg file:border-0 file:bg-slate-800 file:px-3 file:py-2 file:text-slate-200"
              onChange={(e) => {
                const file = e.target.files?.[0];
                if (file) fileImport.mutate(file);
              }}
            />
          </div>
          {fileImport.isPending && <p className="text-sm text-slate-400">Importando…</p>}
          {fileImport.error && <p className="text-sm text-red-400">{fileImport.error.message}</p>}
          {fileImport.data && (
            <p className="text-sm text-emerald-400">
              {fileImport.data.imported_count} juegos importados. Las portadas y géneros se
              añadirán en segundo plano.
            </p>
          )}
          <details className="text-sm text-slate-400">
            <summary className="cursor-pointer text-slate-300">Formato del fichero</summary>
            <p className="mt-2">
              Columnas reconocidas: <code>title</code> o <code>name</code> (obligatoria),{" "}
              <code>playtime_minutes</code> o <code>playtime_hours</code>/<code>hours</code>,{" "}
              <code>status</code> (backlog, playing, completed, dropped, wishlist, other),{" "}
              <code>last_played</code>, <code>favorite</code> y <code>source</code> /{" "}
              <code>sourceName</code> (la tienda de cada juego; si existe, manda sobre la
              plataforma elegida arriba).
            </p>
            <div className="mt-2 grid gap-2 sm:grid-cols-2">
              <pre className="overflow-x-auto rounded-lg bg-slate-950 p-3 text-xs">
                {EXAMPLE_JSON}
              </pre>
              <pre className="overflow-x-auto rounded-lg bg-slate-950 p-3 text-xs">
                {EXAMPLE_CSV}
              </pre>
            </div>
          </details>
        </section>
      </div>

      <section className="card">
        <h2 className="mb-4 text-lg font-semibold">Historial</h2>
        {jobs.data?.length ? (
          <table className="w-full text-left text-sm">
            <thead className="text-slate-400">
              <tr>
                <th className="pb-2 font-medium">Fecha</th>
                <th className="pb-2 font-medium">Plataforma</th>
                <th className="pb-2 font-medium">Estado</th>
                <th className="pb-2 text-right font-medium">Juegos</th>
                <th className="pb-2" />
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800">
              {jobs.data.map((j) => (
                <tr key={j.id}>
                  <td className="py-2">{formatDate(j.created_at)}</td>
                  <td>
                    <span className="flex items-center gap-1.5">
                      <PlatformIcon platform={j.platform} title="" className="h-4 w-4" />
                      {PLATFORM_LABELS[j.platform]}
                    </span>
                  </td>
                  <td>
                    <span
                      className={
                        j.status === "failed"
                          ? "text-red-400"
                          : j.status === "success"
                            ? "text-emerald-400"
                            : j.status === "reverted"
                              ? "text-slate-400"
                              : "text-amber-300"
                      }
                    >
                      {
                        { failed: "✕ ", success: "✓ ", reverted: "↶ ", pending: "⟳ ", running: "⟳ " }[
                          j.status
                        ]
                      }
                      {SYNC_STATUS_LABELS[j.status]}
                    </span>
                    {j.error && <p className="text-xs text-slate-500">{j.error}</p>}
                  </td>
                  <td className="text-right tabular-nums">{j.imported_count}</td>
                  <td className="w-32 py-1 text-right">
                    {j.undoable && (
                      <button
                        type="button"
                        className="btn-secondary px-3 py-1 text-xs"
                        disabled={undo.isPending}
                        onClick={() =>
                          confirm(
                            `¿Deshacer esta importación de ${PLATFORM_LABELS[j.platform]}?

` +
                              "Se quitarán los juegos que añadió y los que ya tenías volverán a su " +
                              "estado anterior.",
                          ) && undo.mutate(j.id)
                        }
                      >
                        ↶ Deshacer
                      </button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        ) : (
          <p className="text-sm text-slate-500">Todavía no has importado nada.</p>
        )}
        {undo.error && <p className="mt-3 text-sm text-red-400">{undo.error.message}</p>}
        {undo.isSuccess && !undo.isPending && (
          <p className="mt-3 text-sm text-slate-400">Importación deshecha.</p>
        )}
      </section>
    </div>
  );
}
