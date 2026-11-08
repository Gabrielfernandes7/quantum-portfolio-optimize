# Otimização de portfólio de ativos da B3 com computação clássica e quântica

Projeto de estudo e aprendizado sobre otimização de carteiras de investimento. A primeira etapa, já concluída, compara a abordagem clássica de Markowitz em quatro ações da B3. A etapa quântica (QUBO e QAOA) ainda não foi iniciada.

**Aviso:** conteúdo educacional. Não é recomendação de investimento.

## Objetivo

1. Entender a teoria de média-variância (Markowitz): retorno esperado, risco, covariância e fronteira eficiente.
2. Calcular a carteira ótima de forma clássica, que servirá de referência (baseline).
3. Preparar a formulação do problema para ser resolvida com algoritmos quânticos. Essa etapa vem depois.

## Estrutura

```
.
├── notebook/
│   └── 01_fundamento_teorico.ipynb   # teoria e cálculos clássicos
├── data/
│   └── precos_b3.csv                 # cópia local dos preços baixados
├── requirements.txt                  # dependências
├── errors.md                         # erros abertos identificados na auditoria
└── corrigido.md                      # erros já corrigidos, com causa e solução
```

## Como executar

Requer Python 3.10 ou superior.

```bash
python -m venv venv
source venv/bin/activate           # Windows: venv\Scripts\activate
pip install -r requirements.txt
cd notebook
jupyter notebook 01_fundamento_teorico.ipynb
```

Execute as células de cima para baixo, a partir do início. O notebook baixa os preços com `yfinance` na primeira execução e salva uma cópia em `data/`.

## Dados e premissas

- **Ativos:** ITUB4, VALE3, KLBN4 e BBAS3 (B3, em reais).
- **Período:** 2023-01-01 a 2025-12-31, com preços ajustados.
- **Taxa livre de risco:** `rf = 0.13`, aproximação do CDI médio do período. Confira a série SGS 12 do Banco Central antes de usar o valor.
- **Anualização:** 252 dias úteis.
- **Premissas de Markowitz:** carteira só comprada, sem custos de transação, horizonte único e parâmetros constantes no tempo. Retornos são tratados como aproximadamente normais, o que nem sempre se confirma (ver a seção de distribuição no notebook).

## Limitações

- Quatro ativos, dois deles bancos, escolhidos com base no histórico (viés de sobrevivência). Os resultados valem para este universo.
- Três anos de dados dão uma estimativa ruidosa do retorno esperado. Um teste fora da amostra mostrou que a carteira otimizada no treino perdeu para a carteira de pesos iguais em 2025.
- Com tão poucos ativos, o método clássico resolve o problema exato em milissegundos. A comparação com o quântico, quando existir, é didática e não uma demonstração de vantagem.

## Status

- [x] Teoria e cálculos clássicos (notebook 01)
- [x] Auditoria de erros (`errors.md` e `corrigido.md`)
- [ ] Formulação QUBO do problema de seleção de ativos
- [ ] Solução com QAOA e comparação com o baseline clássico

## Referências

[Computação Quântica Aplicacada ao Mercado Financeiro](https://github.com/askery/computacao-quantica-aplicada-ao-mercado-financeiro/blob/main/Quantum_Finance_DualQ.ipynb)
