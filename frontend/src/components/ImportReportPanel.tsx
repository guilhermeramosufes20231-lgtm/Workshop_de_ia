import type { ImportReport } from "../types";
import { brl } from "../format";

export default function ImportReportPanel({ report }: { report: ImportReport }) {
  const items: string[] = [
    `${report.valid} de ${report.total_rows} linhas válidas.`,
    report.invalid_count ? `${report.invalid_count} linha(s) inválida(s) descartada(s).` : "",
    report.duplicates ? `${report.duplicates} possível(is) duplicidade(s) (${brl(report.duplicates_value)}) não contabilizada(s).` : "",
    report.transfers ? `${report.transfers} transferência(s) entre contas próprias fora dos totais.` : "",
    report.card_double_count_avoided ? `${report.card_payments} pagamento(s) de fatura não contabilizado(s) para evitar dupla contagem com as compras no cartão.` : "",
    ...report.warnings,
  ].filter(Boolean);
  return (
    <details className="card" open={report.invalid_count > 0 || report.warnings.length > 0}>
      <summary className="cursor-pointer font-semibold">Conferência da importação</summary>
      <ul className="mt-2 list-disc space-y-1 pl-5 text-sm text-slate-700">
        {items.map((t, i) => (
          <li key={i}>{t}</li>
        ))}
      </ul>
      {report.invalid.length > 0 && (
        <div className="mt-3 text-xs text-slate-600">
          <div className="font-semibold">Linhas descartadas:</div>
          {report.invalid.slice(0, 5).map((r) => (
            <div key={r.line}>
              Linha {r.line}: {r.reason}
            </div>
          ))}
        </div>
      )}
    </details>
  );
}
