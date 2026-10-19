# Assistente Financeiro IA

MVP de assistente financeiro conversacional para **pessoas físicas** e **microempresas**: importe um CSV (ou use dados fictícios), veja o painel com gráficos, converse com a IA, simule cenários e **exporte para Excel com gráficos nativos editáveis**.

> ⚠️ **Protótipo.** Use dados fictícios ou dados que você aceite compartilhar. Sem login, sem criptografia em repouso e sem HTTPS próprio: **não é adequado para dados financeiros reais em produção** (veja [Segurança](#segurança-e-privacidade)).

## Funcionalidades

- Dois perfis: **Finanças pessoais** e **Microempresa** (rótulos e indicadores próprios).
- Importação de CSV: detecta colunas (data, descrição, categoria, tipo, valor, conta), separador `;` ou `,`, valores em R$ (`R$ 1.234,56`), valida linhas, sinaliza **duplicidades**, separa **transferências entre contas próprias** e evita **dupla contagem cartão × fatura**. Você confere a importação e pode des/marcar “Contabilizar” em cada linha.
- Painel: receitas, despesas, saldo/resultado, categorias (pizza), evolução mensal (barras), saldo acumulado (linha), maiores despesas e despesas recorrentes. Respeita o período escolhido.
- Chat com IA (prompt-base no backend). Os **números são calculados por código determinístico**; a IA só interpreta e recomenda.
- Recomendações (fato × estimativa × recomendação, com premissas).
- Simulador: corte de 10/15/20% por categoria e aumento de receita; economia mensal/anual e comparação atual × projetado.
- **Exportar para Excel**: abas Movimentações, Resumo, Categorias, Análise temporal, Recomendações, Simulação e Avisos. Totais são **fórmulas** (SUMIFS) e os 4–5 gráficos são **nativos do Excel**, ligados às tabelas. Respeita filtros e período.
- Sem chave de IA o app continua funcionando (**modo offline** com textos por regras).

## Arquitetura e escolha da stack

```
React + TypeScript + Tailwind + Recharts  ──/api──►  FastAPI (Python)
 (estado só na sessão do navegador)                   ├─ csv_import.py   (limpeza/validação)
                                                      ├─ analysis.py     (cálculos determinísticos)
                                                      ├─ simulator.py
                                                      ├─ ai_service.py   (prompt-base + API de IA; chave só aqui)
                                                      ├─ excel_export.py (XlsxWriter, gráficos nativos)
                                                      └─ open_finance.py (interface futura, NÃO implementada)
```

**Por que Python no backend (e não Node)?** O requisito obrigatório é exportar gráficos *nativos e editáveis*. ExcelJS e a edição comunitária do SheetJS **não criam gráficos nativos**; o **XlsxWriter** (Python) cria. Em vez de exportar só imagens, adaptei o backend. O frontend segue a stack pedida (React + TS + Tailwind).

**Isolamento entre participantes:** o servidor é *stateless*: não grava dados. Cada navegador guarda seus dados e os envia a cada requisição; ninguém acessa dados de outro.

## Requisitos

- Python 3.10+ e Node.js 18+
- (Opcional) chave da API da Anthropic

## Executar localmente

```bash
# 1) Backend
cd backend
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp ../.env.example .env            # Windows: copy ..\.env.example .env  -> edite e coloque sua chave
uvicorn apps.main:app --reload --port 8000

# 2) Frontend (outro terminal)
cd frontend
npm install
npm run dev                        # abre http://localhost:5173
```

### Configurar a IA

1. Crie uma chave em <https://console.anthropic.com>.
2. Em `backend/.env`: `ANTHROPIC_API_KEY=sua-chave` (e, se quiser, `ANTHROPIC_MODEL`).
3. Reinicie o backend. A chave **fica só no servidor**; o frontend nunca a recebe.

Sem chave, aparece um aviso e o chat usa o modo offline.

### Testes

```bash
cd backend && pip install -r requirements.txt && python -m pytest -q tests
```

Gere os CSVs fictícios de exemplo (já incluídos em `data/`) com `python -m apps.demo_data`.

## Formato do CSV

```
data;descricao;categoria;tipo;valor;conta
05/09/2026;Salário Empresa Exemplo;Salário;Receita;R$ 4.800,00;Conta corrente
08/09/2026;Netflix;Assinaturas;Despesa;R$ 55,90;Cartão de crédito
```

Só `data` e `valor` são obrigatórias. Sem coluna `tipo`, valor negativo = despesa. Compras com `conta` contendo “cartão” + linhas “Pagamento fatura…” ativam a regra anti-dupla-contagem.

## Publicar no GitHub

```bash
cd assistente-financeiro-ia
git init && git add . && git commit -m "MVP Assistente Financeiro IA"
git branch -M main
git remote add origin https://github.com/SEU_USUARIO/assistente-financeiro-ia.git
git push -u origin main
```

Confirme antes que `.env` **não** aparece em `git status` (o `.gitignore` já o exclui). Se uma chave vazar, revogue-a no console imediatamente.

### Hospedar para o workshop (opcional)

O backend serve o frontend compilado quando existe `frontend/dist`. Exemplo (Render/Railway/Fly):

- Build: `pip install -r backend/requirements.txt && cd frontend && npm install && npm run build`
- Start: `cd backend && uvicorn apps.main:app --host 0.0.0.0 --port $PORT`
- Variáveis: `ANTHROPIC_API_KEY`, `CORS_ORIGINS` (a URL pública).

Em evento com muitos participantes na mesma chave, mantenha o limite `AI_RATE_LIMIT_PER_MIN` e acompanhe o consumo.

## Segurança e privacidade

- **Fluxo de dados da IA:** o servidor envia ao provedor de IA apenas agregados (totais, categorias, série mensal, recorrências e as 10 maiores despesas com descrição/valor). A lista completa de movimentações não é enviada.
- Nenhum dado é gravado em disco ou banco; o navegador mantém tudo na sessão.
- Nunca peça senhas bancárias. Use somente dados fictícios em demonstrações.
- **Antes de aceitar dados reais:** autenticação, controle de acesso, HTTPS, política de privacidade/LGPD, logs sem dados sensíveis, limites e monitoramento.
- Descrições de movimentações são tratadas como texto (o prompt instrui a IA a ignorar instruções contidas nos dados), mas injeção de prompt nunca é eliminada por completo.

## Open Finance (futuro)

Não implementado. A interface `FinancialDataSource` em `backend/app/services/open_finance.py` e o guia [`docs/OPEN_FINANCE.md`](docs/OPEN_FINANCE.md) descrevem os componentes necessários (provedor regulado, consentimento, tokens, normalização e envio ao motor de análise).

## Limitações conhecidas

- Categorias vêm do arquivo; o app não categoriza automaticamente.
- Detecção de transferências, faturas e duplicidades é heurística: confira o relatório de importação.
- Ponto isolado em valores (`1.234`) é lido como decimal; use `1.234,00`.
- Estimativas e simulações não garantem resultados e não substituem orientação profissional.
- Gráficos do Excel foram validados em LibreOffice/openpyxl; abra no Excel e confira no seu ambiente.
- O frontend não foi compilado nem testado no ambiente em que o código foi gerado (sem acesso à internet para instalar pacotes): rode `npm install && npm run build` e reporte erros de tipo, se houver.
