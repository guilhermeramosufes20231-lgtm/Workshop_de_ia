"""Importação e tratamento de CSV de movimentações financeiras.

Tudo aqui é determinístico (sem IA): detecção de colunas, valores em reais,
registros inválidos, duplicidades, transferências próprias e dupla contagem
entre compras no cartão e pagamento de fatura.
"""
import csv
import io
import re
import unicodedata
from datetime import datetime

ALIASES = {
    "date": {"data", "date", "dt", "data lancamento", "data da transacao", "data movimentacao", "data mov"},
    "description": {"descricao", "historico", "description", "memo", "lancamento", "estabelecimento", "detalhe"},
    "category": {"categoria", "category", "grupo"},
    "type": {"tipo", "type", "natureza", "entrada/saida", "debito/credito", "d/c"},
    "amount": {"valor", "amount", "value", "valor (r$)", "valor r$", "montante"},
    "account": {"conta", "account", "meio", "origem", "cartao", "banco"},
}

INCOME_WORDS = {"receita", "entrada", "credito", "credit", "c", "income", "recebimento", "venda", "faturamento"}
EXPENSE_WORDS = {"despesa", "saida", "debito", "debit", "d", "expense", "gasto", "custo", "pagamento"}
TRANSFER_WORDS = {"transferencia", "transf", "transferencia entre contas"}

TRANSFER_RE = re.compile(
    r"transfer\w* (entre|propria|para poupanca|p/ poupanca)|transf\.? (entre|propria)|entre contas|mesma titularidade"
)
CARD_PAYMENT_RE = re.compile(r"pag\w* (de )?fatura|pgto fatura|fatura (do )?cart")

DATE_FORMATS = ["%d/%m/%Y", "%d/%m/%y", "%Y-%m-%d", "%d-%m-%Y", "%d.%m.%Y"]


def norm(text: str) -> str:
    text = unicodedata.normalize("NFKD", str(text or ""))
    text = "".join(c for c in text if not unicodedata.combining(c))
    return re.sub(r"\s+", " ", text.lower()).strip()


def parse_money(raw) -> tuple[float, bool]:
    """Converte texto em reais para (valor_absoluto, negativo?).

    Aceita 'R$ 1.234,56', '1234.56', '-45,90', '(100,00)', '45,90-'.
    Regra para ponto isolado: '1.234' é tratado como decimal (1,234); para milhar
    use ponto + vírgula ('1.234,00') ou vários pontos ('1.234.567').
    """
    if raw is None:
        raise ValueError("valor vazio")
    s = str(raw).strip()
    if not s:
        raise ValueError("valor vazio")
    neg = False
    if s.startswith("(") and s.endswith(")"):
        neg, s = True, s[1:-1]
    s = re.sub(r"(?i)r\$|\s|\u00a0", "", s)
    if s.endswith("-"):
        neg, s = True, s[:-1]
    if s.startswith("-"):
        neg, s = True, s[1:]
    elif s.startswith("+"):
        s = s[1:]
    if not re.fullmatch(r"[\d.,]+", s) or not re.search(r"\d", s):
        raise ValueError(f"valor inválido: {raw!r}")
    if "," in s and "." in s:
        if s.rfind(",") > s.rfind("."):
            s = s.replace(".", "").replace(",", ".")
        else:
            s = s.replace(",", "")
    elif "," in s:
        s = s.replace(",", "") if s.count(",") > 1 else s.replace(",", ".")
    elif s.count(".") > 1:
        s = s.replace(".", "")
    try:
        return abs(float(s)), neg
    except ValueError:
        raise ValueError(f"valor inválido: {raw!r}")


def parse_date(raw) -> str:
    s = str(raw or "").strip()[:10]
    for fmt in DATE_FORMATS:
        try:
            return datetime.strptime(s, fmt).date().isoformat()
        except ValueError:
            continue
    raise ValueError(f"data inválida: {raw!r}")


def decode(data: bytes) -> str:
    for enc in ("utf-8-sig", "latin-1"):
        try:
            return data.decode(enc)
        except UnicodeDecodeError:
            continue
    return data.decode("utf-8", errors="replace")


def detect_columns(headers: list[str]) -> dict[str, str]:
    mapping: dict[str, str] = {}
    for h in headers:
        n = norm(h)
        for field, names in ALIASES.items():
            if field not in mapping and n in names:
                mapping[field] = h
    return mapping


