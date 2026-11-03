import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";

import { gamesApi, libraryApi } from "../api/endpoints";
import type { GameStatus, LibraryEntry } from "../api/types";
import { STATUS_LABELS, STATUS_ORDER } from "../lib/labels";
import AchievementList from "./AchievementList";
import { GameHeader, GameTabs, type GameTab } from "./GameHeader";
import FolderPicker from "./FolderPicker";
import Modal from "./Modal";
import { RatingInput, RatingSummary } from "./Ratings";

interface Props {
  entry: LibraryEntry;
  folders: string[];
  onClose: () => void;
}

export default function EntryEditor({ entry, folders, onClose }: Props) {
  const queryClient = useQueryClient();
  const [status, setStatus] = useState<GameStatus>(entry.status);
  const [folder, setFolder] = useState(entry.custom_folder ?? "");
  const [tab, setTab] = useState<GameTab>("details");
  const [rating, setRating] = useState<number | null>(entry.user_rating);
  const [hours, setHours] = useState(String(Math.round((entry.playtime_minutes / 60) * 10) / 10));

  const invalidate = () => {
    void queryClient.invalidateQueries({ queryKey: ["library"] });
    void queryClient.invalidateQueries({ queryKey: ["customFolders"] });
    void queryClient.invalidateQueries({ queryKey: ["stats"] });
  };

  const save = useMutation({
    mutationFn: async () => {
      await libraryApi.update(entry.id, {
        status,
        custom_folder: status === "other" ? folder.trim() || null : null,
        playtime_minutes: Math.max(0, Math.round(parseFloat(hours.replace(",", ".")) * 60) || 0),
      });
      // The score belongs to the game (shared by all its store entries), so it has its own call
      if (rating !== entry.user_rating) {
        await (rating === null
          ? gamesApi.unrate(entry.game.id)
          : gamesApi.rate(entry.game.id, rating));
      }
    },
    onSuccess: () => {
      invalidate();
      onClose();
    },
  });

  const remove = useMutation({
    mutationFn: () => libraryApi.remove(entry.id),
    onSuccess: () => {
      invalidate();
      onClose();
    },
  });

  const { game } = entry;
  const error = save.error ?? remove.error;

  return (
    <Modal title={game.title} onClose={onClose}>
      <GameHeader entry={entry} />
      <GameTabs entry={entry} tab={tab} onChange={setTab} />
      {tab === "achievements" ? (
        <AchievementList entryId={entry.id} />
      ) : (
        <>
      {game.summary && <p className="mb-5 line-clamp-4 text-sm text-slate-300">{game.summary}</p>}
      <div className="mb-5">
        <RatingSummary game={game} userRating={rating} />
      </div>

      <form
        className="space-y-4"
        onSubmit={(e) => {
          e.preventDefault();
          save.mutate();
        }}
      >
        <fieldset>
          <legend className="mb-2 text-sm font-medium text-slate-300">Categoría</legend>
          <div className="grid grid-cols-3 gap-2">
            {STATUS_ORDER.map((s) => (
              <button
                key={s}
                type="button"
                onClick={() => setStatus(s)}
                className={`rounded-lg border px-2 py-2 text-sm transition ${
                  status === s
                    ? "border-indigo-500 bg-indigo-500/20 text-white"
                    : "border-slate-700 text-slate-300 hover:border-slate-500"
                }`}
              >
                {STATUS_LABELS[s]}
              </button>
            ))}
          </div>
        </fieldset>

        {status === "other" && (
          <FolderPicker value={folder} folders={folders} onChange={setFolder} />
        )}

        <RatingInput value={rating} onChange={setRating} />

        <label className="block text-sm">
          <span className="mb-1 block text-slate-300">Horas jugadas</span>
          <input
            className="input"
            inputMode="decimal"
            value={hours}
            onChange={(e) => setHours(e.target.value)}
          />
        </label>

        {error && <p className="text-sm text-red-400">{error.message}</p>}

        <div className="flex justify-between gap-2 pt-2">
          <button
            type="button"
            className="btn-danger"
            disabled={remove.isPending}
            onClick={() => confirm(`¿Quitar «${game.title}» de tu biblioteca?`) && remove.mutate()}
          >
            Quitar
          </button>
          <div className="flex gap-2">
            <button type="button" className="btn-secondary" onClick={onClose}>
              Cancelar
            </button>
            <button type="submit" className="btn-primary" disabled={save.isPending}>
              Guardar
            </button>
          </div>
        </div>
      </form>
        </>
      )}
    </Modal>
  );
}
