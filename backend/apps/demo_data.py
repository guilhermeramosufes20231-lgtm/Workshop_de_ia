"""Dados 100% fictícios para demonstração (nenhuma informação real).

Gera CSVs com pequenas "sujeiras" propositais (1 linha duplicada, 2 inválidas,
transferência própria, fatura de cartão) para mostrar o tratamento de dados.
Uso: python -m app.demo_data  -> grava data/demo_pessoal.csv e data/demo_empresa.csv
"""
import random
from pathlib import Path

MONTHS = [(2026, m) for m in range(4, 10)]  # abr-set/2026


def brl(v: float) -> str:
    return "R$ " + f"{v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def _d(y: int, m: int, day: int) -> str:
    return f"{day:02d}/{m:02d}/{y}"


def personal_rows() -> list[tuple]:
    rnd = random.Random(42)
    rows = []  # (data, descricao, categoria, tipo, valor, conta)
    for i, (y, m) in enumerate(MONTHS):
        card = []

        def add(day, desc, cat, tipo, val, conta="Conta corrente"):
            rows.append((_d(y, m, day), desc, cat, tipo, round(val, 2), conta))
            if conta == "Cartão de crédito":
                card.append(val)

        add(5, "Salário Empresa Exemplo", "Salário", "Receita", 4800)
        if i % 3 != 2:
            add(18, "Freelance design", "Renda extra", "Receita", rnd.uniform(600, 900))
        add(6, "Transferência entre contas próprias", "Transferência", "Transferência", 500)
        add(7, "Aluguel", "Moradia", "Despesa", 1500)
        add(10, "Condomínio", "Moradia", "Despesa", 420)
        add(12, "Conta de energia", "Moradia", "Despesa", rnd.uniform(140, 190))
        add(15, "Internet", "Moradia", "Despesa", 109.90)
        add(3, "Academia", "Saúde", "Despesa", 119.90)
        add(8, "Netflix", "Assinaturas", "Despesa", 55.90, "Cartão de crédito")
        add(11, "Spotify", "Assinaturas", "Despesa", 21.90, "Cartão de crédito")
        for d in (4, 11, 18, 25):
            add(d, "Supermercado", "Alimentação", "Despesa", rnd.uniform(220, 340), "Cartão de crédito")
            add(d + 1, "Delivery iFood", "Alimentação", "Despesa", rnd.uniform(38, 85), "Cartão de crédito")
        for d in (9, 23):
            add(d, "Combustível", "Transporte", "Despesa", rnd.uniform(180, 230))
        for d in (2, 8, 14, 20, 27):
            add(d, "Uber", "Transporte", "Despesa", rnd.uniform(14, 35), "Cartão de crédito")
        add(16, "Farmácia", "Saúde", "Despesa", rnd.uniform(60, 140))
        for d in (13, 28):
            add(d, "Restaurante / cinema", "Lazer", "Despesa", rnd.uniform(80, 220), "Cartão de crédito")
        add(21, "Compra online", "Compras", "Despesa", rnd.uniform(100, 400), "Cartão de crédito")
        add(20, "Pagamento fatura cartão", "Cartão", "Despesa", sum(card))
    # Sujeiras propositais
    rows.append(rows[5])  # duplicidade exata
    return rows


def business_rows() -> list[tuple]:
    rnd = random.Random(7)
    rows = []

    for y, m in MONTHS:
        def add(day, desc, cat, tipo, val):
            rows.append((_d(y, m, day), desc, cat, tipo, round(val, 2), "Conta PJ"))

        for d in (7, 14, 21, 28):
            add(d, "Vendas à vista", "Vendas", "Receita", rnd.uniform(6000, 9000))
        for d in (10, 25):
            add(d, "Recebimento maquininha cartão", "Vendas", "Receita", rnd.uniform(4000, 6000))
        add(18, "Serviços prestados", "Serviços", "Receita", rnd.uniform(2000, 3500))
        for d in (3, 12, 24):
            add(d, "Fornecedor mercadorias", "Fornecedores", "Despesa", rnd.uniform(3500, 6000))
        add(15, "Embalagens", "Insumos", "Despesa", rnd.uniform(600, 900))
        add(5, "Aluguel da loja", "Aluguel", "Despesa", 4500)
        add(5, "Folha de pagamento", "Folha de pagamento", "Despesa", 9800)
        add(20, "FGTS e INSS", "Impostos e encargos", "Despesa", 2400)
        add(20, "Simples Nacional", "Impostos e encargos", "Despesa", rnd.uniform(2100, 2800))
        add(10, "Energia elétrica", "Utilidades", "Despesa", rnd.uniform(650, 900))
        add(10, "Internet e telefone", "Utilidades", "Despesa", 220)
        add(8, "Anúncios online", "Marketing", "Despesa", rnd.uniform(600, 1200))
        add(9, "Software contábil", "Software", "Despesa", 189)
        add(26, "Taxas da maquininha", "Taxas bancárias", "Despesa", rnd.uniform(380, 520))
        add(27, "Transferência entre contas (reserva)", "Transferência", "Transferência", 3000)
    rows.append(rows[10])  # duplicidade exata
    return rows


def to_csv(rows: list[tuple], broken: bool = True) -> str:
    lines = ["data;descricao;categoria;tipo;valor;conta"]
    for d, desc, cat, tipo, val, conta in rows:
        lines.append(f"{d};{desc};{cat};{tipo};{brl(val)};{conta}")
    if broken:
        lines.append("31/02/2026;Linha com data inválida;Outros;Despesa;R$ 50,00;Conta corrente")
        lines.append("15/09/2026;Linha com valor inválido;Outros;Despesa;abc;Conta corrente")
    return "\n".join(lines) + "\n"


def demo_csv(profile: str) -> str:
    return to_csv(business_rows() if profile == "empresa" else personal_rows())


if __name__ == "__main__":
    out = Path(__file__).resolve().parents[2] / "data"
    out.mkdir(exist_ok=True)
    (out / "demo_pessoal.csv").write_text(demo_csv("pessoal"), encoding="utf-8")
    (out / "demo_empresa.csv").write_text(demo_csv("empresa"), encoding="utf-8")
    print("CSVs fictícios gravados em", out)
