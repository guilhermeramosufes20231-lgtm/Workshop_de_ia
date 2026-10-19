import { useEffect, useState } from "react";
import { api, type Scope } from "../api";
import type { Analysis, SimulationParams, SimulationResult } from "../types";
import { brl } from "../format";

interface Props {
  scope: Scope;
  analysis: Analysis;
  params: SimulationParams;
  onChange: (p: SimulationParams) => void;
}

const REDUCTIONS = [0, 10, 15, 20];
const REVENUE = [0, 5, 10, 20];

export default function Simulator({ scope, analysis, params, onChange }: Props) {
  const [result, setResult] = useState<SimulationResult | null>(null);
  const active = Object.values(params.reductions).some((v) => v > 0) || params.revenue_increase_pct > 0;

  useEffect(() => {
    if (!active) {
      setResult(null);
      return;
    }
    const id = setTimeout(() => {
      api.simulate(scope, params).then(setResult).catch(() => setResult(null));
    }, 250);
    return () => clearTimeout(id);
  }, [scope, params, active]);

  const cats = analysis.categories.slice(0, 6);
  return (
    <div className="card">
      <h3 className="font-semibold">Simulador de cenários</h3>
      <p className="mb-3 text-xs text-slate-500">Estimativas com base na média mensal do período. Não garantem resultados futuros.</p>
      <div className="grid gap-2 sm:grid-cols-2">
        {cats.map((c) => (
          <label key={c.category} className="flex items-center justify-between gap-2 rounded-lg bg-slate-50 p-2 text-sm">
            <span>
              {c.category} <span className="text-xs text-slate-500">({brl(c.value / (analysis.period.months || 1))}/mês)</span>
            </span>
            <select
              className="rounded-md border border-slate-300 bg-white px-2 py-1"
              value={params.reductions[c.category] ?? 0}
              onChange={(e) => onChange({ ...params, reductions: { ...params.reductions, [c.category]: Number(e.target.value) } })}
            >
              {REDUCTIONS.map((r) => (
                <option key={r} value={r}>
                  {r === 0 ? "sem corte" : `-${r}%`}
                </option>
              ))}
            </select>
          </label>
        ))}
        <label className="flex items-center justify-between gap-2 rounded-lg bg-emerald-50 p-2 text-sm">
          <span>Aumento de receita</span>
          <select
            className="rounded-md border border-slate-300 bg-white px-2 py-1"
            value={params.revenue_increase_pct}
            onChange={(e) => onChange({ ...params, revenue_increase_pct: Number(e.target.value) })}
          >
            {REVENUE.map((r) => (
              <option key={r} value={r}>
                {r === 0 ? "sem aumento" : `+${r}%`}
              </option>
            ))}
          </select>
        </label>
      </div>

      {result && result.rows.length + (params.revenue_increase_pct > 0 ? 1 : 0) > 0 && (
        <div className="mt-4 space-y-3 text-sm">
          <div className="grid grid-cols-3 gap-2 text-center">
            <div className="rounded-lg bg-slate-50 p-2">
              <div className="text-xs text-slate-500">Saldo mensal atual</div>
              <div className="font-bold">{brl(result.comparison.current.balance)}</div>
            </div>
            <div className="rounded-lg bg-brand-50 p-2">
              <div className="text-xs text-slate-500">Saldo mensal projetado</div>
              <div className="font-bold text-brand-700">{brl(result.comparison.projected.balance)}</div>
            </div>
            <div className="rounded-lg bg-emerald-50 p-2">
              <div className="text-xs text-slate-500">Ganho estimado/ano</div>
              <div className="font-bold text-emerald-700">{brl(result.comparison.gain_annual)}</div>
            </div>
          </div>
          <div className="text-slate-700">
            Economia estimada com cortes: <strong>{brl(result.comparison.saving_monthly)}/mês</strong> ({brl(result.comparison.saving_annual)}/ano).
          </div>
          <p className="text-xs text-slate-500">{result.disclaimer}</p>
        </div>
      )}
    </div>
  );
}
