"""Exportação .xlsx com XlsxWriter: tabelas, fórmulas editáveis e GRÁFICOS NATIVOS do Excel.

Os totais são fórmulas (SUMIFS) sobre a aba Movimentações; os gráficos apontam para as
células das abas Categorias, Análise temporal e Simulação. Ao editar uma movimentação no
Excel, os totais e gráficos se atualizam. Exporta apenas o período/filtros selecionados.
"""
import io
from datetime import datetime

import xlsxwriter
from xlsxwriter.utility import xl_rowcol_to_cell as rc

from .analysis import analyze, in_period
from .simulator import simulate

TYPE_LABEL = {
    "receita": "Receita",
    "despesa": "Despesa",
    "transferencia": "Transferência",
    "pagamento_fatura": "Pagamento de fatura",
}
TIPO_LABEL = {"fato": "Fato", "estimativa": "Estimativa", "recomendacao": "Recomendação"}
GREEN, DARK = "#0F766E", "#0F172A"
MOV = "'Movimentações'!"


def build_workbook(profile, transactions, start, end, recommendations, simulation) -> bytes:
    txs = sorted([t for t in transactions if in_period(t, start, end)], key=lambda t: (t["date"], t["id"]))
    analysis = analyze(transactions, profile, start, end)
    n = len(txs)

    buf = io.BytesIO()
    wb = xlsxwriter.Workbook(buf, {"in_memory": True})
    wb.set_properties({"title": "Assistente Financeiro IA - análise", "comments": "Dados fictícios ou do próprio usuário. Estimativas não garantem resultados."})

    f_title = wb.add_format({"bold": True, "font_size": 16, "font_color": DARK})
    f_head = wb.add_format({"bold": True, "font_color": "white", "bg_color": GREEN, "border": 1, "valign": "vcenter", "text_wrap": True})
    f_money = wb.add_format({"num_format": "R$ #,##0.00"})
    f_money_b = wb.add_format({"num_format": "R$ #,##0.00", "bold": True})
    f_pct = wb.add_format({"num_format": "0.0%"})
    f_pct_in = wb.add_format({"num_format": "0%", "bg_color": "#FEF9C3", "border": 1})
    f_date = wb.add_format({"num_format": "dd/mm/yyyy"})
    f_month = wb.add_format({"num_format": "mmm/yyyy"})
    f_wrap = wb.add_format({"text_wrap": True, "valign": "top"})
    f_bold = wb.add_format({"bold": True})
    f_note = wb.add_format({"italic": True, "font_color": "#475569", "text_wrap": True, "valign": "top"})

    # ---------------- Movimentações ----------------
    ws_mov = wb.add_worksheet("Movimentações")
    ws_res = wb.add_worksheet("Resumo")
    ws_cat = wb.add_worksheet("Categorias")
    ws_tmp = wb.add_worksheet("Análise temporal")
    ws_rec = wb.add_worksheet("Recomendações")
    ws_sim = wb.add_worksheet("Simulação") if simulation else None
    ws_avi = wb.add_worksheet("Avisos")

    cols = ["Data", "Descrição", "Categoria", "Tipo", "Valor (R$)", "Contabilizar", "Conta", "Observação"]
    data = [
        [
            datetime.fromisoformat(t["date"]),
            t["description"],
            t["category"],
            TYPE_LABEL[t["type"]],
            t["amount"],
            "Sim" if t["counted"] else "Não",
            t["account"],
            t["note"],
        ]
        for t in txs
    ]
    ws_mov.add_table(
        0, 0, max(n, 1), len(cols) - 1,
        {
            "name": "Movimentacoes",
            "data": data,
            "style": "Table Style Medium 2",
            "columns": [
                {"header": cols[0], "format": f_date},
                {"header": cols[1]},
                {"header": cols[2]},
                {"header": cols[3]},
                {"header": cols[4], "format": f_money},
                {"header": cols[5]},
                {"header": cols[6]},
                {"header": cols[7]},
            ],
        },
    )
    for i, w in enumerate([12, 38, 20, 20, 15, 13, 18, 60]):
        ws_mov.set_column(i, i, w)
    ws_mov.freeze_panes(1, 0)
    ws_mov.data_validation(1, 5, max(n, 1), 5, {"validate": "list", "source": ["Sim", "Não"]})

    last = max(n, 1) + 1
    val, typ, cat, cnt, dt = (f"{MOV}${c}$2:${c}${last}" for c in "EDCFA")

    def inc_f(extra=""):
        return f'SUMIFS({val},{typ},"Receita",{cnt},"Sim"{extra})'

    def exp_f(extra=""):
        return f'(SUMIFS({val},{typ},"Despesa",{cnt},"Sim"{extra})+SUMIFS({val},{typ},"Pagamento de fatura",{cnt},"Sim"{extra}))'

    s = analysis["summary"]
    labels = analysis["labels"]
    months = analysis["period"]["months"] or 0

    # ---------------- Resumo ----------------
    ws_res.set_column(0, 0, 38)
    ws_res.set_column(1, 1, 20)
    ws_res.set_column(2, 2, 70)
    ws_res.write(0, 0, "Assistente Financeiro IA - Resumo financeiro", f_title)
    ws_res.write(1, 0, "Perfil: " + ("Microempresa" if profile == "empresa" else "Finanças pessoais"))
    ws_res.write(2, 0, f"Período: {analysis['period']['start'] or 'n/d'} a {analysis['period']['end'] or 'n/d'}")
    for c, h in enumerate(["Indicador", "Valor", "Como é calculado"]):
        ws_res.write(4, c, h, f_head)
    if analysis["has_data"] and n:
        r = 5
        rows_spec = []  # (label, kind, payload, note)
        ws_res.write(r, 0, labels["income"]); ws_res.write_formula(r, 1, "=" + inc_f(), f_money_b, s["income"]); ws_res.write(r, 2, "Soma das receitas contabilizadas (aba Movimentações)", f_note)
        ws_res.write(r + 1, 0, labels["expense"]); ws_res.write_formula(r + 1, 1, "=" + exp_f(), f_money_b, s["expense"]); ws_res.write(r + 1, 2, "Soma das despesas contabilizadas (inclui pagamento de fatura apenas se contabilizado)", f_note)
        ws_res.write(r + 2, 0, labels["balance"]); ws_res.write_formula(r + 2, 1, f"={rc(r,1)}-{rc(r+1,1)}", f_money_b, s["balance"]); ws_res.write(r + 2, 2, "Receitas - despesas", f_note)
        ws_res.write(r + 3, 0, "Taxa de poupança / margem do período")
        ws_res.write_formula(r + 3, 1, f'=IF({rc(r,1)}=0,"n/d",{rc(r+2,1)}/{rc(r,1)})', f_pct, (s["savings_rate"] / 100) if s["savings_rate"] is not None else "n/d")
        ws_res.write(r + 3, 2, "Saldo / receitas", f_note)
        ws_res.write(r + 4, 0, "Meses no período"); ws_res.write_number(r + 4, 1, months); ws_res.write(r + 4, 2, "Meses de calendário entre o início e o fim do período", f_note)
        ws_res.write(r + 5, 0, "Média mensal de receitas"); ws_res.write_formula(r + 5, 1, f"={rc(r,1)}/{rc(r+4,1)}", f_money, s["avg_monthly_income"])
        ws_res.write(r + 6, 0, "Média mensal de despesas"); ws_res.write_formula(r + 6, 1, f"={rc(r+1,1)}/{rc(r+4,1)}", f_money, s["avg_monthly_expense"])
        r += 7
        if profile == "empresa":
            ws_res.write(r, 0, "Custos (fornecedores/insumos)"); ws_res.write_number(r, 1, s.get("costs", 0), f_money)
            ws_res.write(r, 2, "Calculado pelo app a partir das categorias de custo; edite se sua classificação for diferente", f_note)
            ws_res.write(r + 1, 0, "Despesas operacionais"); ws_res.write_formula(r + 1, 1, f"={rc(1+4,1)}-{rc(r,1)}", f_money, s.get("operating_expenses", 0))
            ws_res.write(r + 2, 0, "Margem bruta estimada")
            ws_res.write_formula(r + 2, 1, f'=IF({rc(5,1)}=0,"n/d",({rc(5,1)}-{rc(r,1)})/{rc(5,1)})', f_pct, (s["gross_margin_pct"] / 100) if s.get("gross_margin_pct") is not None else "n/d")
            r += 3
        ws_res.write(r, 0, "Categoria de maior despesa"); ws_res.write(r, 1, s.get("top_category") or "n/d"); ws_res.write(r, 2, f"{s.get('top_category_pct') or 0}% das despesas", f_note)
        ws_res.write(r + 1, 0, "Transferências entre contas (fora dos totais)"); ws_res.write_number(r + 1, 1, s["excluded"]["transfers"])
        ws_res.write(r + 2, 0, "Outras movimentações não contabilizadas"); ws_res.write_number(r + 2, 1, s["excluded"]["not_counted"])
        ws_res.write(r + 2, 2, "Duplicidades e pagamentos de fatura (para evitar dupla contagem)", f_note)
    else:
        ws_res.write(5, 0, "Dados insuficientes para o período selecionado.")

    # ---------------- Categorias ----------------
    ws_cat.set_column(0, 0, 28); ws_cat.set_column(1, 2, 16)
    for c, h in enumerate(["Categoria", "Valor (R$)", "% do total"]):
        ws_cat.write(0, c, h, f_head)
    k = len(analysis["categories"])
    for i, c in enumerate(analysis["categories"], start=1):
        ws_cat.write(i, 0, c["category"])
        ref = f"$A{i+1}"
        ws_cat.write_formula(i, 1, "=" + exp_f(f",{cat},{ref}"), f_money, c["value"])
        ws_cat.write_formula(i, 2, f"=IF(SUM($B$2:$B${k+1})=0,0,B{i+1}/SUM($B$2:$B${k+1}))", f_pct, c["pct"] / 100)
    if k:
        pie = wb.add_chart({"type": "pie"})
        pie.add_series({"name": "Despesas por categoria", "categories": ["Categorias", 1, 0, k, 0], "values": ["Categorias", 1, 1, k, 1],
                        "data_labels": {"percentage": True, "leader_lines": True}})
        pie.set_title({"name": "Distribuição das despesas por categoria"}); pie.set_size({"width": 560, "height": 340})
        ws_cat.insert_chart("E2", pie)
        bar = wb.add_chart({"type": "bar"})
        bar.add_series({"name": "Valor (R$)", "categories": ["Categorias", 1, 0, k, 0], "values": ["Categorias", 1, 1, k, 1], "fill": {"color": GREEN}})
        bar.set_title({"name": "Despesas por categoria (R$)"}); bar.set_legend({"none": True}); bar.set_y_axis({"reverse": True})
        bar.set_size({"width": 560, "height": 340})
        ws_cat.insert_chart("E20", bar)

    # ---------------- Análise temporal ----------------
    ws_tmp.set_column(0, 0, 14); ws_tmp.set_column(1, 4, 18)
    for c, h in enumerate(["Mês", "Receitas", "Despesas", "Saldo", "Saldo acumulado"]):
        ws_tmp.write(0, c, h, f_head)
    tl = analysis["timeline"]
    for i, m in enumerate(tl, start=1):
        y, mo = map(int, m["month"].split("-"))
        ws_tmp.write_datetime(i, 0, datetime(y, mo, 1), f_month)
        crit = f',{dt},">="&$A{i+1},{dt},"<"&EDATE($A{i+1},1)'
        ws_tmp.write_formula(i, 1, "=" + inc_f(crit), f_money, m["income"])
        ws_tmp.write_formula(i, 2, "=" + exp_f(crit), f_money, m["expense"])
        ws_tmp.write_formula(i, 3, f"=B{i+1}-C{i+1}", f_money, m["balance"])
        ws_tmp.write_formula(i, 4, f"=D{i+1}" if i == 1 else f"=E{i}+D{i+1}", f_money, m["cumulative"])
    if tl:
        t = len(tl)
        col = wb.add_chart({"type": "column"})
        col.add_series({"name": ["Análise temporal", 0, 1], "categories": ["Análise temporal", 1, 0, t, 0], "values": ["Análise temporal", 1, 1, t, 1], "fill": {"color": GREEN}})
        col.add_series({"name": ["Análise temporal", 0, 2], "categories": ["Análise temporal", 1, 0, t, 0], "values": ["Análise temporal", 1, 2, t, 2], "fill": {"color": "#F97316"}})
        col.set_title({"name": labels["timeline"]}); col.set_size({"width": 620, "height": 320}); col.set_x_axis({"num_format": "mmm/yy"})
        ws_tmp.insert_chart("G2", col)
        line = wb.add_chart({"type": "line"})
        line.add_series({"name": ["Análise temporal", 0, 4], "categories": ["Análise temporal", 1, 0, t, 0], "values": ["Análise temporal", 1, 4, t, 4], "line": {"color": DARK, "width": 2.5}, "marker": {"type": "circle"}})
        line.set_title({"name": "Saldo acumulado (fluxo de caixa)"}); line.set_size({"width": 620, "height": 320}); line.set_x_axis({"num_format": "mmm/yy"})
        ws_tmp.insert_chart("G19", line)

    # ---------------- Recomendações ----------------
    for c, (h, w) in enumerate([("Tipo", 16), ("Título", 36), ("Detalhe", 80), ("Premissas / estimativas", 60)]):
        ws_rec.write(0, c, h, f_head); ws_rec.set_column(c, c, w)
    if recommendations:
        for i, rec in enumerate(recommendations, start=1):
            ws_rec.write(i, 0, TIPO_LABEL.get(rec["tipo"], rec["tipo"]), f_wrap)
            ws_rec.write(i, 1, rec["titulo"], f_wrap); ws_rec.write(i, 2, rec["detalhe"], f_wrap); ws_rec.write(i, 3, rec.get("premissas", ""), f_wrap)
    else:
        ws_rec.write(1, 0, "Nenhuma recomendação gerada. Use 'Gerar recomendações' no app antes de exportar.", f_note)

    # ---------------- Simulação ----------------
    sim = None
    if ws_sim is not None and analysis["has_data"]:
        sim = simulate(analysis, simulation["reductions"], simulation["revenue_increase_pct"])
        ws_sim.set_column(0, 0, 34); ws_sim.set_column(1, 4, 20)
        for c, h in enumerate(["Categoria", "Média mensal atual", "Redução (%)", "Economia mensal", "Economia anual"]):
            ws_sim.write(0, c, h, f_head)
        m = len(sim["rows"])
        for i, row in enumerate(sim["rows"], start=1):
            ws_sim.write(i, 0, row["category"]); ws_sim.write_number(i, 1, row["current_monthly"], f_money)
            ws_sim.write_number(i, 2, row["reduction_pct"] / 100, f_pct_in)
            ws_sim.write_formula(i, 3, f"=B{i+1}*C{i+1}", f_money, row["saving_monthly"])
            ws_sim.write_formula(i, 4, f"=D{i+1}*12", f_money, row["saving_annual"])
        b = m + 2
        ws_sim.write(b, 0, "Aumento de receita simulado (%)", f_bold)
        ws_sim.write_number(b, 1, simulation["revenue_increase_pct"] / 100, f_pct_in)
        for c, h in enumerate(["Indicador (mensal)", "Atual", "Projetado"]):
            ws_sim.write(b + 2, c, h, f_head)
        cmp_ = sim["comparison"]
        inc_cell, exp_cell, bal_cell = b + 3, b + 4, b + 5
        ws_sim.write(inc_cell, 0, "Receita"); ws_sim.write_number(inc_cell, 1, cmp_["current"]["income"], f_money)
        ws_sim.write_formula(inc_cell, 2, f"={rc(inc_cell,1)}*(1+{rc(b,1)})", f_money, cmp_["projected"]["income"])
        ws_sim.write(exp_cell, 0, "Despesa"); ws_sim.write_number(exp_cell, 1, cmp_["current"]["expense"], f_money)
        sum_save = f"SUM(D2:D{m+1})" if m else "0"
        ws_sim.write_formula(exp_cell, 2, f"={rc(exp_cell,1)}-{sum_save}", f_money, cmp_["projected"]["expense"])
        ws_sim.write(bal_cell, 0, "Saldo")
        ws_sim.write_formula(bal_cell, 1, f"={rc(inc_cell,1)}-{rc(exp_cell,1)}", f_money_b, cmp_["current"]["balance"])
        ws_sim.write_formula(bal_cell, 2, f"={rc(inc_cell,2)}-{rc(exp_cell,2)}", f_money_b, cmp_["projected"]["balance"])
        ws_sim.write(bal_cell + 1, 0, "Ganho mensal estimado")
        ws_sim.write_formula(bal_cell + 1, 2, f"={rc(bal_cell,2)}-{rc(bal_cell,1)}", f_money_b, cmp_["gain_monthly"])
        ws_sim.write(bal_cell + 2, 0, "Ganho anual estimado")
        ws_sim.write_formula(bal_cell + 2, 2, f"={rc(bal_cell+1,2)}*12", f_money_b, cmp_["gain_annual"])
        ws_sim.merge_range(bal_cell + 4, 0, bal_cell + 4, 4, sim["disclaimer"], f_note)
        ws_sim.set_row(bal_cell + 4, 32)
        ch = wb.add_chart({"type": "column"})
        for col_i, color in ((1, "#94A3B8"), (2, GREEN)):
            ch.add_series({"name": ["Simulação", b + 2, col_i], "categories": ["Simulação", inc_cell, 0, bal_cell, 0],
                           "values": ["Simulação", inc_cell, col_i, bal_cell, col_i], "fill": {"color": color}})
        ch.set_title({"name": "Cenário atual x projetado (estimativa, por mês)"}); ch.set_size({"width": 560, "height": 320})
        ws_sim.insert_chart("G2", ch)

    # ---------------- Avisos ----------------
    ws_avi.set_column(0, 0, 120)
    ws_avi.write(0, 0, "Avisos e premissas", f_title)
    notes = [
        f"Gerado em {datetime.now():%d/%m/%Y %H:%M} pelo Assistente Financeiro IA (protótipo/MVP).",
        "Transferências entre contas próprias não são receita nem despesa e ficam fora dos totais.",
        "Linhas com 'Contabilizar = Não' (duplicidades, pagamento de fatura com compras já lançadas) não entram nos totais. Altere para 'Sim'/'Não' e as fórmulas recalculam.",
        "Totais e gráficos são fórmulas/gráficos nativos do Excel ligados às abas de dados: edite os dados e os gráficos se atualizam.",
        "Recomendações e simulações são estimativas baseadas nos dados do período e não garantem resultados futuros. Não substituem orientação profissional.",
    ] + analysis["warnings"]
    for i, note in enumerate(notes, start=2):
        ws_avi.write(i, 0, note, f_wrap)

    wb.close()
    return buf.getvalue()
