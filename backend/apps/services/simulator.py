"""Simulador de cenários: valores são estimativas, não garantias."""

DISCLAIMER = (
    "Valores simulados são estimativas baseadas na média mensal do período analisado. "
    "Não garantem resultados futuros: preços, renda e hábitos podem mudar."
)


def simulate(analysis: dict, reductions: dict[str, float], revenue_increase_pct: float = 0.0) -> dict:
    if not analysis.get("has_data"):
        return {"rows": [], "comparison": {}, "assumptions": [], "disclaimer": DISCLAIMER}
    months = analysis["period"]["months"] or 1
    cats = {c["category"]: c for c in analysis["categories"]}
    rows, saving_month = [], 0.0
    for cat, pct in reductions.items():
        if cat not in cats or pct <= 0:
            continue
        pct = min(float(pct), 100.0)
        monthly = cats[cat]["value"] / months
        save = monthly * pct / 100
        saving_month += save
        rows.append(
            {
                "category": cat,
                "current_monthly": round(monthly, 2),
                "reduction_pct": pct,
                "saving_monthly": round(save, 2),
                "saving_annual": round(save * 12, 2),
            }
        )
    s = analysis["summary"]
    inc_now, exp_now = s["avg_monthly_income"], s["avg_monthly_expense"]
    extra_income = inc_now * max(revenue_increase_pct, 0) / 100
    inc_new, exp_new = inc_now + extra_income, exp_now - saving_month
    comparison = {
        "current": {"income": round(inc_now, 2), "expense": round(exp_now, 2), "balance": round(inc_now - exp_now, 2)},
        "projected": {"income": round(inc_new, 2), "expense": round(exp_new, 2), "balance": round(inc_new - exp_new, 2)},
        "gain_monthly": round((inc_new - exp_new) - (inc_now - exp_now), 2),
        "gain_annual": round(((inc_new - exp_new) - (inc_now - exp_now)) * 12, 2),
        "saving_monthly": round(saving_month, 2),
        "saving_annual": round(saving_month * 12, 2),
        "extra_income_monthly": round(extra_income, 2),
    }
    assumptions = [
        f"Média mensal calculada sobre {months} mês(es) do período selecionado.",
        "A redução percentual é aplicada integralmente à média mensal da categoria.",
        f"Aumento de receita simulado: {revenue_increase_pct:g}% sobre a receita média mensal.",
        "Anualização = valor mensal x 12, sem inflação ou sazonalidade.",
    ]
    return {"rows": rows, "comparison": comparison, "assumptions": assumptions, "disclaimer": DISCLAIMER}
