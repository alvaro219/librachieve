import { useEffect } from "react";
import { useTranslation } from "react-i18next";
import { useNavigate } from "react-router-dom";

import { useAuth } from "../auth/AuthContext";

/** Landing page after Steam sign-in: the backend has set the refresh cookie,
 * and AuthProvider has already exchanged it for a session on page load. */
export default function AuthCallbackPage() {
  const { user, loading } = useAuth();
  const navigate = useNavigate();
  const { t } = useTranslation();

  useEffect(() => {
    if (!loading) navigate(user ? "/" : "/login?error=SteamError", { replace: true });
  }, [loading, user, navigate]);

  return <p className="p-8 text-slate-400">{t("auth.connectingSteam")}</p>;
}
