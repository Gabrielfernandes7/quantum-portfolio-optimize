# Otimização de carteira com Markowitz, QUBO, QAOA e VQE: metodologia e resultados

Documento de leitura científica dos cinco notebooks do projeto. Cada seção descreve o método, o resultado observado e a sua limitação. Os números vêm das saídas salvas em cada notebook, e as discrepâncias encontradas aparecem na seção 7.

**Aviso:** material educacional. Não é recomendação de investimento.

---

## 1. Objetivo

Verificar se a formulação quântica da carteira (QUBO, QAOA e VQE), usada na referência DualQ, produz soluções úteis para escolher a alocação entre quatro ações da B3 (BBAS3, ITUB4, KLBN4 e VALE3). Para isso, comparamos cada método com um baseline clássico exato e com uma estratégia ingênua (pesos iguais), em um teste fora da amostra.

## 2. Dados

- **Fonte:** cotações de fechamento baixadas com `yfinance` e salvas em `data/precos_b3.csv`.
- **Ativos:** BBAS3, ITUB4, KLBN4 e VALE3 (B3, em reais).
- **Treino:** 2023-01-01 a 2024-12-31 para estimar μ e Σ.
- **Teste:** 2025-01-01 a 2025-12-30, usado apenas para avaliação fora da amostra.
- **Anualização:** 252 dias úteis, aplicada a μ e Σ.
- **Taxa livre de risco:** rf = 0,13, aproximação do CDI médio do período, ainda não conferida na série SGS 12 do Banco Central.

## 3. Métodos

### 3.1 Baseline clássico (notebook 01)

Markowitz com média-variância: retorno esperado μ, covariância Σ, fronteira eficiente calculada por otimização (SLSQP), e carteira de máximo Sharpe. A fronteira foi construída pela minimização de wᵀΣw sob retorno-alvo, com pesos entre 0 e 1 e soma igual a 1.

### 3.2 Formulação QUBO (notebook 02)

Escolha de ativos com restrição de orçamento, conforme a DualQ:

$$
\min_{x\in\{0,1\}^n} \; q\,x^T\Sigma x - \mu^T x + \lambda(\mathbf{1}^T x - B)^2
$$

com q = 0,5, B = 2 e λ testado em {0,01; 0,1; 1; 10}. A forma matricial foi conferida contra a forma com pesos (erro de 10⁻¹⁵), e a conversão para Ising, contra a forma QUBO (erro de 10⁻¹⁵).

### 3.3 QAOA em Qiskit (notebook 03)

QAOA com StatevectorSampler (simulação ideal, 4096 shots), profundidades p ∈ {1, 2, 3} e cinco sementes. Medimos P(ótimo) e P(viável) a partir da distribuição de amostras, e não apenas a resposta do solver, porque `MinimumEigenOptimizer` devolve a amostra de menor energia. Comparamos com um sorteio uniforme sobre os 16 vetores. Também fizemos varredura de λ e um modelo de ruído de despolarização (taxas ilustrativas, não calibradas em hardware).

### 3.4 Alocação com pesos discretos e VQE (notebook 04)

Cada ativo recebe 3 bits: w_i = u_i/8, com u_i ∈ {0,…,7} e Σu_i = 8. São 12 qubits e 161 alocações viáveis, entre 4096 vetores. Baselines: (a) Markowitz contínuo, com SLSQP; (b) força bruta sobre as 161 alocações viáveis; (c) VQE com ansatz RY/CZ (`n_local`, entrelaçamento completo), com 1, 2 e 3 repetições e três sementes, COBYLA com até 1000 avaliações e ponto inicial semeado.

### 3.5 Reprodução da abordagem DualQ (notebook 05)

Reproduzimos o caso da referência (ativos BRKM5, ITUB4, VALE3 e KLBN4, de 2016 a 2021) com os hiperparâmetros dela: q = 0,5, B = 2, λ = 4, QAOA com p = 20 e COBYLA de 250 iterações, VQE com 11 repetições e COBYLA de 500 iterações. Depois aplicamos a mesma abordagem aos dados de 01, em duas unidades: μ anual com Σ diária (como na referência) e μ e Σ anuais. Cada configuração foi repetida com 8 sementes.

