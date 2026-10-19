import { useEffect, useRef, useState } from "react";
import type { ChatMsg } from "../types";

const SUGGESTIONS = [
  "Quanto recebi e quanto gastei?",
  "Quais são minhas maiores categorias de gasto?",
  "Onde posso economizar?",
  "Tenho despesas recorrentes que valem revisar?",
];

interface Props {
  messages: ChatMsg[];
  loading: boolean;
  onSend: (text: string) => void;
}

export default function Chat({ messages, loading, onSend }: Props) {
  const [text, setText] = useState("");
  const endRef = useRef<HTMLDivElement>(null);
  useEffect(() => endRef.current?.scrollIntoView({ behavior: "smooth" }), [messages, loading]);

  const send = (t: string) => {
    const v = t.trim();
    if (!v || loading) return;
    onSend(v);
    setText("");
  };

  return (
    <div className="card flex h-[34rem] flex-col lg:h-[calc(100vh-7rem)]">
      <h3 className="mb-2 font-semibold">Chat com o assistente</h3>
      <div className="flex-1 space-y-3 overflow-y-auto pr-1">
        {messages.length === 0 && (
          <div className="space-y-2">
            <p className="text-sm text-slate-500">Pergunte sobre seus dados. Experimente:</p>
            {SUGGESTIONS.map((s) => (
              <button key={s} onClick={() => send(s)} className="block w-full rounded-xl border border-slate-200 p-2 text-left text-sm hover:bg-slate-50">
                {s}
              </button>
            ))}
          </div>
        )}
        {messages.map((m, i) => (
          <div key={i} className={`flex ${m.role === "user" ? "justify-end" : "justify-start"}`}>
            <div className={`max-w-[90%] whitespace-pre-wrap rounded-2xl px-3 py-2 text-sm ${m.role === "user" ? "bg-brand-700 text-white" : "bg-slate-100 text-slate-800"}`}>
              {m.content}
              {m.role === "assistant" && m.source && (
                <div className="mt-1 text-[10px] uppercase tracking-wide text-slate-400">{m.source === "ia" ? "IA" : m.source === "offline" ? "modo offline" : "sistema"}</div>
              )}
            </div>
          </div>
        ))}
        {loading && <div className="text-sm text-slate-400">Analisando…</div>}
        <div ref={endRef} />
      </div>
      <div className="mt-3 flex gap-2">
        <input
          className="flex-1 rounded-xl border border-slate-300 px-3 py-2 text-sm"
          placeholder="Digite sua pergunta…"
          value={text}
          maxLength={1000}
          onChange={(e) => setText(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && send(text)}
        />
        <button className="btn-primary" onClick={() => send(text)} disabled={loading || !text.trim()}>
          Enviar
        </button>
      </div>
    </div>
  );
}
