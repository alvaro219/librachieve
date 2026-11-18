import { useTranslation } from "react-i18next";
import { Link } from "react-router-dom";

export default function NotFoundPage() {
  const { t } = useTranslation();
  return (
    <div className="card mx-auto max-w-md text-center">
      <p className="mb-4 text-slate-300">{t("notFound.text")}</p>
      <Link to="/" className="btn-primary">
        {t("notFound.back")}
      </Link>
    </div>
  );
}