## 4. Resultados

### 4.1 Notebook 01: baseline clássico

| Medida | Resultado |
|---|---|
| Melhor Sharpe da fronteira (treino) | 0,84 |
| Melhor Sharpe da nuvem aleatória (treino) | 0,73 |
| Pesos iguais em 2025 | retorno 21,5%, risco 15,2%, Sharpe 0,558 |
| Máximo Sharpe otimizado no treino, em 2025 | retorno −2,7%, risco 22,9%, Sharpe −0,685 |
| Concentração da carteira otimizada | 77% em BBAS3 |
| Curtose em excesso de BBAS3 | 9,34 (distribuição com caudas pesadas) |

**Leitura:** a otimização ajusta o ruído das estimativas. Ao ser testada fora da amostra, a carteira otimizada perde para pesos iguais.

### 4.2 Notebook 02: formulação QUBO

- Com treino 2023–2024: μ = (BBAS3 29,5%; ITUB4 19,6%; KLBN4 20,4%; VALE3 −13,3%).
- Ótimo exato: BBAS3 + KLBN4 (x = 1010), valor f = −0,4465.
- λ = 0,1 deixa o mínimo global inviável (3 ativos). A partir de λ = 1, o mínimo é viável.
- Para q entre 0,1 e 10, a escolha não muda. A correlação BBAS3–ITUB4 de 0,60 explica por que o par BBAS3–ITUB4 não é escolhido.

**Leitura:** a formulação está correta, verificada por força bruta. A seleção é insensível a q no intervalo testado, o que indica que a escolha depende mais dos dados do que do apetite ao risco.

### 4.3 Notebook 03: QAOA

| p | P(ótimo) média | P(viável) média |
|---|---|---|
| 1 | 1,2% | 7,5% |
| 2 | 2,3% | 13,5% |
| 3 | 2,5% | 9,7% |
| Sorteio uniforme | 6,25% | 37,5% |

- O solver acertou o ótimo em todas as execuções (15 de 15), mas isso ocorre porque ele devolve a amostra de menor energia.
- Com λ = 0,1, P(viável) cai de 8,6% para 5,2%. Com λ = 1 e λ = 10, o efeito é quase o mesmo.
- Com ruído (taxas ilustrativas), P(viável) em p = 2 cai de 13,5% para 9,5%, com grande dispersão entre sementes.

**Leitura:** nesta formulação e nesses parâmetros, o QAOA como amostrador tem desempenho inferior ao sorteio uniforme, tanto para o ótimo quanto para a viabilidade.

### 4.4 Notebook 04: alocação com pesos e VQE

| Estratégia | Pesos (BBAS3, ITUB4, KLBN4, VALE3) | Retorno 2025 | Risco 2025 | Sharpe 2025 |
|---|---|---|---|---|
| Pesos iguais | 25%, 25%, 25%, 25% | 22,46% | 15,17% | 0,624 |
| Markowitz contínuo | 100%, 0%, 0%, 0% | −0,08% | 27,98% | −0,467 |
| Força bruta discreta | 87,5%, 0%, 12,5%, 0% | −0,88% | 25,12% | −0,553 |
| VQE (melhor amostra viável) | 87,5%, 0%, 12,5%, 0% | −0,88% | 25,12% | −0,553 |

- Discretização: custo de 0,0073 na função objetivo em relação ao contínuo.
- Viabilidade do VQE: até 53% das amostras de uma execução, contra 3,9% do sorteio.
- Acerto do ótimo viável: 2 de 9 execuções. Nesses casos, P(ótimo) ≈ 0,003%, abaixo do sorteio (0,024%).
- Avaliações do COBYLA: entre 279 e 540, abaixo do limite de 1000.

