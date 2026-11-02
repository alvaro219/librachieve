import type { ReactNode } from "react";
import { Link } from "react-router-dom";

export default function AuthShell({ title, children }: { title: string; children: ReactNode }) {
  return (
    <div className="flex min-h-screen items-center justify-center p-4">
      <div className="w-full max-w-sm">
        <Link to="/" className="mb-8 flex items-center justify-center gap-2 text-2xl font-bold">
          <img src="/favicon.svg" alt="" className="h-9 w-9" />
          Librachieve
        </Link>
        <div className="card space-y-5">
          <h1 className="text-xl font-semibold">{title}</h1>
          {children}
        </div>
      </div>
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
