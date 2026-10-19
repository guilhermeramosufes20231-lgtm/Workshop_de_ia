"""Cálculos financeiros determinísticos. A IA só interpreta estes resultados."""
import re
import statistics
from collections import defaultdict
from datetime import date

from .csv_import import norm

COST_CATEGORIES = {"fornecedores", "insumos", "materia-prima", "materia prima", "custo de mercadoria", "custos", "frete"}

LABELS = {
    "pessoal": {
        "income": "Total de receitas",
        "expense": "Total de despesas",
        "balance": "Saldo do período",
        "timeline": "Receitas e despesas ao longo do tempo",
    },
    "empresa": {
        "income": "Receitas e recebimentos",
        "expense": "Custos e despesas",
        "balance": "Resultado estimado do período",
        "timeline": "Evolução do fluxo de caixa",
    },
}


def is_expense(t: dict) -> bool:
    return t["type"] in ("despesa", "pagamento_fatura")


def in_period(t: dict, start: str | None, end: str | None) -> bool:
    return (not start or t["date"] >= start) and (not end or t["date"] <= end)


def month_span(start: str, end: str) -> int:
    s, e = date.fromisoformat(start), date.fromisoformat(end)
    return (e.year - s.year) * 12 + e.month - s.month + 1


def analyze(transactions: list[dict], profile: str = "pessoal", start: str | None = None, end: str | None = None) -> dict:
    txs = [t for t in transactions if in_period(t, start, end)]
    counted = [t for t in txs if t["counted"] and t["type"] != "transferencia"]
    warnings: list[str] = []
    labels = LABELS[profile]

    if not counted:
        return {
            "profile": profile,
            "labels": labels,
            "period": {"start": start, "end": end, "months": 0},
            "has_data": False,
            "summary": {},
            "categories": [],
            "timeline": [],
            "top_expenses": [],
            "recurring": [],
            "warnings": ["Sem movimentações contabilizadas no período selecionado: dados insuficientes para análise."],
        }

    p_start = start or min(t["date"] for t in txs)
    p_end = end or max(t["date"] for t in txs)
    months = max(month_span(p_start, p_end), 1)

    income = round(sum(t["amount"] for t in counted if t["type"] == "receita"), 2)
    expenses = [t for t in counted if is_expense(t)]
    expense = round(sum(t["amount"] for t in expenses), 2)
    balance = round(income - expense, 2)

    by_cat: dict[str, dict] = defaultdict(lambda: {"value": 0.0, "count": 0})
    for t in expenses:
        by_cat[t["category"]]["value"] += t["amount"]
        by_cat[t["category"]]["count"] += 1
    categories = [
        {
            "category": c,
            "value": round(v["value"], 2),
            "pct": round(v["value"] / expense * 100, 1) if expense else 0.0,
            "count": v["count"],
        }
        for c, v in sorted(by_cat.items(), key=lambda kv: -kv[1]["value"])
    ]

    by_month: dict[str, dict] = defaultdict(lambda: {"income": 0.0, "expense": 0.0})
    for t in counted:
        m = t["date"][:7]
        if t["type"] == "receita":
            by_month[m]["income"] += t["amount"]
        elif is_expense(t):
            by_month[m]["expense"] += t["amount"]
    timeline, cumulative = [], 0.0
    for m in sorted(by_month):
        inc, exp = round(by_month[m]["income"], 2), round(by_month[m]["expense"], 2)
        cumulative += inc - exp
        timeline.append({"month": m, "income": inc, "expense": exp, "balance": round(inc - exp, 2), "cumulative": round(cumulative, 2)})

    top_expenses = [
        {"date": t["date"], "description": t["description"], "category": t["category"], "amount": t["amount"]}
        for t in sorted(expenses, key=lambda t: -t["amount"])[:10]
    ]

    # Despesas recorrentes: mesma descrição em >= 3 meses distintos, valor estável.
    groups: dict[str, list[dict]] = defaultdict(list)
    for t in expenses:
        key = re.sub(r"[\d/]+|[^a-z ]", "", norm(t["description"])).strip()
        if key:
            groups[key].append(t)
    recurring = []
    for items in groups.values():
        ms = {t["date"][:7] for t in items}
        if len(ms) < 3:
            continue
        per_month: dict[str, float] = defaultdict(float)
        for t in items:
            per_month[t["date"][:7]] += t["amount"]
        vals = list(per_month.values())
        mean = statistics.mean(vals)
        if mean and statistics.pstdev(vals) / mean <= 0.2:
            recurring.append(
                {
                    "description": items[0]["description"],
                    "category": items[0]["category"],
                    "months": len(ms),
                    "avg_monthly": round(mean, 2),
                }
            )
    recurring.sort(key=lambda r: -r["avg_monthly"])

    summary = {
        "income": income,
        "expense": expense,
        "balance": balance,
        "savings_rate": round(balance / income * 100, 1) if income else None,
        "avg_monthly_income": round(income / months, 2),
        "avg_monthly_expense": round(expense / months, 2),
        "n_income": sum(1 for t in counted if t["type"] == "receita"),
        "n_expense": len(expenses),
        "top_category": categories[0]["category"] if categories else None,
        "top_category_pct": categories[0]["pct"] if categories else None,
        "excluded": {
            "transfers": sum(1 for t in txs if t["type"] == "transferencia"),
            "not_counted": sum(1 for t in txs if not t["counted"] and t["type"] != "transferencia"),
        },
    }
    if profile == "empresa":
        costs = round(sum(c["value"] for c in categories if norm(c["category"]) in COST_CATEGORIES), 2)
        summary["costs"] = costs
        summary["operating_expenses"] = round(expense - costs, 2)
        summary["gross_margin_pct"] = round((income - costs) / income * 100, 1) if income else None

    if months < 2:
        warnings.append("Período com menos de 2 meses: tendências e recorrências não podem ser avaliadas com segurança.")
    elif months < 3:
        warnings.append("Menos de 3 meses de dados: a detecção de despesas recorrentes fica limitada.")
    if not income:
        warnings.append("Nenhuma receita no período: taxa de poupança e margens não foram calculadas.")
    sem_cat = next((c for c in categories if c["category"] == "Sem categoria"), None)
    if sem_cat and sem_cat["pct"] > 20:
        warnings.append(f"{sem_cat['pct']}% das despesas estão sem categoria; a análise por categoria é parcial.")

    return {
        "profile": profile,
        "labels": labels,
        "period": {"start": p_start, "end": p_end, "months": months},
        "has_data": True,
        "summary": summary,
        "categories": categories,
        "timeline": timeline,
        "top_expenses": top_expenses,
        "recurring": recurring,
        "warnings": warnings,
    }