**Leitura:** o VQE aprende a respeitar a restrição de soma, mas não concentra probabilidade no ótimo. Mesmo a melhor carteira viável do VQE coincide com a da força bruta, e perde para pesos iguais fora da amostra.

### 4.5 Notebook 05: abordagem DualQ

**Reprodução do caso da referência (dados de 2016–2021):**

- O valor exato f = −0,6152 coincide com o da referência, mas o vetor ótimo sai como 1010 (BRKM5 + VALE3). A referência rotula o mesmo valor como 1001 (BRKM5 + KLBN4).
- Com 8 sementes:

| Método | Média de P(ótimo) | Mínimo | Máximo | Referência DualQ |
|---|---|---|---|---|
| QAOA p = 20 | 4,5% | 0,2% | 18,1% | 63,3% |
| VQE 11 reps | 15,3% | 0,0% | 72,7% | 49,0% |

**Mesma abordagem nos dados de 01 (8 sementes):**

| Configuração | QAOA: média (mín–máx) | VQE: média (mín–máx) |
|---|---|---|
| Unidades da DualQ (μ anual, Σ diária) | 5,8% (0,3%–9,8%) | 14,8% (0,0%–49,9%) |
| Unidades consistentes (μ e Σ anuais) | 2,9% (0,02%–11,0%) | 13,1% (0,0%–46,9%) |

**Leitura:** a probabilidade de ótimo depende fortemente da semente. Os valores altos reportados pela referência (63% e 49%) aparecem em uma única execução. Na nossa reprodução, o VQE alcança essa faixa em algumas sementes, mas o QAOA não alcança 63% em nenhuma delas. Uma única execução com semente não é evidência suficiente.

## 5. Discussão

1. **Formulação:** a conversão para QUBO e para Ising é exata. Os erros de conversão são da ordem de 10⁻¹⁵ e foram verificados por força bruta.
2. **Algoritmos:** tanto QAOA quanto VQE encontram o ótimo em algumas execuções, mas a probabilidade de encontrá-lo é baixa e muito sensível à semente. Em nossos testes, a probabilidade de ótimo fica abaixo do sorteio uniforme para o QAOA, e apenas em casos isolados do VQE supera o sorteio.
3. **Retorno da otimização:** em todos os métodos, a carteira escolhida com dados de treino perde para pesos iguais em 2025. O problema central é a estimativa de μ com dois anos de dados, e não o algoritmo de otimização.
4. **Papel das unidades:** misturar retorno anual com covariância diária altera o problema. Em nossos testes, a escolha de unidades mudou as probabilidades de forma importante, mas não mudou a conclusão de que a otimização não supera pesos iguais.
5. **Penalidade:** λ precisa ser grande o bastante para que o mínimo global seja viável. Em 02 e 04, λ = 1 não bastava; em 04, usamos λ = 10.

## 6. Ameaças à validade

- **Número de ativos e de períodos:** quatro ativos e três anos de dados são uma amostra pequena. Os resultados valem para este universo.
- **Um único ano de teste:** 2025 é um único período fora da amostra.
- **Simulação ideal:** a maior parte dos resultados é de simulação sem ruído. O modelo de ruído é ilustrativo.
- **Sementes:** o número de sementes é pequeno (5 a 8 por configuração). A dispersão observada é grande.
- **Ordem dos ativos:** a referência DualQ parece rotular ativos com uma ordem diferente da dos dados. Não conseguimos confirmar isso sem acesso aos dados originais dela.
- **Versões de software:** a referência usa `qiskit.aqua` (Qiskit 0.32). Nossa implementação usa Qiskit 2.6.2. Diferenças podem vir do ponto inicial e do otimizador.

## 7. Discrepâncias registradas

