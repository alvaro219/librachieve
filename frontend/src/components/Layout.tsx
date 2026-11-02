import { Link, NavLink, Outlet } from "react-router-dom";

import { useAuth } from "../auth/AuthContext";

const navClass = ({ isActive }: { isActive: boolean }) =>
  `rounded-lg px-3 py-2 text-sm font-medium transition ${
    isActive ? "bg-slate-800 text-white" : "text-slate-400 hover:text-white"
  }`;

export default function Layout() {
  const { user, logout } = useAuth();

  return (
    <div className="min-h-screen">
      <header className="sticky top-0 z-20 border-b border-slate-800 bg-slate-950/90 backdrop-blur">
        <div className="mx-auto flex max-w-7xl items-center gap-6 px-4 py-3">
          <Link to="/" className="flex items-center gap-2 text-lg font-bold tracking-tight">
            <img src="/favicon.svg" alt="" className="h-7 w-7" />
            Librachieve
          </Link>
          {user && (
            <nav className="flex gap-1">
              <NavLink to="/" end className={navClass}>
                Biblioteca
              </NavLink>
              <NavLink to="/stats" className={navClass}>
                Estadísticas
              </NavLink>
              <NavLink to="/import" className={navClass}>
                Importar
              </NavLink>
            </nav>
          )}
          <div className="ml-auto flex items-center gap-3">
            {user ? (
              <>
                <NavLink to="/settings" className={navClass}>
                  <span className="flex items-center gap-2">
                    {user.avatar_url && (
                      <img src={user.avatar_url} alt="" className="h-6 w-6 rounded-full" />
                    )}
                    {user.username}
                  </span>
                </NavLink>
                <button onClick={() => void logout()} className="btn-secondary px-3 py-1.5">
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
      <main className="mx-auto max-w-7xl px-4 py-8">
        <Outlet />
      </main>
    </div>
  );
}
