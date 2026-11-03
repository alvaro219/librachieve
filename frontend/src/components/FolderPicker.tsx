interface Props {
  value: string;
  folders: string[];
  onChange: (folder: string) => void;
}

/** Free-text folder name with the existing folders as one-click chips (no native datalist). */
export default function FolderPicker({ value, folders, onChange }: Props) {
  const typed = value.trim().toLowerCase();
  const matches = folders.filter((f) => !typed || f.toLowerCase().includes(typed));
  const isNew = typed !== "" && !folders.some((f) => f.toLowerCase() === typed);

  return (
    <div className="text-sm">
      <label htmlFor="folder-input" className="mb-1 block text-slate-300">
        Carpeta
      </label>
      <input
        id="folder-input"
        className="input"
        value={value}
        maxLength={64}
        autoComplete="off"
        placeholder={folders.length ? "Elige una o escribe una nueva…" : "p. ej. Cooperativo, Retro…"}
        onChange={(e) => onChange(e.target.value)}
      />

      {(matches.length > 0 || isNew) && (
        <div className="mt-2 flex flex-wrap items-center gap-2">
          {matches.map((f) => {
            const selected = f.toLowerCase() === typed;
            return (
              <button
                key={f}
                type="button"
                aria-pressed={selected}
                onClick={() => onChange(selected ? "" : f)}
                className={`rounded-lg border px-3 py-1 text-xs transition ${
                  selected
                    ? "border-indigo-500 bg-indigo-500/20 text-white"
                    : "border-slate-700 text-slate-300 hover:border-slate-500 hover:text-white"
                }`}
              >
                📁 {f}
              </button>
            );
          })}
          {isNew && (
            <span className="text-xs text-slate-400">
              Se creará la carpeta «{value.trim()}»
            </span>
          )}
        </div>
      )}
    </div>
  );
}