1. **Retorno de pesos iguais em 2025:** 21,5% no notebook 01 e 22,46% no notebook 04, com os mesmos ativos e período. A taxa livre de risco é 0,13 nos dois. A causa não foi identificada.
2. **Máximo Sharpe x mínimo de variância:** o notebook 04 usa a função de custo q·wᵀΣw − μᵀw, e o notebook 01 usa o máximo Sharpe. Por isso, os resultados fora da amostra não são diretamente comparáveis.
3. **Ordem dos ativos na referência DualQ:** o vetor ótimo 1001 da referência corresponde a 1010 nos nossos dados, com o mesmo valor. Isso sugere rotulagem trocada, a confirmar.

## 8. Conclusões

1. **A formulação é válida.** O QUBO e o Ising reproduzem a função de custo nas 16 bitstrings, e o solver exato encontra o ótimo.
2. **Nos nossos testes, QAOA e VQE não superam o sorteio como amostradores do ótimo.** Os resultados altos da referência aparecem apenas em execuções isoladas e não são reproduzidos de forma estável.
3. **Nenhuma otimização superou pesos iguais fora da amostra.** Com dois anos de treino, a estimativa de μ é insuficiente, e a carteira otimizada concentra em um ativo.
4. **A recomendação metodológica** para trabalhos futuros é: repetir cada configuração com muitas sementes, reportar média e dispersão, usar unidades consistentes, testar fora da amostra em mais de um período, e confirmar a série SGS 12 do Banco Central antes de usar rf.
5. **Para investimento**, a diversificação foi a estratégia mais robusta nos dados disponíveis. Esta conclusão é específica do universo de quatro ativos e do período analisado.

---

## 9. Reflexão: o que funcionou, o que não funcionou e por quê

Esta seção avalia cada método pelo critério do projeto: a solução é melhor que a alternativa simples, e o resultado se mantém fora da amostra? As causas indicadas são hipóteses, a menos que digam o contrário.

### 9.1 O que funcionou

**Formulação QUBO e conversão para Ising.** Funcionou de forma exata. As duas conversões reproduzem a função de custo nas 16 bitstrings, com erro de 10⁻¹⁵. Essa parte é reutilizável para qualquer número de ativos, desde que a verificação por força bruta continue sendo feita enquanto o problema for pequeno.

**Otimização clássica contínua (Markowitz com SLSQP).** Funcionou computacionalmente: converge em milissegundos e produz a fronteira eficiente sem erro numérico. É o método mais barato e o mais confiável do conjunto. O problema não está no solver, e sim na estimativa de μ, que alimenta a otimização.

**Força bruta sobre as alocações discretas.** Funcionou perfeitamente para 4 ativos e 12 qubits. Com 4096 vetores, a resposta é exata e instantânea. Foi a referência que permitiu medir o custo da discretização (0,0073).

**Pesos iguais.** Foi a estratégia mais robusta fora da amostra, em todos os testes (Sharpe de 0,56 a 0,62 em 2025, contra valores negativos das alternativas otimizadas). Não exige estimativa de μ, o que a torna menos sensível ao erro de estimação. Esse resultado é consistente com a literatura sobre o "1/N" (DeMiguel et al., 2009).

**Infraestrutura quântica no Qiskit atual.** `StatevectorSampler`, `AerSamplerV2`, `QAOA`, `SamplingVQE` e `n_local` funcionam e reproduzem as saídas esperadas. A reprodução do Hamiltoniano e a varredura de sementes são reprodutíveis quando o ponto inicial é fixado (ver seção 9.4).

**Viabilidade no VQE.** O VQE, com 1 a 3 repetições, aprendeu a respeitar a restrição de soma. A probabilidade de viabilidade chegou a 53%, contra 3,9% de um sorteio. Isso mostra que o ansatz consegue representar estados de soma fixa, mesmo sem concentrar probabilidade no ótimo.

### 9.2 O que não funcionou

**QAOA como amostrador do ótimo (p = 1 a 3, simulação ideal).** P(ótimo) ficou entre 1,2% e 2,5%, abaixo do sorteio (6,25%). O solver "acertou" em 15 de 15 execuções, mas isso se deve à escolha da menor energia entre as amostras, e não a uma distribuição concentrada no ótimo.

