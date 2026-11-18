import { Trans, useTranslation } from "react-i18next";
import { Link } from "react-router-dom";

import { SITE } from "../lib/site";
import LanguageSelect from "./LanguageSelect";

export default function Footer() {
  const { t } = useTranslation();
  return (
    <footer className="mt-16 border-t border-slate-800 py-6 text-xs text-slate-500">
      <div className="mx-auto flex max-w-7xl flex-wrap items-center gap-x-4 gap-y-2 px-4">
        <span>© 2026 {SITE.name}</span>
        <Link to="/privacidad" className="hover:text-slate-300">
          {t("footer.privacy")}
        </Link>
        <Link to="/aviso-legal" className="hover:text-slate-300">
          {t("footer.legal")}
        </Link>
        <a href={SITE.repoUrl} target="_blank" rel="noreferrer" className="hover:text-slate-300">
          {t("footer.source")}
        </a>
        <LanguageSelect className="text-xs" />
        <span className="ml-auto">
          <Trans
            i18nKey="footer.credits"
            components={{
              igdb: (
                <a
                  href="https://www.igdb.com"
                  target="_blank"
                  rel="noreferrer"
                  className="underline"
                />
              ),
              steam: (
                <a
                  href="https://steamcommunity.com"
                  target="_blank"
                  rel="noreferrer"
                  className="underline"
                />
              ),
            }}
          />
        </span>
      </div>
    </footer>
  );
}
