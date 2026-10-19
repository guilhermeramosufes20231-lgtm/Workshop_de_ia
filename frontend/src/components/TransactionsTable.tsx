import { useMemo, useState } from "react";
import type { Transaction } from "../types";
import { brl, dateBr } from "../format";

const TYPE_LABEL: Record<string, string> = { receita: "Receita", despesa: "Despesa", transferencia: "Transferência", pagamento_fatura: "Pgto. fatura" };

interface Props {
  transactions: Transaction[];
  start?: string;
  end?: string;
  onToggle: (id: number) => void;
}

export default function TransactionsTable({ transactions, start, end, onToggle }: Props) {
  const [q, setQ] = useState("");
  const [onlyIssues, setOnlyIssues] = useState(false);
  const rows = useMemo(
    () =>
      transactions.filter(
        (t) =>
          (!start || t.date >= start) &&
          (!end || t.date <= end) &&
          (!onlyIssues || !t.counted) &&
          (!q || `${t.description} ${t.category}`.toLowerCase().includes(q.toLowerCase()))
      ),
    [transactions, start, end, q, onlyIssues]
  );
  return (
    <div className="card">
      <div className="mb-3 flex flex-wrap items-center gap-3">
        <h3 className="font-semibold">Movimentações importadas ({rows.length})</h3>
        <input className="rounded-lg border border-slate-300 px-3 py-1.5 text-sm" placeholder="Buscar…" value={q} onChange={(e) => setQ(e.target.value)} />
        <label className="flex items-center gap-2 text-sm text-slate-600">
          <input type="checkbox" checked={onlyIssues} onChange={(e) => setOnlyIssues(e.target.checked)} />
          Só não contabilizadas
        </label>
      </div>
      <div className="max-h-96 overflow-auto rounded-lg border border-slate-200">
        <table className="w-full text-left text-sm">
          <thead className="sticky top-0 bg-slate-100 text-xs uppercase text-slate-600">
            <tr>
              <th className="p-2">Contab.</th>
              <th className="p-2">Data</th>
              <th className="p-2">Descrição</th>
              <th className="p-2">Categoria</th>
              <th className="p-2">Tipo</th>
              <th className="p-2 text-right">Valor</th>
            </tr>
          </thead>
          <tbody>
            {rows.slice(0, 300).map((t) => (
              <tr key={t.id} className={`border-t border-slate-100 ${t.counted ? "" : "bg-amber-50 text-slate-500"}`} title={t.note}>
                <td className="p-2">
                  <input type="checkbox" checked={t.counted} onChange={() => onToggle(t.id)} aria-label="Contabilizar" />
                </td>
                <td className="whitespace-nowrap p-2">{dateBr(t.date)}</td>
                <td className="p-2">
                  {t.description}
                  {t.note && <div className="text-xs text-amber-700">{t.note}</div>}
                </td>
                <td className="p-2">{t.category}</td>
                <td className="p-2">{TYPE_LABEL[t.type]}</td>
                <td className={`whitespace-nowrap p-2 text-right ${t.type === "receita" ? "text-emerald-700" : ""}`}>{brl(t.amount)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      {rows.length > 300 && <p className="mt-2 text-xs text-slate-500">Mostrando as 300 primeiras. A exportação para Excel inclui todas.</p>}
    </div>
  );
}
