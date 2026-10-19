import type { Recommendation } from "../types";

const TONE: Record<string, string> = {
  fato: "bg-slate-100 text-slate-700",
  estimativa: "bg-amber-100 text-amber-800",
  recomendacao: "bg-emerald-100 text-emerald-800",
};
const NAME: Record<string, string> = { fato: "Fato", estimativa: "Estimativa", recomendacao: "Recomendação" };

interface Props {
  items: Recommendation[];
  source: string | null;
  loading: boolean;
  onGenerate: () => void;
}

export default function Recommendations({ items, source, loading, onGenerate }: Props) {
  return (
    <div className="card">
      <div className="mb-3 flex items-center justify-between gap-2">
        <h3 className="font-semibold">Análise e recomendações</h3>
        <button className="btn-primary" onClick={onGenerate} disabled={loading}>
          {loading ? "Gerando…" : items.length ? "Gerar novamente" : "Gerar recomendações"}
        </button>
      </div>
      {items.length === 0 && <p className="text-sm text-slate-500">Gere as recomendações para incluí-las também na planilha Excel.</p>}
      <div className="space-y-3">
        {items.map((r, i) => (
          <div key={i} className="rounded-xl border border-slate-200 p-3">
            <span className={`rounded-full px-2 py-0.5 text-xs font-semibold ${TONE[r.tipo]}`}>{NAME[r.tipo]}</span>
            <div className="mt-1 font-semibold">{r.titulo}</div>
            <p className="text-sm text-slate-700">{r.detalhe}</p>
            {r.premissas && <p className="mt-1 text-xs text-slate-500">Premissas: {r.premissas}</p>}
          </div>
        ))}
      </div>
      {source && items.length > 0 && (
        <p className="mt-2 text-xs text-slate-400">{source === "ia" ? "Gerado por IA a partir dos números calculados." : "Gerado por regras locais (IA não configurada ou indisponível)."}</p>
      )}
    </div>
  );
}
