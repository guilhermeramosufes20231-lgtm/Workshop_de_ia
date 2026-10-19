"""API do Assistente Financeiro IA (stateless: nada é gravado no servidor)."""
import time
from collections import defaultdict, deque
from pathlib import Path

from fastapi import Depends, FastAPI, File, HTTPException, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from fastapi.staticfiles import StaticFiles

from . import config
from .demo_data import demo_csv
from .models import ChatRequest, ExportRequest, Period, SimulateRequest
from .services import ai_service
from .services.analysis import analyze
from .services.csv_import import import_csv
from .services.excel_export import build_workbook
from .services.simulator import simulate

app = FastAPI(title="Assistente Financeiro IA", version="0.1.0")
app.add_middleware(CORSMiddleware, allow_origins=config.CORS_ORIGINS, allow_methods=["*"], allow_headers=["*"])

_hits: dict[str, deque] = defaultdict(deque)


def ai_limit(request: Request) -> None:
    """Limite simples por IP (em memória) para proteger a chave em workshops."""
    ip = request.client.host if request.client else "?"
    q, now = _hits[ip], time.time()
    while q and now - q[0] > 60:
        q.popleft()
    if len(q) >= config.AI_RATE_LIMIT_PER_MIN:
        raise HTTPException(429, "Muitas requisições de IA em pouco tempo. Aguarde um minuto.")
    q.append(now)


def _txs(body: Period) -> list[dict]:
    if len(body.transactions) > config.MAX_TRANSACTIONS:
        raise HTTPException(413, f"Máximo de {config.MAX_TRANSACTIONS} movimentações por análise.")
    return [t.model_dump() for t in body.transactions]


@app.get("/api/health")
def health():
    return {"ok": True, "ai_enabled": config.AI_ENABLED, "model": config.ANTHROPIC_MODEL if config.AI_ENABLED else None}


@app.get("/api/demo")
def demo(profile: str = "pessoal"):
    if profile not in ("pessoal", "empresa"):
        raise HTTPException(400, "Perfil inválido.")
    return import_csv(demo_csv(profile))


@app.post("/api/import")
async def import_file(file: UploadFile = File(...)):
    data = await file.read(config.MAX_UPLOAD_BYTES + 1)
    if len(data) > config.MAX_UPLOAD_BYTES:
        raise HTTPException(413, "Arquivo maior que o limite permitido.")
    try:
        return import_csv(data)
    except ValueError as exc:
        raise HTTPException(400, str(exc))


@app.post("/api/analyze")
def analyze_endpoint(body: Period):
    return analyze(_txs(body), body.profile, body.start, body.end)


@app.post("/api/simulate")
def simulate_endpoint(body: SimulateRequest):
    a = analyze(_txs(body), body.profile, body.start, body.end)
    return simulate(a, body.simulation.reductions, body.simulation.revenue_increase_pct)


@app.post("/api/chat", dependencies=[Depends(ai_limit)])
def chat_endpoint(body: ChatRequest):
    a = analyze(_txs(body), body.profile, body.start, body.end)
    return ai_service.chat(a, [m.model_dump() for m in body.messages])


@app.post("/api/recommendations", dependencies=[Depends(ai_limit)])
def recommendations_endpoint(body: Period):
    a = analyze(_txs(body), body.profile, body.start, body.end)
    return ai_service.recommendations(a)


@app.post("/api/export")
def export_endpoint(body: ExportRequest):
    txs = _txs(body)
    xlsx = build_workbook(
        body.profile, txs, body.start, body.end,
        [r.model_dump() for r in body.recommendations],
        body.simulation.model_dump() if body.simulation else None,
    )
    return Response(
        xlsx,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": 'attachment; filename="assistente-financeiro.xlsx"'},
    )


_dist = Path(__file__).resolve().parents[2] / "frontend" / "dist"
if _dist.exists():  # produção: um único serviço serve API + interface
    app.mount("/", StaticFiles(directory=_dist, html=True), name="frontend")
