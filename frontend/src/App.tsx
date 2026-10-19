import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { api, type Scope } from "./api";
import Chat from "./components/Chat";
import Charts from "./components/Charts";
import ImportReportPanel from "./components/ImportReportPanel";
import Landing from "./components/Landing";
import Recommendations from "./components/Recommendations";
import Simulator from "./components/Simulator";
import SummaryCards from "./components/SummaryCards";
import TransactionsTable from "./components/TransactionsTable";
import type { Analysis, ChatMsg, ImportReport, Profile, Recommendation, SimulationParams, Transaction } from "./types";

const EMPTY_SIM: SimulationParams = { reductions: {}, revenue_increase_pct: 0 };

export default function App() {
  const [profile, setProfile] = useState<Profile>("pessoal");
  const [transactions, setTransactions] = useState<Transaction[]>([]);
  const [report, setReport] = useState<ImportReport | null>(null);
  const [start, setStart] = useState("");
  const [end, setEnd] = useState("");
  const [analysis, setAnalysis] = useState<Analysis | null>(null);
  const [messages, setMessages] = useState<ChatMsg[]>([]);
  const [chatLoading, setChatLoading] = useState(false);
  const [recs, setRecs] = useState<Recommendation[]>([]);
  const [recsSource, setRecsSource] = useState<string | null>(null);
  const [recsLoading, setRecsLoading] = useState(false);
  const [sim, setSim] = useState<SimulationParams>(EMPTY_SIM);
  const [loading, setLoading] = useState(false);
  const [exporting, setExporting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [aiEnabled, setAiEnabled] = useState<boolean | null>(null);
  const fileRef = useRef<HTMLInputElement>(null);

  const hasData = transactions.length > 0;

  useEffect(() => {
    api.health().then((h) => setAiEnabled(h.ai_enabled)).catch(() => setError("Não foi possível falar com o servidor. Ele está rodando em http://localhost:8000?"));
  }, []);

  const scope: Scope = useMemo(
    () => ({ profile, transactions, start: start || undefined, end: end || undefined }),
    [profile, transactions, start, end]
  );

  // Recalcula o painel sempre que dados, perfil ou período mudam.
  useEffect(() => {
    if (!hasData) {
      setAnalysis(null);
      return;
    }
    let cancelled = false;
    const id = setTimeout(() => {
      api
        .analyze(scope)
        .then((a) => !cancelled && setAnalysis(a))
        .catch((e: Error) => !cancelled && setError(e.message));
    }, 150);
    // As recomendações e a simulação antigas deixam de valer quando o escopo muda.
    setRecs([]);
    setRecsSource(null);
    return () => {
      cancelled = true;
      clearTimeout(id);
    };
  }, [scope, hasData]);

  const load = useCallback(async (fn: () => Promise<{ transactions: Transaction[]; report: ImportReport }>) => {
    setLoading(true);
    setError(null);
    try {
      const res = await fn();
      setTransactions(res.transactions);
      setReport(res.report);
      setStart("");
      setEnd("");
      setSim(EMPTY_SIM);
      setMessages([]);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setLoading(false);
    }
  }, []);

  const loadDemo = (p: Profile = profile) => load(() => api.demo(p));
  const loadFile = (f: File) => load(() => api.importCsv(f));

  const changeProfile = (p: Profile) => {
    setProfile(p);
    setSim(EMPTY_SIM);
  };

  const sendChat = async (text: string) => {
    const next: ChatMsg[] = [...messages, { role: "user", content: text }];
    setMessages(next);
    setChatLoading(true);
    try {
      const r = await api.chat(scope, next);
      setMessages([...next, { role: "assistant", content: r.reply, source: r.source }]);
    } catch (e) {
      setMessages([...next, { role: "assistant", content: `Não consegui responder: ${(e as Error).message}`, source: "sistema" }]);
    } finally {
      setChatLoading(false);
    }
  };

  const generateRecs = async () => {
    setRecsLoading(true);
    try {
      const r = await api.recommendations(scope);
      setRecs(r.items);
      setRecsSource(r.source);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setRecsLoading(false);
    }
  };

  const exportExcel = async () => {
    setExporting(true);
    setError(null);
    try {
      const simActive = Object.values(sim.reductions).some((v) => v > 0) || sim.revenue_increase_pct > 0;
      await api.exportXlsx(scope, recs, simActive ? sim : null);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setExporting(false);
    }
  };

  const toggleCounted = (id: number) => setTransactions((txs) => txs.map((t) => (t.id === id ? { ...t, counted: !t.counted } : t)));

  const reset = () => {
    setTransactions([]);
    setReport(null);
    setAnalysis(null);
    setMessages([]);
    setRecs([]);
    setSim(EMPTY_SIM);
    setStart("");
    setEnd("");
  };

  if (!hasData) {
    return <Landing profile={profile} onProfile={setProfile} onDemo={() => loadDemo()} onFile={loadFile} loading={loading} error={error} aiEnabled={aiEnabled} />;
  }

  return (
    <div className="min-h-screen">
      <header className="sticky top-0 z-10 border-b border-slate-200 bg-white/90 backdrop-blur">
        <div className="mx-auto flex max-w-7xl flex-wrap items-center gap-3 px-4 py-3">
          <button onClick={reset} className="flex items-center gap-2 font-bold text-slate-900" title="Voltar ao início">
            <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-brand-700 text-sm text-white">R$</span>
            <span className="hidden sm:inline">Assistente Financeiro IA</span>
          </button>
          <select className="rounded-lg border border-slate-300 px-2 py-1.5 text-sm" value={profile} onChange={(e) => changeProfile(e.target.value as Profile)} aria-label="Perfil">
            <option value="pessoal">Finanças pessoais</option>
            <option value="empresa">Microempresa</option>
          </select>
          <div className="flex items-center gap-1 text-sm">
            <input type="date" className="rounded-lg border border-slate-300 px-2 py-1" value={start} max={end || undefined} onChange={(e) => setStart(e.target.value)} aria-label="Início do período" />
            <span>a</span>
            <input type="date" className="rounded-lg border border-slate-300 px-2 py-1" value={end} min={start || undefined} onChange={(e) => setEnd(e.target.value)} aria-label="Fim do período" />
            {(start || end) && (
              <button className="px-1 text-slate-500 underline" onClick={() => (setStart(""), setEnd(""))}>
                limpar
              </button>
            )}
          </div>
          <div className="ml-auto flex flex-wrap gap-2">
            <button className="btn-ghost" onClick={() => fileRef.current?.click()}>
              Importar CSV
            </button>
            <input ref={fileRef} type="file" accept=".csv,text/csv" hidden onChange={(e) => (e.target.files?.[0] && loadFile(e.target.files[0]), (e.target.value = ""))} />
            <button className="btn-ghost" onClick={() => loadDemo()}>
              Dados fictícios
            </button>
            <button className="btn-primary" onClick={exportExcel} disabled={exporting || !analysis?.has_data}>
              {exporting ? "Exportando…" : "Exportar para Excel"}
            </button>
          </div>
        </div>
      </header>

      <main className="mx-auto grid max-w-7xl gap-4 px-4 py-4 lg:grid-cols-[1fr_24rem]">
        <div className="min-w-0 space-y-4">
          {error && (
            <div className="flex items-start justify-between rounded-xl bg-red-50 p-3 text-sm text-red-700">
              <span>{error}</span>
              <button onClick={() => setError(null)} aria-label="Fechar">
                ✕
              </button>
            </div>
          )}
          {aiEnabled === false && (
            <div className="rounded-xl bg-amber-50 p-3 text-sm text-amber-900">IA não configurada no servidor: chat e recomendações usam regras locais. Veja o README para definir a ANTHROPIC_API_KEY.</div>
          )}
          {report && <ImportReportPanel report={report} />}
          {analysis && analysis.warnings.length > 0 && (
            <div className="rounded-xl border border-amber-200 bg-amber-50 p-3 text-sm text-amber-900">
              {analysis.warnings.map((w, i) => (
                <div key={i}>⚠ {w}</div>
              ))}
            </div>
          )}
          {analysis && (
            <>
              <SummaryCards analysis={analysis} />
              <Charts analysis={analysis} />
              {analysis.has_data && (
                <>
                  <div className="grid gap-4 xl:grid-cols-2">
                    <div className="card">
                      <h3 className="mb-2 font-semibold">Principais despesas</h3>
                      <ol className="space-y-1 text-sm">
                        {analysis.top_expenses.slice(0, 7).map((t, i) => (
                          <li key={i} className="flex justify-between gap-2">
                            <span className="truncate">
                              {t.description} <span className="text-xs text-slate-400">({t.category})</span>
                            </span>
                            <span className="font-medium">{t.amount.toLocaleString("pt-BR", { style: "currency", currency: "BRL" })}</span>
                          </li>
                        ))}
                      </ol>
                      {analysis.recurring.length > 0 && (
                        <div className="mt-3 border-t pt-2 text-sm">
                          <div className="font-semibold">Despesas recorrentes</div>
                          {analysis.recurring.slice(0, 5).map((r) => (
                            <div key={r.description} className="flex justify-between text-slate-600">
                              <span>{r.description}</span>
                              <span>~{r.avg_monthly.toLocaleString("pt-BR", { style: "currency", currency: "BRL" })}/mês</span>
                            </div>
                          ))}
                        </div>
                      )}
                    </div>
                    <Simulator scope={scope} analysis={analysis} params={sim} onChange={setSim} />
                  </div>
                  <Recommendations items={recs} source={recsSource} loading={recsLoading} onGenerate={generateRecs} />
                </>
              )}
            </>
          )}
          <TransactionsTable transactions={transactions} start={start || undefined} end={end || undefined} onToggle={toggleCounted} />
        </div>

        <aside className="lg:sticky lg:top-20 lg:self-start">
          <Chat messages={messages} loading={chatLoading} onSend={sendChat} />
        </aside>
      </main>
    </div>
  );
}
