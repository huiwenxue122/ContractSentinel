/**
 * Mirrors backend RiskMemoItem / Citation for API response.
 */
export interface Citation {
  section?: string | null;
  page?: number | null;
}

export interface RiskMemoItem {
  clause: string;
  clause_ref?: string | null;
  risk_level: string;
  rule_triggered: string;
  reason: string;
  fallback_language?: string | null;
  escalation: string;
  citation?: Citation | null;
  evidence_summary?: string | null;
  justified?: boolean | null;
  confidence?: string | null;
}

export interface StructuredRiskMemo {
  contract_id?: string | null;
  items: RiskMemoItem[];
}
