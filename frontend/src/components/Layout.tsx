import type { ReactNode } from "react";
import { Link, NavLink, Outlet } from "react-router-dom";

import { useAuth } from "../auth/AuthContext";
import Footer from "./Footer";
import { useFriends } from "./FriendButton";

const navClass = ({ isActive }: { isActive: boolean }) =>
  `rounded-lg px-3 py-2 text-sm font-medium transition ${
    isActive ? "bg-slate-800 text-white" : "text-slate-400 hover:text-white"
  }`;

const tabClass = ({ isActive }: { isActive: boolean }) =>
  `relative flex flex-1 flex-col items-center gap-0.5 py-2 text-[11px] font-medium transition ${
    isActive ? "text-indigo-300" : "text-slate-400"
  }`;

/** 24x24 outline icons for the mobile tab bar */
const ICONS: Record<string, ReactNode> = {
  library: <path d="M4 5h4v14H4zM10 5h4v14h-4zM16.5 5.5l3.8 1-3.4 13-3.8-1z" />,
  stats: <path d="M4 20V10M10 20V4M16 20v-7M21 20H3" />,
  import: <path d="M12 4v11m0 0-4-4m4 4 4-4M5 20h14" />,
  friends: (
    <path d="M9 11a3.5 3.5 0 1 0 0-7 3.5 3.5 0 0 0 0 7Zm-6 9c0-3.3 2.7-6 6-6s6 2.7 6 6M16 4.5a3.5 3.5 0 0 1 0 6.5M18 14.3c1.8.9 3 2.9 3 5.2" />
  ),
  admin: <path d="M12 3 4 6v6c0 4.5 3.4 8.3 8 9 4.6-.7 8-4.5 8-9V6z" />,
};

function TabIcon({ name }: { name: keyof typeof ICONS }) {
  return (
    <svg
      viewBox="0 0 24 24"
      className="h-6 w-6"
      fill="none"
      stroke="currentColor"
      strokeWidth={1.8}
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden
    >
      {ICONS[name]}
    </svg>
  );
}

function Badge({ count, className = "" }: { count: number; className?: string }) {
  if (count <= 0) return null;
  return (
    <span
      className={`rounded-full bg-indigo-500 px-1.5 text-xs font-semibold text-white ${className}`}
      title={`${count} solicitudes de amistad`}
    >
      {count}
    </span>
  );
}

function UserAvatar({ src, name }: { src: string | null; name: string }) {
  return src ? (
    <img src={src} alt="" className="h-7 w-7 rounded-full" />
  ) : (
    <span className="flex h-7 w-7 items-center justify-center rounded-full bg-indigo-600 text-xs font-semibold uppercase">
      {name.slice(0, 1)}
    </span>
  );
}

export default function Layout() {
  const { user, logout } = useAuth();
  const friends = useFriends(!!user);
  const pending = user ? (friends.data?.incoming.length ?? 0) : 0;
  const isAdmin = user?.role === "admin";

  return (
    <div className="flex min-h-screen flex-col">
      <header className="sticky top-0 z-20 border-b border-slate-800 bg-slate-950/90 pt-[env(safe-area-inset-top)] backdrop-blur">
        <div className="mx-auto flex max-w-7xl items-center gap-6 px-4 py-3">
          <Link to="/" className="flex shrink-0 items-center gap-2 text-lg font-bold tracking-tight">
            <img
              src="/logo-160.webp"
              srcSet="/logo-160.webp 1x, /logo-320.webp 2x"
              alt=""
              className="h-9 w-9 rounded-lg"
            />
            Librachieve
          </Link>
          {user && (
            <nav className="hidden gap-1 md:flex">
              <NavLink to="/" end className={navClass}>
                Biblioteca
              </NavLink>
              <NavLink to="/stats" className={navClass}>
                Estadísticas
              </NavLink>
              <NavLink to="/import" className={navClass}>
                Importar
              </NavLink>
              <NavLink to="/amigos" className={navClass}>
                <span className="flex items-center gap-1.5">
                  Amigos
                  <Badge count={pending} />
                </span>
              </NavLink>
              {isAdmin && (
                <NavLink to="/admin" className={navClass}>
                  Admin
                </NavLink>
              )}
            </nav>
          )}
          <div className="ml-auto flex min-w-0 items-center gap-3">
            {user ? (
              <>
                {/* Admins only; on wide screens it's in the main nav */}
                {isAdmin && (
                  <NavLink
                    to="/admin"
                    className={({ isActive }) =>
                      `rounded-lg p-2 transition md:hidden ${
                        isActive ? "bg-slate-800 text-white" : "text-slate-400 hover:text-white"
                      }`
                    }
                    title="Administración"
                    aria-label="Administración"
                  >
                    <TabIcon name="admin" />
                  </NavLink>
                )}
                <NavLink to="/settings" className={navClass} title="Ajustes">
                  <span className="flex min-w-0 items-center gap-2">
                    <UserAvatar src={user.avatar_url} name={user.username} />
                    <span className="hidden truncate sm:inline">{user.username}</span>
                  </span>
                </NavLink>
                <button
                  onClick={() => void logout()}
                  className="btn-secondary hidden px-3 py-1.5 md:inline-flex"
                >
                  Salir
                </button>
              </>
            ) : (
              <Link to="/login" className="btn-primary">
                Entrar
              </Link>
            )}
          </div>
        </div>
      </header>
      <main className="mx-auto w-full max-w-7xl flex-1 px-4 py-6 md:py-8">
        <Outlet />
      </main>
      <Footer />
      {user && (
        <>
          {/* Room so the fixed tab bar never covers the end of the page */}
          <div className="h-[calc(4rem+env(safe-area-inset-bottom))] md:hidden" aria-hidden />
          <nav
            className="fixed inset-x-0 bottom-0 z-30 flex border-t border-slate-800 bg-slate-950/95 pb-[env(safe-area-inset-bottom)] backdrop-blur md:hidden"
            aria-label="Secciones"
          >
            <NavLink to="/" end className={tabClass}>
              <TabIcon name="library" />
              Biblioteca
            </NavLink>
            <NavLink to="/stats" className={tabClass}>
              <TabIcon name="stats" />
              Estadísticas
            </NavLink>
            <NavLink to="/import" className={tabClass}>
              <TabIcon name="import" />
              Importar
            </NavLink>
            <NavLink to="/amigos" className={tabClass}>
              <TabIcon name="friends" />
              Amigos
              <Badge count={pending} className="absolute left-1/2 top-1 ml-2" />
            </NavLink>
          </nav>
        </>
      )}
    </div>
  );
}
