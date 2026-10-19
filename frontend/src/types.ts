export type Profile = "pessoal" | "empresa";
export type TxType = "receita" | "despesa" | "transferencia" | "pagamento_fatura";

export interface Transaction {
  id: number;
  date: string;
  description: string;
  category: string;
  type: TxType;
  amount: number;
  account: string;
  counted: boolean;
  note: string;
}

export interface ImportReport {
  total_rows: number;
  valid: number;
  invalid: { line: number; reason: string; raw: string }[];
  invalid_count: number;
  duplicates: number;
  duplicates_value: number;
  transfers: number;
  card_payments: number;
  card_double_count_avoided: boolean;
  warnings: string[];
}

export interface Summary {
  income: number;
  expense: number;
  balance: number;
  savings_rate: number | null;
  avg_monthly_income: number;
  avg_monthly_expense: number;
  top_category: string | null;
  top_category_pct: number | null;
  costs?: number;
  operating_expenses?: number;
  gross_margin_pct?: number | null;
}

export interface Analysis {
  profile: Profile;
  labels: { income: string; expense: string; balance: string; timeline: string };
  period: { start: string | null; end: string | null; months: number };
  has_data: boolean;
  summary: Summary;
  categories: { category: string; value: number; pct: number; count: number }[];
  timeline: { month: string; income: number; expense: number; balance: number; cumulative: number }[];
  top_expenses: { date: string; description: string; category: string; amount: number }[];
  recurring: { description: string; category: string; months: number; avg_monthly: number }[];
  warnings: string[];
}

export interface Recommendation {
  tipo: "fato" | "estimativa" | "recomendacao";
  titulo: string;
  detalhe: string;
  premissas: string;
}

export interface SimulationParams {
  reductions: Record<string, number>;
  revenue_increase_pct: number;
}

export interface SimulationResult {
  rows: { category: string; current_monthly: number; reduction_pct: number; saving_monthly: number; saving_annual: number }[];
  comparison: {
    current: { income: number; expense: number; balance: number };
    projected: { income: number; expense: number; balance: number };
    gain_monthly: number;
    gain_annual: number;
    saving_monthly: number;
    saving_annual: number;
    extra_income_monthly: number;
  };
  assumptions: string[];
  disclaimer: string;
}

export interface ChatMsg {
  role: "user" | "assistant";
  content: string;
  source?: string;
}