*Por que, hipóteses:*
- **Profundidade rasa.** Com p ≤ 3, o circuito tem poucos parâmetros (2p) para explorar uma paisagem com 16 estados. Mais camadas ajudaram pouco (de 1,2% para 2,5%).
- **Paisagem dominada pela penalidade.** Com λ = 1, a matriz Q é dominada pelo termo de penalidade, e a parte de risco quase não influencia a distribuição. Isso reduz a informação útil no sinal.
- **Otimizador.** COBYLA com 300 iterações para 2p parâmetros pode parar em um mínimo local. Não testamos outros otimizadores.
- **Sorteio é um baseline forte aqui.** Com 16 estados, a probabilidade de um sorteio acertar o ótimo é 1/16. Um algoritmo quântico precisa superar isso de forma clara, e não superou.

**VQE como otimizador da alocação.** Com 12 qubits e 24 a 48 parâmetros, o VQE acertou a melhor alocação viável em 2 de 9 execuções, mas com probabilidade de ~0,003% no circuito, abaixo do sorteio (0,024%). Ou seja, o acerto veio de uma amostra de menor energia, e não de um circuito concentrado no ótimo.

*Por que, hipóteses:*
- **Convergência prematura.** O COBYLA parou entre 279 e 540 avaliações, abaixo do limite de 1000, o que indica convergência por tolerância em um mínimo local.
- **Dependência da semente.** Entre sementes, P(ótimo) variou de 0% a 73% na reprodução da DualQ. Com 3 sementes por configuração, a estatística é fraca.
- **Expressividade do ansatz.** RY com entrelaçamento CZ gera estados com soma de pesos variável. Não há garantia de que a região do ótimo seja acessível com poucas repetições.
- **Possíveis platôs estéreis.** Em circuitos rasos com muitos qubits, gradientes podem ser pequenos (McClean et al., 2018). Com 12 qubits e otimizador sem gradiente, o efeito não foi isolado, mas é uma explicação plausível para a falta de convergência.

**Reprodução das probabilidades da DualQ.** A solução exata (valor −0,6152) foi reproduzida. As probabilidades de ótimo de 63% (QAOA) e 49% (VQE) não foram. A média de 8 sementes ficou em 4,5% e 15%, e o QAOA não chegou a 63% em nenhuma semente.

*Por que, hipóteses:*
- **Ponto inicial e otimizador não descritos na referência.** O notebook da DualQ não fixa o ponto inicial do VQE, e a versão `qiskit.aqua` usa um padrão que não conseguimos recuperar.
- **Fonte de dados.** Não temos as saídas originais do yfinance da referência. O valor exato idêntico sugere que os dados coincidem, mas isso não é prova.
- **Uma única execução na referência.** Pelos nossos testes, a probabilidade de ótimo depende muito da semente. Um número isolado não representa o comportamento típico do método.

**Carteira otimizada fora da amostra (todos os métodos).** Em 2025, nenhuma alternativa otimizada superou pesos iguais. A carteira de máximo Sharpe concentrou 77% em BBAS3 e perdeu.

*Por que, hipóteses:*
- **Erro de estimação.** Com dois anos de dados, μ tem erro de estimação grande, e a otimização amplifica esse erro (Ledoit e Wolf, 2004; DeMiguel et al., 2009).
- **Retornos não normais.** A curtose em excesso de BBAS3 é 9,34, o que enfraquece as premissas de média-variância.

### 9.3 Resumo comparativo

| Método | Resultado | Por quê, em uma frase |
|---|---|---|
| Formulação QUBO / Ising | Funcionou | Conversão exata e verificada |
| Markowitz contínuo | Funcionou computacionalmente, falhou fora da amostra | Erro de estimação de μ |
| Força bruta discreta | Funcionou | Exata, mas só viável para poucos ativos |
| Pesos iguais | Funcionou melhor fora da amostra | Não depende de μ estimado |
| QAOA (p ≤ 3) | Não funcionou | Probabilidade abaixo do sorteio; poucas camadas e penalidade dominante |
| VQE (1 a 3 reps) | Parcial | Aprende viabilidade, não concentra no ótimo; convergência prematura |
| Reprodução DualQ | Parcial | Valor exato reproduzido; probabilidades altas não reproduzidas |

