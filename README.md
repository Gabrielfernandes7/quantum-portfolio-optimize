# Otimização de portfólio de ativos da B3 com computação clássica e quântica

Projeto de estudo sobre otimização de carteiras de investimento. Compara o método clássico de Markowitz com formulações quânticas (QUBO, QAOA e VQE) para quatro ações da B3, com avaliação fora da amostra. As etapas clássica e quântica estão concluídas. Os resultados completos, a metodologia e a discussão estão em [`RESULTADOS.md`](RESULTADOS.md).

**Aviso:** conteúdo educacional. Não é recomendação de investimento.

## Principais conclusões

- A formulação QUBO e a conversão para Ising são exatas e foram verificadas por força bruta.
- QAOA (p ≤ 3) e VQE, em simulação ideal, não superaram um sorteio uniforme como amostradores do ótimo, em média. Com 30 sementes, a mediana de probabilidade do ótimo é zero no VQE em todas as configurações. Poucas execuções concentram a probabilidade no ótimo (a maior chegou a 72,5%).
- O SPSA, com o orçamento testado (1000 avaliações no VQE, 300 no QAOA), não melhora o COBYLA e não converge.
- Nenhuma otimização (clássica ou quântica) superou pesos iguais fora da amostra (2025). Com dois anos de treino, a estimativa de retorno esperado é o gargalo.
- Os valores altos de probabilidade reportados pela referência DualQ (63% e 49%) não se reproduziram de forma estável entre sementes.

## Objetivo

1. Entender a teoria de média-variância (Markowitz): retorno esperado, risco, covariância e fronteira eficiente.
2. Estabelecer um baseline clássico exato para comparação.
3. Formular o problema como QUBO e Ising, e testar QAOA e VQE com ferramentas atuais do Qiskit.
4. Reproduzir a abordagem da referência DualQ e comparar com os nossos resultados.

## Metodologia

Dividimos os dados em treino (2023–2024, para estimar μ e Σ anualizados em 252 dias úteis) e teste fora da amostra (2025, sem uso na escolha das carteiras). Calculamos o baseline clássico de Markowitz (fronteira eficiente e máximo Sharpe, com rf = 0,13) e a formulação QUBO de seleção de ativos, verificada por força bruta e convertida para Ising. Em seguida, testamos QAOA (p ≤ 3) e VQE em simulação ideal, medindo P(ótimo) e P(viável) a partir das amostras e comparando com um sorteio uniforme. No VQE, cada peso usa 3 bits, em passos de 12,5% (12 qubits). Também reproduzimos a abordagem DualQ e fizemos um estudo complementar, com 30 sementes e o otimizador SPSA.

> [!NOTE]
> Nos nossos testes, a formulação QUBO é exata, mas QAOA e VQE não superam um sorteio uniforme como amostradores do ótimo, em média. Com 30 sementes, a mediana do VQE é zero em todas as configurações, e só algumas execuções concentram probabilidade no ótimo. Nenhuma otimização, clássica ou quântica, superou pesos iguais fora da amostra em 2025. O gargalo está na estimativa de retorno esperado com dois anos de treino, e não no algoritmo de otimização. Nos dados disponíveis, a diversificação foi a estratégia mais robusta. Essa conclusão vale para este universo de quatro ativos e para este período de teste.

## Estrutura

```
.
├── notebook/
│   ├── 01_fundamento_teorico.ipynb   # teoria e baseline clássico (Markowitz)
│   ├── 02_qubo_teoria.ipynb          # formulação QUBO e Ising, verificada por força bruta
│   ├── 03_qaoa_qiskit.ipynb          # QAOA com Qiskit: probabilidades, profundidade, penalidade, ruído
│   ├── 04_alocacao_vqe.ipynb         # alocação com pesos discretos (3 bits por ativo) e VQE
│   ├── 05_dualq_abordagem.ipynb      # reprodução da abordagem DualQ e comparação
│   └── figuras/                      # diagramas dos circuitos (VQE e QAOA)
├── data/
│   └── precos_b3.csv                 # cópia local dos preços baixados
├── scripts/
│   └── estudo_sementes_otimizadores.py  # estudo com 30 sementes e SPSA (QAOA e VQE)
├── resultados/                       # saídas do estudo: execuções (CSV) e resumo
├── RESULTADOS.md                     # metodologia, resultados, reflexão, glossário e referências
├── requirements.txt                  # dependências clássicas (notebook 01)
└── requirements-quantum.txt          # dependências quânticas (notebooks 02 a 05 e scripts)
```

## Como executar

São dois ambientes. O clássico serve para o notebook 01. O quântico, para os notebooks 02 a 05 e para o script de estudo.

**Ambiente clássico (Python 3.10 ou superior):**

```bash
python -m venv venv
source venv/bin/activate           # Windows: venv\Scripts\activate
pip install -r requirements.txt
cd notebook
jupyter notebook 01_fundamento_teorico.ipynb
```

