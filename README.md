# coletor-dados

Coleta automática de dados **públicos** de mercado (catálogos de lojas e preços de marketplaces), a cada 6 horas, pelo GitHub Actions.

- `config/` — o que coletar (lojas, termos de busca)
- `coletores/` — scripts (só leitura de páginas e APIs públicas, com pausa entre chamadas)
- `dados/` — resultado de cada coleta e `status.json` com o resumo da última rodada

Sem login, sem dados pessoais, sem segredos.
