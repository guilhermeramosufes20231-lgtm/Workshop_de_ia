from typing import Literal, Optional

from pydantic import BaseModel, Field

Profile = Literal["pessoal", "empresa"]
TxType = Literal["receita", "despesa", "transferencia", "pagamento_fatura"]


class Transaction(BaseModel):
    id: int
    date: str  # ISO yyyy-mm-dd
    description: str = Field(max_length=300)
    category: str = Field(max_length=100)
    type: TxType
    amount: float  # sempre positivo; o sinal vem do tipo
    account: str = ""
    counted: bool = True  # False = não entra nos totais (transferência, duplicidade etc.)
    note: str = ""


class Period(BaseModel):
    profile: Profile = "pessoal"
    transactions: list[Transaction]
    start: Optional[str] = None
    end: Optional[str] = None


class ChatMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(max_length=4000)


class ChatRequest(Period):
    messages: list[ChatMessage]


class SimulationParams(BaseModel):
    reductions: dict[str, float] = {}  # categoria -> % (0-100)
    revenue_increase_pct: float = 0.0


class SimulateRequest(Period):
    simulation: SimulationParams


class Recommendation(BaseModel):
    tipo: Literal["fato", "estimativa", "recomendacao"] = "recomendacao"
    titulo: str
    detalhe: str
    premissas: str = ""


class ExportRequest(Period):
    recommendations: list[Recommendation] = []
    simulation: Optional[SimulationParams] = None
