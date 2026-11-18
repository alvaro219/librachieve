import i18n from "i18next";
import LanguageDetector from "i18next-browser-languagedetector";
import { initReactI18next } from "react-i18next";

import en from "./locales/en";
import es from "./locales/es";
import fr from "./locales/fr";

export const LANGUAGES = [
  { code: "es", label: "Español" },
  { code: "en", label: "English" },
  { code: "fr", label: "Français" },
] as const;
export type Language = (typeof LANGUAGES)[number]["code"];

/** BCP 47 locale for dates and numbers */
export const LOCALES: Record<Language, string> = { es: "es-ES", en: "en-GB", fr: "fr-FR" };

void i18n
  .use(LanguageDetector)
  .use(initReactI18next)
  .init({
    resources: { es: { translation: es }, en: { translation: en }, fr: { translation: fr } },
    supportedLngs: LANGUAGES.map((l) => l.code),
    nonExplicitSupportedLngs: true, // "es-MX", "fr-CA"… use es / fr
    load: "languageOnly",
    fallbackLng: "en", // any other browser language
    interpolation: { escapeValue: false }, // React already escapes
    detection: {
      order: ["localStorage", "navigator"],
      lookupLocalStorage: "lang",
      caches: ["localStorage"],
    },
    returnNull: false,
  });

const syncHtmlLang = (lng: string) => document.documentElement.setAttribute("lang", lng);
syncHtmlLang(i18n.resolvedLanguage ?? "en");
i18n.on("languageChanged", syncHtmlLang);

/** Current UI language, always one of ours */
export const currentLanguage = (): Language =>
  (LANGUAGES.find((l) => l.code === i18n.resolvedLanguage)?.code ?? "en") as Language;

export const currentLocale = () => LOCALES[currentLanguage()];

export default i18n;
