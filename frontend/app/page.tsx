"use client";

import { useLocale } from "@/app/context/LocaleContext";
import type { RiskMemoItem } from "@/app/types/risk";
import { RiskCard } from "@/app/components/RiskCard";

/** Mock items for layout demo; Task 19 will replace with API StructuredRiskMemo. */
const MOCK_RISK_ITEMS: RiskMemoItem[] = [
  {
    clause: "The indemnification obligations under this Section shall survive termination and extend to claims arising from the conduct of either party prior to the Effective Date.",
    clause_ref: "section_7_2",
    risk_level: "Medium",
    rule_triggered: "R001",
    reason: "Indemnity survival language may extend liability beyond contract term.",
    fallback_language: "Consider limiting survival to 24 months after termination.",
    escalation: "Suggest Revision",
    citation: { section: "Section 7.2", page: 12 },
    evidence_summary: "Clause 7.2 states survival of indemnity without time limit; R001 flags open-ended survival.",
    justified: true,
    confidence: "high",
  },
  {
    clause: "Governing law shall be the laws of the State of New York.",
    clause_ref: "section_9_1",
    risk_level: "Low",
    rule_triggered: "R003",
    reason: "Standard choice of law; no carve-out required for this engagement.",
    escalation: "Acceptable",
    citation: { section: "Section 9.1", page: null },
    evidence_summary: "Single sentence governing law; no conflicting terms.",
  },
];

/**
 * 证据导向审查布局：左侧合同/条款展示，右侧风险卡片列表。
 * 右侧使用 RiskCard + EvidenceChain（citation + evidence_summary）；任务 19 对接 API。
 */
export default function Home() {
  const { t } = useLocale();

  return (
    <div className="flex h-screen overflow-hidden">
      <aside className="w-1/2 flex flex-col border-r border-[var(--panel-border)] bg-[var(--card-bg)] overflow-hidden">
        <header className="shrink-0 px-4 py-3 border-b border-[var(--panel-border)] bg-[var(--panel-bg)]">
          <h1 className="text-sm font-semibold text-[var(--accent)]">
            {t("panelContract")}
          </h1>
        </header>
        <div className="flex-1 overflow-auto p-4">
          <div className="rounded border border-dashed border-[var(--panel-border)] bg-[var(--panel-bg)] p-6 text-center text-[var(--muted)]">
            <p className="text-sm">{t("panelContractPlaceholder")}</p>
            <p className="mt-2 text-xs">{t("panelContractHint")}</p>
          </div>
        </div>
      </aside>

      <main className="w-1/2 flex flex-col overflow-hidden">
        <header className="shrink-0 px-4 py-3 border-b border-[var(--panel-border)] bg-[var(--panel-bg)]">
          <h2 className="text-sm font-semibold text-[var(--accent)]">
            {t("panelRisks")}
          </h2>
        </header>
        <div className="flex-1 overflow-auto p-4 space-y-3">
          {MOCK_RISK_ITEMS.map((item, i) => (
            <RiskCard key={i} item={item} />
          ))}
        </div>
      </main>
    </div>
  );
}
