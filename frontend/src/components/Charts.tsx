import { Bar, BarChart, CartesianGrid, Cell, Legend, Line, LineChart, Pie, PieChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import type { Analysis } from "../types";
import { brl, monthLabel } from "../format";

const COLORS = ["#0f766e", "#f97316", "#6366f1", "#eab308", "#ec4899", "#0ea5e9", "#84cc16", "#a855f7", "#64748b", "#ef4444"];

export default function Charts({ analysis }: { analysis: Analysis }) {
  if (!analysis.has_data) return null;
  const timeline = analysis.timeline.map((t) => ({ ...t, label: monthLabel(t.month) }));
  const cats = analysis.categories;
  const money = (v: unknown) => brl(Number(v));
  return (
    <div className="grid gap-4 lg:grid-cols-2">
      <div className="card">
        <h3 className="mb-2 font-semibold">Distribuição dos gastos por categoria</h3>
        <div className="h-72">
          <ResponsiveContainer>
            <PieChart>
              <Pie data={cats} dataKey="value" nameKey="category" innerRadius={50} outerRadius={95} paddingAngle={2}>
                {cats.map((_, i) => (
                  <Cell key={i} fill={COLORS[i % COLORS.length]} />
                ))}
              </Pie>
              <Tooltip formatter={money} />
              <Legend />
            </PieChart>
          </ResponsiveContainer>
        </div>
      </div>

      <div className="card">
        <h3 className="mb-2 font-semibold">{analysis.labels.timeline}</h3>
        <div className="h-72">
          <ResponsiveContainer>
            <BarChart data={timeline}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="label" />
              <YAxis tickFormatter={(v: number) => `${Math.round(v / 1000)}k`} />
              <Tooltip formatter={money} />
              <Legend />
              <Bar dataKey="income" name="Receitas" fill="#0f766e" radius={[4, 4, 0, 0]} />
              <Bar dataKey="expense" name="Despesas" fill="#f97316" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
        {timeline.length < 2 && <p className="text-xs text-slate-500">Há apenas um mês no período: a evolução no tempo é limitada.</p>}
      </div>

      <div className="card lg:col-span-2">
        <h3 className="mb-2 font-semibold">{analysis.profile === "empresa" ? "Fluxo de caixa acumulado" : "Saldo acumulado"}</h3>
        <div className="h-60">
          <ResponsiveContainer>
            <LineChart data={timeline}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="label" />
              <YAxis tickFormatter={(v: number) => `${Math.round(v / 1000)}k`} />
              <Tooltip formatter={money} />
              <Line type="monotone" dataKey="cumulative" name="Saldo acumulado" stroke="#0f172a" strokeWidth={2.5} dot />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  );
}
