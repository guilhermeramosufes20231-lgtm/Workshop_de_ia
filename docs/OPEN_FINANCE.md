# Preparação para Open Finance

**Estado atual:** não implementado. O MVP funciona só com CSV e dados fictícios.

## Componentes necessários

1. **Provedor/agregador regulado** (instituição participante do Open Finance Brasil ou parceiro que opere como iniciador/receptor de dados). Escolha considerando custo, cobertura de bancos, SLA e sandbox.
2. **Cadastro da aplicação** no provedor: client id/secret (somente no servidor), URLs de redirecionamento, webhooks.
3. **Fluxo de consentimento**: o usuário é redirecionado ao ambiente da instituição/provedor, autentica *lá* e autoriza escopos e prazo (ex.: contas, saldos, transações). O app **nunca** coleta senha bancária.
4. **Backend de tokens**: troca do código de autorização por tokens, armazenamento criptografado (cofre/KMS), renovação e revogação; registro de consentimentos (quem, o quê, até quando) e tela para o usuário revogar.
5. **Camada de dados** (`FinancialDataSource` em `backend/app/services/open_finance.py`): busca contas/transações e **normaliza** para o formato interno (`date`, `description`, `category`, `type`, `amount`, `account`), marcando transferências próprias e fatura de cartão.
6. **Motor de análise**: reaproveita `analysis.py`, `simulator.py` e `ai_service.py` sem alterações; só muda a origem dos dados.
7. **Autenticação e autorização** de usuários do app, isolamento por usuário e criptografia em trânsito (HTTPS) e em repouso.
8. **Conformidade**: LGPD (base legal, minimização, retenção, direitos do titular), logs sem dados sensíveis, política de privacidade e termos.

## Fluxo resumido

```
Usuário → app → provedor (consentimento no ambiente do banco) → callback com código
        → backend troca por token → FinancialDataSource.fetch_transactions()
        → normalização → analysis.py → (agregados) → IA → resposta/painel/Excel
```

## Passos sugeridos

1. Criar conta sandbox no provedor e uma classe `XyzDataSource` que implementa `fetch_transactions`.
2. Adicionar rotas `/api/connect` (inicia consentimento) e `/api/callback`.
3. Persistir consentimentos/tokens (banco + criptografia) e introduzir login.
4. Testar com contas fictícias do sandbox antes de qualquer dado real.
