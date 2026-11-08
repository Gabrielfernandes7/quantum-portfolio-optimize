# Otimização de portfólio de ativos da B3 com computação clássica e quântica

Projeto de estudo sobre otimização de carteiras de investimento. Compara o método clássico de Markowitz com formulações quânticas (QUBO, QAOA e VQE) para quatro ações da B3, com avaliação fora da amostra. As etapas clássica e quântica estão concluídas. Os resultados completos, a metodologia e a discussão estão em [`RESULTADOS.md`](RESULTADOS.md).

**Aviso:** conteúdo educacional. Não é recomendação de investimento.

## Principais conclusões

- A formulação QUBO e a conversão para Ising são exatas e foram verificadas por força bruta.
- QAOA (p ≤ 3) e VQE, em simulação ideal, não superaram um sorteio uniforme como amostradores do ótimo.
- Nenhuma otimização (clássica ou quântica) superou pesos iguais fora da amostra (2025). Com dois anos de treino, a estimativa de retorno esperado é o gargalo.
- Os valores altos de probabilidade reportados pela referência DualQ (63% e 49%) não se reproduziram de forma estável entre sementes.

## Objetivo

1. Entender a teoria de média-variância (Markowitz): retorno esperado, risco, covariância e fronteira eficiente.
2. Estabelecer um baseline clássico exato para comparação.
3. Formular o problema como QUBO e Ising, e testar QAOA e VQE com ferramentas atuais do Qiskit.
4. Reproduzir a abordagem da referência DualQ e comparar com os nossos resultados.

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
├── RESULTADOS.md                     # metodologia, resultados, reflexão, glossário e referências
├── errors.md                         # erros abertos identificados na auditoria
├── corrigido.md                      # erros já corrigidos, com causa e solução
├── audit_quantum.md                  # auditoria do notebook de referência DualQ
├── plan.md                           # plano de trabalho
├── requirements.txt                  # dependências clássicas (notebook 01)
└── requirements-quantum.txt          # dependências quânticas (notebooks 02 a 05)
```

## Como executar

São dois ambientes. O clássico serve para o notebook 01. O quântico, para os notebooks 02 a 05.

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

## Dados e premissas

- **Ativos:** ITUB4, VALE3, KLBN4 e BBAS3 (B3, em reais). O notebook 05 usa BRKM5, ITUB4, VALE3 e KLBN4, como a referência.
- **Período de treino:** 2023-01-01 a 2024-12-31. **Teste fora da amostra:** 2025.
- **Taxa livre de risco:** `rf = 0.13`, aproximação do CDI do período. Confira a série SGS 12 do Banco Central antes de usar o valor.
- **Anualização:** 252 dias úteis, aplicada a μ e Σ.
- **Premissas de Markowitz:** carteira só comprada, sem custos de transação, horizonte único e parâmetros constantes no tempo. Retornos não são normais (curtose em excesso de até 9,3 em BBAS3).

## Limitações

- Quatro ativos e três anos de dados. Os resultados valem para este universo e este período.
- Um único período de teste fora da amostra (2025).
- Simulação ideal na maior parte dos testes. O modelo de ruído é ilustrativo, não calibrado em hardware.
- Poucas sementes por configuração (5 a 8). A probabilidade de ótimo varia muito entre sementes.
- Com quatro ativos, a força bruta resolve o problema em milissegundos. A comparação quântica é metodológica, não uma demonstração de vantagem.
- Discrepâncias ainda abertas, listadas em `RESULTADOS.md`, seção 7 (por exemplo, retorno de pesos iguais em 2025: 21,5% no notebook 01 e 22,46% no notebook 04).

## Status

- [x] Teoria e cálculos clássicos (notebook 01)
- [x] Auditoria de erros (`errors.md` e `corrigido.md`)
- [x] Formulação QUBO e Ising, verificada (notebook 02)
- [x] QAOA com Qiskit atual, com análise de probabilidades (notebook 03)
- [x] Alocação com pesos e VQE (notebook 04)
- [x] Reprodução da abordagem DualQ e comparação (notebook 05)
- [x] Leitura científica dos resultados, reflexão e glossário (`RESULTADOS.md`)
- [ ] Investigar a discrepância de retorno de pesos iguais entre os notebooks 01 e 04
- [ ] Confirmar a série SGS 12 do Banco Central para a taxa livre de risco
- [ ] Testar otimizadores alternativos (SPSA) e mais sementes no VQE e no QAOA

## Referências

Referências completas, com DOI, estão na seção 11 de [`RESULTADOS.md`](RESULTADOS.md). Principais fontes:

- Markowitz, H. (1952). *The Journal of Finance*, 7(1), 77–91.
- Farhi, E., Goldstone, J., & Gutmann, S. (2014). A Quantum Approximate Optimization Algorithm. arXiv:1411.4028.
- Peruzzo, A., et al. (2014). A variational eigenvalue solver on a photonic quantum processor. *Nature Communications*, 5, 4213.
- Quantum_Finance_DualQ.ipynb (askery). Notebook de referência do projeto: [GitHub](https://github.com/askery/computacao-quantica-aplicada-ao-mercado-financeiro/blob/main/Quantum_Finance_DualQ.ipynb). Artigo na RBEF: https://doi.org/10.1590/1806-9126-RBEF-2022-0099
