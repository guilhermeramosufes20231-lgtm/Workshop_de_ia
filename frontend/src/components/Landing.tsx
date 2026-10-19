import { useRef } from "react";
import type { Profile } from "../types";

interface Props {
  profile: Profile;
  onProfile: (p: Profile) => void;
  onDemo: () => void;
  onFile: (f: File) => void;
  loading: boolean;
  error: string | null;
  aiEnabled: boolean | null;
}

const PROFILES: { id: Profile; title: string; text: string }[] = [
  { id: "pessoal", title: "Finanças pessoais", text: "Receitas, despesas, orçamento, categorias de consumo e economia." },
  { id: "empresa", title: "Microempresa", text: "Faturamento, custos, despesas, fluxo de caixa e resultado estimado." },
];

export default function Landing({ profile, onProfile, onDemo, onFile, loading, error, aiEnabled }: Props) {
  const fileRef = useRef<HTMLInputElement>(null);
  return (
    <main className="mx-auto max-w-3xl px-4 py-10">
      <div className="mb-8 text-center">
        <div className="mx-auto mb-4 flex h-14 w-14 items-center justify-center rounded-2xl bg-brand-700 text-2xl text-white">R$</div>
        <h1 className="text-3xl font-bold text-slate-900 sm:text-4xl">Assistente Financeiro IA</h1>
        <p className="mt-3 text-slate-600">
          Converse com seus números: descubra quanto entrou e saiu, onde dá para economizar, simule cenários e leve tudo para o Excel.
        </p>
      </div>

      <section className="card mb-4">
        <h2 className="mb-3 font-semibold">1. Escolha seu perfil</h2>
        <div className="grid gap-3 sm:grid-cols-2">
          {PROFILES.map((p) => (
            <button
              key={p.id}
              onClick={() => onProfile(p.id)}
              className={`rounded-xl border-2 p-4 text-left transition ${profile === p.id ? "border-brand-600 bg-brand-50" : "border-slate-200 hover:border-slate-300"}`}
            >
              <div className="font-semibold">{p.title}</div>
              <div className="mt-1 text-sm text-slate-600">{p.text}</div>
            </button>
          ))}
        </div>
      </section>

      <section className="card mb-4">
        <h2 className="mb-3 font-semibold">2. Traga seus dados</h2>
        <div className="flex flex-col gap-3 sm:flex-row">
          <button className="btn-primary flex-1" onClick={onDemo} disabled={loading}>
            Carregar dados fictícios
          </button>
          <button className="btn-ghost flex-1" onClick={() => fileRef.current?.click()} disabled={loading}>
            Importar arquivo CSV
          </button>
          <input
            ref={fileRef}
            type="file"
            accept=".csv,text/csv"
            hidden
            onChange={(e) => {
              const f = e.target.files?.[0];
              if (f) onFile(f);
              e.target.value = "";
            }}
          />
        </div>
        <p className="mt-3 text-xs text-slate-500">
          Colunas reconhecidas: data, descrição, categoria, tipo, valor (e conta). Aceita separador ; ou , e valores como “R$ 1.234,56”.
        </p>
        {loading && <p className="mt-3 text-sm text-slate-600">Carregando…</p>}
        {error && <p className="mt-3 rounded-lg bg-red-50 p-3 text-sm text-red-700">{error}</p>}
      </section>

      <section className="rounded-2xl border border-amber-200 bg-amber-50 p-4 text-sm text-amber-900">
        <strong>Protótipo (MVP).</strong> Use dados fictícios ou dados que você aceite compartilhar. Nada é gravado no servidor: os dados ficam
        nesta sessão do navegador. Para as respostas de IA, o servidor envia apenas totais, categorias, série mensal e as 10 maiores despesas ao
        provedor de IA — não a lista completa de movimentações.{" "}
        {aiEnabled === false && <span className="font-semibold">IA não configurada: o chat funciona em modo offline (regras locais).</span>}
      </section>
    </main>
  );
}
