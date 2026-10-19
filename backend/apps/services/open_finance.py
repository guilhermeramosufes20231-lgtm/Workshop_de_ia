"""Camada de dados financeiros — preparada para Open Finance (NÃO implementada).

O restante do app consome apenas `FinancialDataSource.fetch_transactions()`, que
devolve movimentações já normalizadas (mesmo formato de `models.Transaction`).
Hoje a única fonte é o CSV/demo. Para integrar Open Finance, crie uma nova
classe (ex.: `PluggyDataSource`) e registre-a em `get_source`. Veja
docs/OPEN_FINANCE.md para consentimento, tokens e fluxo completo.
Nunca solicite senhas bancárias: o consentimento ocorre no ambiente da instituição.
"""
from typing import Protocol


class FinancialDataSource(Protocol):
    def fetch_transactions(self, user_ref: str, start: str, end: str) -> list[dict]:
        """Retorna movimentações normalizadas (date, description, category, type, amount, account)."""
        ...


class OpenFinanceNotConfigured(NotImplementedError):
    pass


class OpenFinanceDataSource:
    """Esqueleto: use o SDK do provedor escolhido (agregador regulado) aqui."""

    def fetch_transactions(self, user_ref: str, start: str, end: str) -> list[dict]:
        raise OpenFinanceNotConfigured(
            "Integração Open Finance não implementada nesta versão (MVP usa CSV e dados fictícios)."
        )


def get_source(name: str = "csv") -> FinancialDataSource:
    if name == "open_finance":
        return OpenFinanceDataSource()
    raise ValueError("No MVP, os dados chegam por upload de CSV ou dados fictícios (veja /api/import).")
