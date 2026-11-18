import "i18next";

import type es from "./locales/es";

// Typed keys: t("library.title") is checked against the Spanish file (the source of truth)
declare module "i18next" {
  interface CustomTypeOptions {
    defaultNS: "translation";
    resources: { translation: typeof es };
  }
}
