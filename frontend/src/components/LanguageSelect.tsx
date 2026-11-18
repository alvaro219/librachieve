import { useTranslation } from "react-i18next";

import { LANGUAGES, currentLanguage } from "../i18n";

/** Language picker; the choice is remembered in this browser. */
export default function LanguageSelect({ className = "" }: { className?: string }) {
  const { t, i18n } = useTranslation();
  return (
    <select
      className={`cursor-pointer rounded-md border border-slate-700 bg-slate-900 px-2 py-1 text-slate-300 hover:border-slate-500 focus:border-indigo-500 focus:outline-none ${className}`}
      value={currentLanguage()}
      onChange={(e) => void i18n.changeLanguage(e.target.value)}
      aria-label={t("common.language")}
    >
      {LANGUAGES.map((l) => (
        <option key={l.code} value={l.code}>
          {l.label}
        </option>
      ))}
    </select>
  );
}
