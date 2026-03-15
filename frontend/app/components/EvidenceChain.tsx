"use client";

import { useLocale } from "@/app/context/LocaleContext";
import type { Citation, RiskMemoItem } from "@/app/types/risk";

/**
 * 证据链展示：使用当前 API 返回的 citation + evidence_summary。
 * 后端暂无「引用到的条款/定义列表」接口，此处展示条款引用与证据摘要；
 * 若后续提供 GET /contracts/:id/clauses/:id/context，可扩展为完整证据链。
 */
export function EvidenceChain({ item }: { item: RiskMemoItem }) {
  const { t } = useLocale();
  const citation = item.citation;
  const section = citation?.section ?? item.clause_ref ?? null;
  const evidence = item.evidence_summary?.trim() ?? null;
  if (!section && !evidence) return null;

  return (
    <div className="mt-3 rounded border border-[var(--panel-border)] bg-[var(--panel-bg)] p-3 text-xs">
      <div className="font-medium text-[var(--muted)] mb-1.5">
        {t("evidenceChainTitle")}
      </div>
      {section && (
        <p className="text-gray-700">
          <span className="text-[var(--muted)]">{t("evidenceSection")}:</span>{" "}
          {section}
          {citation?.page != null && (
            <span className="ml-1 text-[var(--muted)]"> (p.{citation.page})</span>
          )}
        </p>
      )}
      {evidence && (
        <p className="mt-1.5 text-gray-600 leading-relaxed">{evidence}</p>
      )}
    </div>
  );
}
