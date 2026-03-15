"use client";

import { useState } from "react";
import { useLocale } from "@/app/context/LocaleContext";
import type { RiskMemoItem } from "@/app/types/risk";
import { EvidenceChain } from "./EvidenceChain";

function riskLevelClass(level: string): string {
  const v = level.toLowerCase();
  if (v === "high") return "bg-red-100 text-red-800";
  if (v === "low") return "bg-green-100 text-green-800";
  return "bg-amber-100 text-amber-800";
}

function riskLevelLabel(level: string, t: (k: string) => string): string {
  const v = level.toLowerCase();
  if (v === "high") return t("riskLevelHigh");
  if (v === "low") return t("riskLevelLow");
  return t("riskLevelMedium");
}

export function RiskCard({ item, defaultExpandEvidence = false }: { item: RiskMemoItem; defaultExpandEvidence?: boolean }) {
  const { t } = useLocale();
  const [showEvidence, setShowEvidence] = useState(defaultExpandEvidence);
  return (
    <div className="rounded-lg border border-[var(--panel-border)] bg-[var(--card-bg)] p-4 shadow-sm">
      <div className="flex items-center gap-2 mb-2 flex-wrap">
        <span className="text-xs font-medium text-[var(--muted)]">
          {t("riskCardRule")} {item.rule_triggered}
          {item.clause_ref ? ` · ${item.clause_ref}` : ""}
        </span>
        <span
          className={`rounded px-1.5 py-0.5 text-xs font-medium ${riskLevelClass(item.risk_level)}`}
        >
          {riskLevelLabel(item.risk_level, t)}
        </span>
      </div>
      {item.clause && (
        <p className="text-sm text-gray-700 line-clamp-3 mb-2">{item.clause}</p>
      )}
      {item.reason && (
        <p className="text-sm text-gray-600 mb-2">
          <span className="text-[var(--muted)]">{t("riskCardReason")}:</span>{" "}
          {item.reason}
        </p>
      )}
      {item.fallback_language && (
        <p className="text-sm text-gray-600 mb-2">
          <span className="text-[var(--muted)]">{t("riskCardFallback")}:</span>{" "}
          {item.fallback_language}
        </p>
      )}
      {item.escalation && (
        <p className="text-sm">
          <span className="text-[var(--muted)]">{t("riskCardEscalation")}:</span>{" "}
          {item.escalation}
        </p>
      )}
      {(item.justified !== undefined && item.justified !== null) && (
        <p className="mt-2 text-xs text-[var(--muted)]">
          {t("riskCardJustified")}: {item.justified ? t("justifiedYes") : t("justifiedNo")}
          {item.confidence && ` · ${t("riskCardConfidence")}: ${item.confidence}`}
        </p>
      )}
      {(item.citation || item.evidence_summary) && (
        <>
          <button
            type="button"
            onClick={() => setShowEvidence((s) => !s)}
            className="mt-2 text-xs font-medium text-[var(--accent)] hover:underline"
          >
            {showEvidence ? t("evidenceCollapse") : t("evidenceExpand")}
          </button>
          {showEvidence && <EvidenceChain item={item} />}
        </>
      )}
    </div>
  );
}