### 9.4 O que eu faria diferente

1. **Testar outros otimizadores** (SPSA, por exemplo, ou L-BFGS com gradiente por parameter shift) antes de concluir que o VQE não funciona.
2. **Rodar muitas sementes** (no mínimo 30) e reportar média, mediana e intervalo, em vez de execuções isoladas.
3. **Aumentar p e o número de repetições** de forma sistemática, para mapear a curva de desempenho.
4. **Calibrar λ** por varredura antes de comparar algoritmos, porque a escala da penalidade muda o problema.
5. **Usar mais de um período de teste** e estimativas de μ com encolhimento (Ledoit e Wolf, 2004) antes de julgar a otimização.
6. **Conferir a série SGS 12** do Banco Central para a taxa livre de risco, em vez de usar a aproximação 0,13.

---

## 10. Glossário

- **Ativo:** título negociado em bolsa (aqui, ação da B3).
- **Retorno:** variação percentual do preço em um período. Aqui, anual, calculado como média diária × 252.
- **Volatilidade:** desvio padrão dos retornos. Mede o risco de flutuação do preço.
- **Covariância:** medida de como dois ativos variam juntos. Positiva, eles se movem na mesma direção; negativa, em direções opostas.
- **Correlação:** covariância normalizada, entre −1 e +1.
- **Carteira (portfólio):** combinação de ativos com pesos definidos, que somam 100%.
- **Fronteira eficiente:** conjunto de carteiras que oferecem o maior retorno para cada nível de risco.
- **Sharpe:** retorno em excesso da taxa livre de risco, dividido pela volatilidade. Mede retorno por unidade de risco.
- **Taxa livre de risco (rf):** retorno de um investimento sem risco. Aqui, 0,13, aproximação do CDI.
- **Curtose em excesso:** medida de caudas. Zero em uma normal; valores altos indicam eventos extremos mais frequentes.
- **Erro de estimação:** erro nas estimativas de μ e Σ a partir de dados finitos. Leva a carteiras que parecem ótimas no treino e falham fora da amostra.
- **Out-of-sample (fora da amostra):** avaliação em dados que não foram usados para escolher a carteira.
- **QUBO (Quadratic Unconstrained Binary Optimization):** problema de minimizar uma forma quadrática sobre variáveis binárias, sem restrições.
- **Penalidade (λ):** termo somado à função de custo para punir violações de restrição.
- **Viabilidade:** propriedade de satisfazer a restrição (aqui, soma dos pesos igual a 100%).
- **Ising / Hamiltoniano:** forma equivalente ao QUBO, com variáveis de spin ±1, expressa como operador de Pauli. É a entrada do QAOA e do VQE.
- **Qubit:** unidade básica de informação quântica. Aqui, cada qubit representa um bit de decisão.
- **Bitstring:** sequência de 0 e 1 obtida ao medir o circuito. Cada uma representa uma carteira.
- **Statevector (vetor de estado):** representação completa do estado quântico, usada em simulação ideal.
- **Shot:** uma medição do circuito. P(ótimo) é estimado a partir de milhares de shots.
- **Ansatz:** circuito parametrizado usado pelo VQE.
- **Camada / repetições (reps):** repetição de um bloco de portas no circuito. Mais repetições dão mais parâmetros e mais expressividade.
- **Portas RY, CZ, RZZ, RX:** portas quânticas básicas. RY e RX são rotações; CZ e RZZ criam emaranhamento entre dois qubits.
- **Emaranhamento:** correlação quântica entre qubits, que o VQE e o QAOA usam para explorar combinações.
- **QAOA (Quantum Approximate Optimization Algorithm):** algoritmo variacional que alterna uma camada de custo e uma de mistura, com parâmetros γ e β.
- **VQE (Variational Quantum Eigensolver):** algoritmo variacional que minimiza a energia média de um Hamiltoniano sobre um ansatz parametrizado.
- **COBYLA:** otimizador clássico sem gradiente, usado para ajustar os parâmetros do QAOA e do VQE.
- **Semente (seed):** valor que fixa a sequência de números aleatórios, para tornar a execução reproduzível.
- **Sorteio uniforme:** escolha aleatória com probabilidade igual para cada vetor. É o baseline mínimo de qualquer método.
- **Discretização:** aproximação de pesos contínuos por passos fixos (aqui, 1/8).
- **Platô estéril (barren plateau):** região em que o gradiente de um circuito variacional é tão pequeno que o otimizador não consegue progredir.

