import { useState } from "react";

import type { LibraryEntry } from "../api/types";
import AchievementList from "./AchievementList";
import { GameHeader, GameTabs, type GameTab } from "./GameHeader";
import Modal from "./Modal";

/** Read-only game view, used on public profiles. */
export default function GameDetail({ entry, onClose }: { entry: LibraryEntry; onClose: () => void }) {
  const [tab, setTab] = useState<GameTab>(entry.achievements_total > 0 ? "achievements" : "details");
  return (
    <Modal title={entry.game.title} onClose={onClose}>
      <GameHeader entry={entry} />
      <GameTabs entry={entry} tab={tab} onChange={setTab} />
      {tab === "details" ? (
        <p className="text-sm text-slate-300">{entry.game.summary ?? "Sin descripción."}</p>
      ) : (
        <AchievementList entryId={entry.id} />
      )}
    </Modal>
  );
}
