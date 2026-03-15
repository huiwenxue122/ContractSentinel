"use client";

import { useLocale } from "@/app/context/LocaleContext";

export function LanguageSwitcher() {
  const { locale, setLocale, t } = useLocale();

  return (
    <div className="flex items-center gap-1 rounded-md border border-[var(--panel-border)] bg-[var(--card-bg)] px-1 py-0.5 text-xs">
      <span className="mr-1 text-[var(--muted)]">{t("language")}:</span>
      {(["zh", "en"] as const).map((lang) => (
        <button
          key={lang}
          type="button"
          onClick={() => setLocale(lang)}
          className={`rounded px-2 py-1 font-medium transition ${
            locale === lang
              ? "bg-[var(--accent)] text-white"
              : "text-[var(--muted)] hover:bg-[var(--panel-bg)] hover:text-gray-700"
          }`}
          aria-pressed={locale === lang}
          aria-label={lang === "zh" ? "中文" : "English"}
        >
          {lang === "zh" ? t("langZh") : t("langEn")}
        </button>
      ))}
    </div>
  );
}
