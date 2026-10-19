# Arquitetura

| Camada | Tecnologia | Responsabilidade |
|---|---|---|
| UI | React 18, TypeScript, Tailwind, Recharts | Landing, painel, chat, simulador, tabela, exportação |
| API | FastAPI | Rotas `/api/*`, limites de tamanho e taxa |
| Dados | `csv_import.py` | Colunas, datas, R$, inválidos, duplicidades, transferências, cartão × fatura |
| Cálculo | `analysis.py`, `simulator.py` | Totais, categorias, série mensal, recorrência, cenários |
| IA | `ai_service.py` | Prompt-base, contexto agregado, fallback offline |
| Excel | `excel_export.py` (XlsxWriter) | Tabelas, fórmulas SUMIFS e gráficos nativos |
| Futuro | `open_finance.py` | Interface `FinancialDataSource` |

Rotas: `GET /api/health`, `GET /api/demo`, `POST /api/import`, `/api/analyze`, `/api/simulate`, `/api/chat`, `/api/recommendations`, `/api/export`.

Decisões: servidor *stateless* (isolamento e privacidade), cálculo determinístico separado da IA (números verificáveis), exportação com fórmulas para a planilha ser editável.
