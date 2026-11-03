// Single-series horizontal bar chart: one hue (no legend needed; the card title names it),
// bars capped at 12px with a rounded data-end and square baseline, value at the tip in text ink.

import type { ReactNode } from "react";

export interface BarDatum {
  label: string;
  /** Optional mark shown before the label (e.g. a store logo). */
  icon?: ReactNode;
  value: number;
  /** Shown at the bar tip and in the tooltip. Defaults to the raw value. */
  display?: string;
  /** Extra tooltip line. */
  detail?: string;
}

export default function BarList({ data, emptyText }: { data: BarDatum[]; emptyText: string }) {
  if (data.length === 0) return <p className="text-sm text-slate-500">{emptyText}</p>;
  const max = Math.max(...data.map((d) => d.value), 1);

  return (
    <ul className="space-y-3">
      {data.map((d) => {
        const display = d.display ?? String(d.value);
        const tooltip = [`${d.label}: ${display}`, d.detail].filter(Boolean).join("\n");
        return (
          <li key={d.label} title={tooltip} className="group">
            <div className="mb-1 flex justify-between gap-3 text-sm">
              <span className="flex items-center gap-1.5 truncate text-slate-300">
                {d.icon}
                {d.label}
              </span>
            </div>
            <div className="flex items-center gap-3">
              <div className="h-3 flex-1">
                <div
                  className="h-3 rounded-r bg-series-1 transition-[filter] group-hover:brightness-125"
                  style={{ width: `${Math.max((d.value / max) * 100, d.value > 0 ? 1.5 : 0)}%` }}
                />
              </div>
              <span className="w-16 shrink-0 text-right text-sm tabular-nums text-slate-200">
                {display}
              </span>
            </div>
          </li>
        );
      })}
    </ul>
  );
}
