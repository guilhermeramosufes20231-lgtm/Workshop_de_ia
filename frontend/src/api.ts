import type { Analysis, ChatMsg, ImportReport, Profile, Recommendation, SimulationParams, SimulationResult, Transaction } from "./types";

async function handle<T>(res: Response): Promise<T> {
  if (!res.ok) {
    let msg = `Erro ${res.status}`;
    try {
      const body = await res.json();
      if (typeof body.detail === "string") msg = body.detail;
    } catch {
      /* ignora */
    }
    throw new Error(msg);
  }
  return res.json() as Promise<T>;
}

const post = <T,>(url: string, body: unknown) =>
  fetch(url, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) }).then((r) => handle<T>(r));

export interface Scope {
  profile: Profile;
  transactions: Transaction[];
  start?: string;
  end?: string;
}

export const api = {
  health: () => fetch("/api/health").then((r) => handle<{ ok: boolean; ai_enabled: boolean; model: string | null }>(r)),
  demo: (profile: Profile) => fetch(`/api/demo?profile=${profile}`).then((r) => handle<{ transactions: Transaction[]; report: ImportReport }>(r)),
  importCsv: (file: File) => {
    const fd = new FormData();
    fd.append("file", file);
    return fetch("/api/import", { method: "POST", body: fd }).then((r) => handle<{ transactions: Transaction[]; report: ImportReport }>(r));
  },
  analyze: (s: Scope) => post<Analysis>("/api/analyze", s),
  simulate: (s: Scope, simulation: SimulationParams) => post<SimulationResult>("/api/simulate", { ...s, simulation }),
  chat: (s: Scope, messages: ChatMsg[]) =>
    post<{ reply: string; source: string }>("/api/chat", { ...s, messages: messages.map(({ role, content }) => ({ role, content })) }),
  recommendations: (s: Scope) => post<{ items: Recommendation[]; source: string }>("/api/recommendations", s),
  exportXlsx: async (s: Scope, recommendations: Recommendation[], simulation: SimulationParams | null) => {
    const res = await fetch("/api/export", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ ...s, recommendations, simulation }),
    });
    if (!res.ok) throw new Error(`Falha ao exportar (${res.status})`);
    const blob = await res.blob();
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "assistente-financeiro.xlsx";
    a.click();
    URL.revokeObjectURL(url);
  },
};
