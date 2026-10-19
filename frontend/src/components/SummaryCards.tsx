import type { Analysis } from "../types";
import { brl } from "../format";

function Card({ label, value, tone }: { label: string; value: string; tone?: "good" | "bad" }) {
  const color = tone === "good" ? "text-emerald-700" : tone === "bad" ? "text-red-600" : "text-slate-900";
  return (
    <div className="card">
      <div className="text-xs font-medium uppercase tracking-wide text-slate-500">{label}</div>
      <div className={`mt-1 text-xl font-bold sm:text-2xl ${color}`}>{value}</div>
    </div>
  );
}

export default function SummaryCards({ analysis }: { analysis: Analysis }) {
  if (!analysis.has_data) return null;
  const s = analysis.summary;
  const l = analysis.labels;
  return (
    <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">
      <Card label={l.income} value={brl(s.income)} />
      <Card label={l.expense} value={brl(s.expense)} />
      <Card label={l.balance} value={brl(s.balance)} tone={s.balance >= 0 ? "good" : "bad"} />
      {analysis.profile === "empresa" ? (
        <Card label="Margem bruta estimada" value={s.gross_margin_pct != null ? `${s.gross_margin_pct}%` : "n/d"} />
      ) : (
        <Card label="Taxa de poupança" value={s.savings_rate != null ? `${s.savings_rate}%` : "n/d"} />
      )}
    </div>
  );
}