---

## 11. Referências

**Teoria financeira**

- Markowitz, H. (1952). Portfolio Selection. *The Journal of Finance*, 7(1), 77–91. https://doi.org/10.2307/2975974
- Sharpe, W. F. (1994). The Sharpe Ratio. *The Journal of Portfolio Management*, 21(1), 49–58.
- Ledoit, O., & Wolf, M. (2004). Honey, I Shrunk the Sample Covariance Matrix. *The Journal of Portfolio Management*, 30(4), 110–119.
- DeMiguel, V., Garlappi, L., & Uppal, R. (2009). Optimal Versus Naive Diversification: How Inefficient Is the 1/N Portfolio Strategy? *The Review of Financial Studies*, 22(5), 1915–1953. https://doi.org/10.1093/rfs/hhm075

**Formulação QUBO e Ising**

- Glover, F., Kochenberger, G., & Du, Y. (2018). A Tutorial on Formulating and Using QUBO Models. arXiv:1811.11538.
- Lucas, A. (2014). Ising formulations of many NP problems. *Frontiers in Physics*, 2, 5. https://doi.org/10.3389/fphy.2014.00005

**Algoritmos quânticos**

- Farhi, E., Goldstone, J., & Gutmann, S. (2014). A Quantum Approximate Optimization Algorithm. arXiv:1411.4028.
- Peruzzo, A., et al. (2014). A variational eigenvalue solver on a photonic quantum processor. *Nature Communications*, 5, 4213. https://doi.org/10.1038/ncomms5213
- Kandala, A., et al. (2017). Hardware-efficient variational quantum eigensolver for small molecules and quantum magnets. *Nature*, 549, 242–246. https://doi.org/10.1038/nature23879
- Cerezo, M., et al. (2021). Variational quantum algorithms. *Nature Reviews Physics*, 3, 625–644. https://doi.org/10.1038/s42254-021-00348-9
- McClean, J. R., Boixo, S., Smelyanskiy, V. N., Babbush, R., & Neven, H. (2018). Barren plateaus in quantum neural network training landscapes. *Nature Communications*, 9, 4812. https://doi.org/10.1038/s41467-018-07090-4

**Otimizador**

- Powell, M. J. D. (1994). A direct search optimization method that models the objective and constraint functions by linear interpolations. In *Advances in Optimization and Numerical Analysis* (pp. 51–67). Kluwer Academic.

**Referência analisada**

- Quantum_Finance_DualQ.ipynb (askery, GitHub). Notebook de apoio ao artigo publicado na *Revista Brasileira de Ensino de Física* (RBEF). https://doi.org/10.1590/1806-9126-RBEF-2022-0099 — https://github.com/askery/computacao-quantica-aplicada-ao-mercado-financeiro

**Software e dados**

- Qiskit contributors. Qiskit (versão 2.6.2), Qiskit Algorithms (0.4.0), Qiskit Optimization (0.7.0) e Qiskit Aer (0.18.2). https://qiskit.org
- Aroussi, R. yfinance: Yahoo! Finance market data downloader. https://github.com/ranaroussi/yfinance
- Banco Central do Brasil. Série SGS 12 (CDI diário). https://www3.bcb.gov.br/sgspub
