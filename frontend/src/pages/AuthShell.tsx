import type { ReactNode } from "react";
import { Link } from "react-router-dom";

import Footer from "../components/Footer";

export default function AuthShell({ title, children }: { title: string; children: ReactNode }) {
  return (
    <div className="flex min-h-screen flex-col">
      <div className="flex flex-1 items-center justify-center p-4">
        <div className="w-full max-w-sm">
          <Link to="/" className="mb-6 flex justify-center">
            <img
              src="/logo-320.webp"
              srcSet="/logo-320.webp 1x, /logo-640.webp 2x"
              alt="Librachieve"
              className="h-40 w-40 rounded-3xl"
            />
          </Link>
          <div className="card space-y-5">
            <h1 className="text-xl font-semibold">{title}</h1>
            {children}
          </div>
        </div>
      </div>
      <Footer />
    </div>
  );
}

export function SteamButton() {
  return (
    <a href="/api/auth/steam/login" className="btn-secondary w-full">
      Entrar con Steam
    </a>
  );
}