**Ambiente quântico (Python 3.14, testado com Qiskit 2.6.2):**

```bash
python3.14 -m venv venv-quantum
venv-quantum/bin/python -m pip install -r requirements-quantum.txt
venv-quantum/bin/python -m ipykernel install --user --name venv-quantum
cd notebook
jupyter notebook 02_qubo_teoria.ipynb
```

Execute as células de cima para baixo. O notebook 01 baixa os preços com `yfinance` na primeira execução e salva uma cópia em `data/`. Os notebooks 02 a 04 leem essa cópia. O 05 baixa de novo os dados de 2016–2021 para reproduzir a referência.

Cada notebook está executado com as saídas salvas. Os resultados de simulação dependem de sementes fixas.

**Estudo complementar (30 sementes e SPSA):**

```bash
venv-quantum/bin/python scripts/estudo_sementes_otimizadores.py
```

O script usa as mesmas configurações dos notebooks 03 e 04, roda em paralelo (8 processos) e grava os resultados em `resultados/`. Ele sobrescreve os CSVs existentes. Os notebooks não são alterados por ele.

## Dados e premissas

- **Ativos:** ITUB4, VALE3, KLBN4 e BBAS3 (B3, em reais). O notebook 05 usa BRKM5, ITUB4, VALE3 e KLBN4, como a referência.
- **Período de treino:** 2023-01-01 a 2024-12-31. **Teste fora da amostra:** 2025.
- **Taxa livre de risco:** `rf = 0.13`, usada em todos os notebooks. Conferida na série SGS 12 do Banco Central (CDI diário, composto em 252 dias úteis): 12,0% a.a. em 2023–2024 e 14,3% a.a. em 2025. O valor 0,13 fica dentro da faixa do período, mas abaixo do CDI realizado em 2025. Detalhes na seção 2 de `RESULTADOS.md`.
- **Anualização:** 252 dias úteis, aplicada a μ e Σ.
- **Premissas de Markowitz:** carteira só comprada, sem custos de transação, horizonte único e parâmetros constantes no tempo. Retornos não são normais (curtose em excesso de até 9,3 em BBAS3).

## Limitações

- Quatro ativos e três anos de dados. Os resultados valem para este universo e este período.
- Um único período de teste fora da amostra (2025).
- Simulação ideal na maior parte dos testes. O modelo de ruído é ilustrativo, não calibrado em hardware.
- Sementes: 3 a 8 por configuração nos notebooks, e 30 no estudo complementar (seção 4.6 de `RESULTADOS.md`). A probabilidade de ótimo varia muito entre sementes.
- SPSA testado com um único orçamento de avaliações. Com ele, não convergiu.
- Com quatro ativos, a força bruta resolve o problema em milissegundos. A comparação quântica é metodológica, não uma demonstração de vantagem.
- Discrepâncias registradas em `RESULTADOS.md`, seção 7. A de retorno de pesos iguais em 2025 (21,5% no notebook 01 e 22,46% no notebook 04) foi resolvida: a célula do notebook 04 perdia o primeiro dia de 2025. Os dois notebooks agora dão 21,47%.

## Status

- [x] Teoria e cálculos clássicos (notebook 01)
- [x] Formulação QUBO e Ising, verificada (notebook 02)
- [x] QAOA com Qiskit atual, com análise de probabilidades (notebook 03)
- [x] Alocação com pesos e VQE (notebook 04)
- [x] Reprodução da abordagem DualQ e comparação (notebook 05)
- [x] Leitura científica dos resultados, reflexão e glossário (`RESULTADOS.md`)
- [x] Investigar a discrepância de retorno de pesos iguais entre os notebooks 01 e 04 (corrigida no notebook 04)
- [x] Confirmar a série SGS 12 do Banco Central para a taxa livre de risco (seção 2 de `RESULTADOS.md`)
- [x] Testar mais sementes (30) no VQE e no QAOA, e o SPSA como otimizador alternativo (seção 4.6 de `RESULTADOS.md`)
- [ ] Testar o SPSA com orçamento maior de avaliações, para ver se ele converge

## Referências

Referências completas, com DOI, estão na seção 11 de [`RESULTADOS.md`](RESULTADOS.md). Principais fontes:

- Markowitz, H. (1952). *The Journal of Finance*, 7(1), 77–91.
- Farhi, E., Goldstone, J., & Gutmann, S. (2014). A Quantum Approximate Optimization Algorithm. arXiv:1411.4028.
- Peruzzo, A., et al. (2014). A variational eigenvalue solver on a photonic quantum processor. *Nature Communications*, 5, 4213.
- Quantum_Finance_DualQ.ipynb (askery). Notebook de referência do projeto: [GitHub](https://github.com/askery/computacao-quantica-aplicada-ao-mercado-financeiro/blob/main/Quantum_Finance_DualQ.ipynb). Artigo na RBEF: https://doi.org/10.1590/1806-9126-RBEF-2022-0099
