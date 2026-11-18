import { useTranslation } from "react-i18next";

import LibraryBrowser from "../components/LibraryBrowser";

export default function LibraryPage() {
  const { t } = useTranslation();
  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">{t("library.title")}</h1>
      <LibraryBrowser />
    </div>
  );
}