def import_csv(data: bytes | str) -> dict:
    text = decode(data) if isinstance(data, bytes) else data
    if not text.strip():
        raise ValueError("O arquivo está vazio.")
    first = text.splitlines()[0]
    delimiter = ";" if first.count(";") >= first.count(",") and ";" in first else ("\t" if "\t" in first else ",")
    reader = csv.DictReader(io.StringIO(text), delimiter=delimiter)
    headers = reader.fieldnames or []
    cols = detect_columns(headers)
    missing = [f for f in ("date", "amount") if f not in cols]
    if missing:
        names = {"date": "data", "amount": "valor"}
        raise ValueError(
            "Colunas obrigatórias não encontradas: "
            + ", ".join(names[m] for m in missing)
            + f". Colunas lidas: {', '.join(headers)}"
        )

    warnings: list[str] = []
    invalid: list[dict] = []
    rows: list[dict] = []
    total_rows = 0
    for line_no, raw in enumerate(reader, start=2):
        if not any((v or "").strip() for v in raw.values() if isinstance(v, str)):
            continue
        total_rows += 1
        try:
            iso = parse_date(raw.get(cols["date"]))
            value, negative = parse_money(raw.get(cols["amount"]))
        except ValueError as exc:
            invalid.append({"line": line_no, "reason": str(exc), "raw": ";".join(str(v) for v in raw.values())[:120]})
            continue
        desc = (raw.get(cols["description"]) or "").strip() if "description" in cols else ""
        cat = (raw.get(cols["category"]) or "").strip() if "category" in cols else ""
        acct = (raw.get(cols["account"]) or "").strip() if "account" in cols else ""
        tipo_txt = norm(raw.get(cols["type"])) if "type" in cols else ""

        ndesc, ncat = norm(desc), norm(cat)
        if tipo_txt in TRANSFER_WORDS or ncat.startswith("transfer") or TRANSFER_RE.search(f"{ndesc} {ncat}"):
            tx_type = "transferencia"
        elif CARD_PAYMENT_RE.search(f"{ndesc} {ncat}"):
            tx_type = "pagamento_fatura"
        elif tipo_txt in INCOME_WORDS:
            tx_type = "receita"
        elif tipo_txt in EXPENSE_WORDS:
            tx_type = "despesa"
        else:
            tx_type = "despesa" if negative else "receita"
        rows.append(
            {
                "date": iso,
                "description": desc or "(sem descrição)",
                "category": cat or "Sem categoria",
                "type": tx_type,
                "amount": round(value, 2),
                "account": acct,
                "counted": tx_type != "transferencia",
                "note": "Transferência entre contas próprias: não é receita nem despesa" if tx_type == "transferencia" else "",
            }
        )

    rows.sort(key=lambda r: r["date"])

    # Duplicidades exatas (mesma data, descrição, valor, tipo e conta): mantém a 1ª.
    seen: set = set()
    dup_count, dup_value = 0, 0.0
    for r in rows:
        key = (r["date"], norm(r["description"]), r["amount"], r["type"], norm(r["account"]))
        if key in seen:
            r["counted"] = False
            r["note"] = "Possível duplicidade (linha idêntica): não contabilizada"
            dup_count += 1
            dup_value += r["amount"]
        else:
            seen.add(key)

    # Dupla contagem cartão x fatura.
    card_purchases = any(
        r["type"] == "despesa" and "cart" in norm(r["account"]) and r["counted"] for r in rows
    )
    card_payments = [r for r in rows if r["type"] == "pagamento_fatura" and r["counted"]]
    double_count_avoided = False
    if card_payments:
        if card_purchases:
            for r in card_payments:
                r["counted"] = False
                r["note"] = "Pagamento de fatura: não contabilizado (as compras no cartão já estão como despesas)"
            double_count_avoided = True
        else:
            warnings.append(
                "Há pagamentos de fatura, mas nenhuma compra identificada no cartão. "
                "Eles foram contados como despesa; sem o detalhe das compras, a análise por categoria fica limitada."
            )

    uncategorized = sum(1 for r in rows if r["category"] == "Sem categoria")
    if "category" not in cols:
        warnings.append("Arquivo sem coluna de categoria: todas as movimentações ficaram em 'Sem categoria'.")
    elif uncategorized and rows and uncategorized / len(rows) > 0.2:
        warnings.append(f"{uncategorized} movimentações sem categoria; a análise por categoria pode ficar imprecisa.")
    if "type" not in cols:
        warnings.append("Sem coluna de tipo: o sinal do valor foi usado (negativo = despesa, positivo = receita).")
    if not rows:
        warnings.append("Nenhuma linha válida foi encontrada.")

    for i, r in enumerate(rows, start=1):
        r["id"] = i

    report = {
        "total_rows": total_rows,
        "valid": len(rows),
        "invalid": invalid[:20],
        "invalid_count": len(invalid),
        "duplicates": dup_count,
        "duplicates_value": round(dup_value, 2),
        "transfers": sum(1 for r in rows if r["type"] == "transferencia"),
        "card_payments": len(card_payments),
        "card_double_count_avoided": double_count_avoided,
        "columns_detected": cols,
        "delimiter": delimiter,
        "warnings": warnings,
    }
    return {"transactions": rows, "report": report}
