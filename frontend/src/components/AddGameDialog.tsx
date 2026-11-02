import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useEffect, useState } from "react";

import { ApiError } from "../api/client";
import { gamesApi, libraryApi } from "../api/endpoints";
import type { GameStatus, LibraryEntryCreate, Platform } from "../api/types";
import { PLATFORMS, PLATFORM_LABELS, STATUS_LABELS, STATUS_ORDER } from "../lib/labels";
import Modal from "./Modal";

function useDebounced<T>(value: T, ms: number): T {
  const [debounced, setDebounced] = useState(value);
  useEffect(() => {
    const t = setTimeout(() => setDebounced(value), ms);
    return () => clearTimeout(t);
  }, [value, ms]);
  return debounced;
}

export default function AddGameDialog({ onClose }: { onClose: () => void }) {
  const queryClient = useQueryClient();
  const [query, setQuery] = useState("");
  const [platform, setPlatform] = useState<Platform>("other");
  const [status, setStatus] = useState<GameStatus>("backlog");
  const debounced = useDebounced(query.trim(), 400);

  const search = useQuery({
    queryKey: ["igdbSearch", debounced],
    queryFn: () => gamesApi.search(debounced),
    enabled: debounced.length >= 2,
    retry: false,
  });
  const igdbUnavailable = search.error instanceof ApiError && search.error.status === 503;

  const add = useMutation({
    mutationFn: (body: LibraryEntryCreate) => libraryApi.add({ ...body, platform, status }),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["library"] });
      void queryClient.invalidateQueries({ queryKey: ["stats"] });
      onClose();
    },
  });

  return (
    <Modal title="Añadir juego" onClose={onClose}>
      <div className="space-y-4">
        <div className="grid grid-cols-2 gap-3">
          <label className="text-sm">
            <span className="mb-1 block text-slate-300">Plataforma</span>
            <select
              className="input"
              value={platform}
              onChange={(e) => setPlatform(e.target.value as Platform)}
            >
              {PLATFORMS.map((p) => (
                <option key={p} value={p}>
                  {PLATFORM_LABELS[p]}
                </option>
              ))}
            </select>
          </label>
          <label className="text-sm">
            <span className="mb-1 block text-slate-300">Categoría</span>
            <select
              className="input"
              value={status}
              onChange={(e) => setStatus(e.target.value as GameStatus)}
            >
              {STATUS_ORDER.map((s) => (
                <option key={s} value={s}>
                  {STATUS_LABELS[s]}
                </option>
              ))}
            </select>
          </label>
        </div>

        <input
          autoFocus
          className="input"
          placeholder="Busca un juego por título…"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
        />

        {igdbUnavailable && (
          <p className="text-xs text-amber-300">
            La búsqueda en IGDB no está configurada; se añadirá solo con el título.
          </p>
        )}
        {search.isFetching && <p className="text-sm text-slate-400">Buscando…</p>}

        <ul className="max-h-72 space-y-1 overflow-y-auto">
          {search.data?.map((r) => (
            <li key={r.igdb_id}>
              <button
                type="button"
                disabled={add.isPending}
                onClick={() => add.mutate({ igdb_id: r.igdb_id })}
                className="flex w-full items-center gap-3 rounded-lg p-2 text-left hover:bg-slate-800"
              >
                {r.cover_url ? (
                  <img src={r.cover_url} alt="" className="h-14 w-10 rounded object-cover" />
                ) : (
                  <div className="h-14 w-10 rounded bg-slate-800" />
                )}
                <div>
                  <p className="text-sm font-medium">{r.title}</p>
                  <p className="text-xs text-slate-400">
                    {[r.release_date?.slice(0, 4), r.genres.slice(0, 2).join(", ")]
                      .filter(Boolean)
                      .join(" · ")}
                  </p>
                </div>
              </button>
            </li>
          ))}
        </ul>

        {query.trim().length >= 1 && (
          <button
            type="button"
            className="btn-secondary w-full"
            disabled={add.isPending}
            onClick={() => add.mutate({ title: query.trim() })}
          >
            Añadir «{query.trim()}» sin datos de IGDB
          </button>
        )}

        {add.error && <p className="text-sm text-red-400">{add.error.message}</p>}
      </div>
    </Modal>
  );
}
