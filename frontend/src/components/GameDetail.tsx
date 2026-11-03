import { useState } from "react";

import type { LibraryEntry } from "../api/types";
import AchievementList from "./AchievementList";
import { GameHeader, GameTabs, type GameTab } from "./GameHeader";
import Modal from "./Modal";
import { RatingSummary } from "./Ratings";

/** Read-only game view, used on public profiles. */
export default function GameDetail({ entry, onClose }: { entry: LibraryEntry; onClose: () => void }) {
  const [tab, setTab] = useState<GameTab>(entry.achievements_total > 0 ? "achievements" : "details");
  return (
    <Modal title={entry.game.title} onClose={onClose}>
      <GameHeader entry={entry} />
      <GameTabs entry={entry} tab={tab} onChange={setTab} />
      {tab === "details" ? (
        <div className="space-y-4">
          <RatingSummary game={entry.game} userRating={entry.user_rating} ownerLabel="Su nota" />
          <p className="text-sm text-slate-300">{entry.game.summary ?? "Sin descripción."}</p>
        </div>
      ) : (
        <AchievementList entryId={entry.id} />
      )}
    </Modal>
  );
}
