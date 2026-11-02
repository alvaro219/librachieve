import { Link } from "react-router-dom";

import { SITE } from "../lib/site";

export default function Footer() {
  return (
    <footer className="mt-16 border-t border-slate-800 py-6 text-xs text-slate-500">
      <div className="mx-auto flex max-w-7xl flex-wrap items-center gap-x-4 gap-y-2 px-4">
        <span>© 2026 {SITE.name}</span>
        <Link to="/privacidad" className="hover:text-slate-300">
          Privacidad
        </Link>
        <Link to="/aviso-legal" className="hover:text-slate-300">
          Aviso legal
        </Link>
        <a href={SITE.repoUrl} target="_blank" rel="noreferrer" className="hover:text-slate-300">
          Código fuente
        </a>
        <span className="ml-auto">
          Datos de juegos de{" "}
          <a href="https://www.igdb.com" target="_blank" rel="noreferrer" className="underline">
            IGDB.com
          </a>{" "}
          ·{" "}
          <a href="https://steamcommunity.com" target="_blank" rel="noreferrer" className="underline">
            Powered by Steam
          </a>
          . No afiliado con Valve, Epic Games, GOG, Amazon ni Twitch.
        </span>
      </div>
    </footer>
  );
}
