"use client";

import { LocaleProvider } from "@/app/context/LocaleContext";
import { LanguageSwitcher } from "@/app/components/LanguageSwitcher";

export function ClientProviders({ children }: { children: React.ReactNode }) {
  return (
    <LocaleProvider>
      <div className="absolute top-3 right-4 z-10">
        <LanguageSwitcher />
      </div>
      {children}
    </LocaleProvider>
  );
}
