"""Estudo complementar: mais sementes e otimizador SPSA para QAOA (configuração do notebook 03)
e VQE (configuração do notebook 04). Não altera os notebooks.

Saídas em resultados/:
  qaoa_execucoes.csv, vqe_execucoes.csv   uma linha por (configuração, otimizador, semente)
  resumo_estudo.csv                       média, mediana, desvio e IC95% por configuração
"""
import os
import warnings
from itertools import product
from concurrent.futures import ProcessPoolExecutor

import numpy as np
import pandas as pd
from scipy import stats

warnings.filterwarnings('ignore')

RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
CSV = os.path.join(RAIZ, 'data', 'precos_b3.csv')
SAIDA = os.path.join(RAIZ, 'resultados')
SEMENTES = list(range(30))
WORKERS = 8

# Orçamento de cada otimizador (iterações do SPSA; COBYLA usa maxiter direto).
# SPSA usa 2 avaliações por iteração, mais a calibração inicial.
# 'SPSA-grande' tem 4x o orçamento de 'SPSA' e testa se o limite era o gargalo.
ORCAMENTO = {
    'QAOA': {'COBYLA': 300, 'SPSA': 150, 'SPSA-grande': 600},
    'VQE': {'COBYLA': 1000, 'SPSA': 500, 'SPSA-grande': 2000},
}
OTIMIZADORES = ['COBYLA', 'SPSA', 'SPSA-grande']


def otimizador(nome, problema):
    from qiskit_algorithms.optimizers import COBYLA, SPSA
    it = ORCAMENTO[problema][nome]
    return COBYLA(maxiter=it) if nome == 'COBYLA' else SPSA(maxiter=it)


def carregar():
    df = pd.read_csv(CSV, header=[0, 1], index_col=0, skiprows=[2], parse_dates=True)
    close = df['Close'].apply(pd.to_numeric, errors='coerce').dropna()
    close.index = pd.to_datetime(close.index)
    ret = close.loc['2023-01-01':'2024-12-31'].pct_change().dropna()
    mu = (ret.mean() * 252).values
    Sigma = (ret.cov() * 252).values
    return list(close.columns), mu, Sigma


# ---------------- QAOA (notebook 03: 4 ativos, B = 2, lam = 1, 4096 shots) ----------------
def qaoa_problema(ativos, mu, Sigma, lam=1.0, B=2, q=0.5):
    n = len(ativos)
    ones = np.ones(n)
    Q = q * Sigma + lam * np.outer(ones, ones)
    c = -mu - 2 * lam * B * ones
    d = lam * B ** 2
    return Q, c, d


def otimo_qaoa(Q, c, d, n, B):
    todos = np.array(list(product([0, 1], repeat=n)))
    f = np.einsum('ij,jk,ik->i', todos, Q, todos) + todos @ c + d
    viaveis = todos.sum(axis=1) == B
    k = np.argmin(np.where(viaveis, f, np.inf))
    return todos[k]


def executa_qaoa(args):
    p, otim, semente, nome_opt = args
    from qiskit.primitives import StatevectorSampler
    from qiskit_algorithms.minimum_eigensolvers import QAOA
    from qiskit_algorithms.optimizers import COBYLA, SPSA
    from qiskit_optimization.algorithms import MinimumEigenOptimizer
    ativos, mu, Sigma = carregar()
    Q, c, d = qaoa_problema(ativos, mu, Sigma)
    from qiskit_optimization import QuadraticProgram
    qp = QuadraticProgram('carteira')
    for a in ativos:
        qp.binary_var(name=a)
    qp.minimize(constant=d, linear=c, quadratic=Q)
    x_ot = otimo_qaoa(Q, c, d, len(ativos), 2)

    # O ponto inicial do QAOA usa o gerador algorithm_globals, separado do np.random:
    # sem fixá-lo, cada execução parte de um ponto diferente e os resultados não se repetem.
    from qiskit_algorithms.utils import algorithm_globals
    np.random.seed(semente)
    algorithm_globals.random_seed = semente
    opt = otimizador(nome_opt, 'QAOA')
    sampler = StatevectorSampler(default_shots=4096, seed=semente)
    qaoa = QAOA(sampler=sampler, optimizer=opt, reps=p)
    res = MinimumEigenOptimizer(qaoa).solve(qp)
    p_opt = sum(s.probability for s in res.samples if np.array_equal(s.x, x_ot))
    p_viav = sum(s.probability for s in res.samples if s.x.sum() == 2)
    return {
        'problema': 'QAOA 4 ativos (nb03)', 'otimizador': nome_opt, 'config': f'p={p}',
        'semente': semente, 'acertou_solver': bool(np.array_equal(res.x, x_ot)),
        'P_otimo': p_opt, 'P_viavel': p_viav,
        'avaliacoes': res.min_eigen_solver_result.cost_function_evals,
    }


# ---------------- VQE (notebook 04: 12 qubits, 3 bits por ativo, lam = 10) ----------------
N_ATIVOS, K, SOMA, Q_RISCO, LAM = 4, 3, 8, 0.5, 10.0


def vqe_problema(mu, Sigma):
    n, N = N_ATIVOS, N_ATIVOS * K
    M = np.zeros((n, N))
    for i in range(n):
        for k in range(K):
            M[i, i * K + k] = 2 ** k / 8
    a = M.T @ np.ones(n)
    Q = Q_RISCO * M.T @ Sigma @ M + LAM * np.outer(a, a)
    c = -M.T @ mu - 2 * LAM * a
    d = LAM
    return M, Q, c, d


def unidades(b):
    return (np.asarray(b).reshape(N_ATIVOS, K) * (2 ** np.arange(K))).sum(axis=1).astype(int)


def executa_vqe(args):
    reps, semente, nome_opt = args
    from qiskit.primitives import StatevectorSampler
    from qiskit.circuit.library import n_local
    from qiskit_algorithms.minimum_eigensolvers import SamplingVQE
    from qiskit_algorithms.optimizers import COBYLA, SPSA
    from qiskit_optimization import QuadraticProgram
    from qiskit_optimization.algorithms import MinimumEigenOptimizer
    _, mu, Sigma = carregar()
    M, Q, c, d = vqe_problema(mu, Sigma)
    N = N_ATIVOS * K
    qp = QuadraticProgram('alocacao')
    for j in range(N):
        qp.binary_var(name=f'b{j}')
    qp.minimize(constant=d, linear=c, quadratic=Q)

    estados = np.array(list(product([0, 1], repeat=N)))
    e = np.einsum('ij,jk,ik->i', estados, Q, estados) + estados @ c + d
    viav = np.array([unidades(b).sum() == SOMA for b in estados])
    idx = np.where(viav)[0]
    k_ot = idx[np.argmin(e[idx])]
    optimos = [estados[i] for i in idx if abs(e[i] - e[k_ot]) < 1e-9]

    np.random.seed(semente)
    ansatz = n_local(N, ['ry'], ['cz'], entanglement='full', reps=reps)
    x0 = np.random.default_rng(semente).uniform(-np.pi, np.pi, ansatz.num_parameters)
    opt = otimizador(nome_opt, 'VQE')
    sampler = StatevectorSampler(default_shots=4096, seed=semente)
    vqe = SamplingVQE(sampler=sampler, ansatz=ansatz, optimizer=opt, initial_point=x0)
    res = MinimumEigenOptimizer(vqe).solve(qp)
    p_opt = sum(s.probability for s in res.samples if any(np.array_equal(s.x, o) for o in optimos))
    p_viav = sum(s.probability for s in res.samples if unidades(s.x).sum() == SOMA)
    return {
        'problema': 'VQE 12 qubits (nb04)', 'otimizador': nome_opt, 'config': f'reps={reps}',
        'semente': semente, 'acertou_solver': any(np.array_equal(res.x, o) for o in optimos),
        'P_otimo': p_opt, 'P_viavel': p_viav,
        'avaliacoes': res.min_eigen_solver_result.cost_function_evals,
    }


def uniformes_vqe():
    N = N_ATIVOS * K
    estados = np.array(list(product([0, 1], repeat=N)))
    _, mu, Sigma = carregar()
    M, Q, c, d = vqe_problema(mu, Sigma)
    e = np.einsum('ij,jk,ik->i', estados, Q, estados) + estados @ c + d
    viav = np.array([unidades(b).sum() == SOMA for b in estados])
    idx = np.where(viav)[0]
    k_ot = idx[np.argmin(e[idx])]
    n_opt = sum(1 for i in idx if abs(e[i] - e[k_ot]) < 1e-9)
    return n_opt / len(estados), viav.mean()


def resumir(df, base_opt, base_viav):
    linhas = []
    for (prob, opt, cfg), g in df.groupby(['problema', 'otimizador', 'config'], sort=False):
        n = len(g)
        po = g['P_otimo']
        ic = stats.t.ppf(0.975, n - 1) * po.std(ddof=1) / np.sqrt(n)
        linhas.append({
            'problema': prob, 'otimizador': opt, 'config': cfg, 'sementes': n,
            'acerto_solver': g['acertou_solver'].mean(),
            'P_otimo_media': po.mean(), 'P_otimo_mediana': po.median(), 'P_otimo_dp': po.std(ddof=1),
            'P_otimo_IC95_inf': po.mean() - ic, 'P_otimo_IC95_sup': po.mean() + ic,
            'P_otimo_min': po.min(), 'P_otimo_max': po.max(),
            'frac_acima_sorteio_otimo': (po > base_opt).mean(),
            'P_viavel_media': g['P_viavel'].mean(), 'frac_acima_sorteio_viavel': (g['P_viavel'] > base_viav).mean(),
            'avaliacoes_media': g['avaliacoes'].mean(), 'avaliacoes_max': g['avaliacoes'].max(),
            'sorteio_P_otimo': base_opt, 'sorteio_P_viavel': base_viav,
        })
    return pd.DataFrame(linhas)


def main(etapas=('qaoa', 'vqe')):
    """etapas: 'qaoa', 'vqe' ou ambas. A etapa não executada é lida do CSV já existente em resultados/."""
    os.makedirs(SAIDA, exist_ok=True)
    ativos, mu, Sigma = carregar()
    caminho_q = os.path.join(SAIDA, 'qaoa_execucoes.csv')
    caminho_v = os.path.join(SAIDA, 'vqe_execucoes.csv')

    with ProcessPoolExecutor(max_workers=WORKERS) as ex:
        if 'qaoa' in etapas:
            tarefas_q = [(p, None, s, o) for p in [1, 2, 3] for s in SEMENTES for o in OTIMIZADORES]
            qaoa = pd.DataFrame(list(ex.map(executa_qaoa, tarefas_q, chunksize=4)))
            qaoa.to_csv(caminho_q, index=False)
            print('QAOA concluído', len(qaoa), flush=True)
        else:
            qaoa = pd.read_csv(caminho_q)
        if 'vqe' in etapas:
            tarefas_v = [(r, s, o) for r in [1, 2, 3] for s in SEMENTES for o in OTIMIZADORES]
            vqe = pd.DataFrame(list(ex.map(executa_vqe, tarefas_v, chunksize=2)))
            vqe.to_csv(caminho_v, index=False)
            print('VQE concluído', len(vqe), flush=True)
        else:
            vqe = pd.read_csv(caminho_v)

    # Sorteio uniforme: QAOA (16 vetores, 1 ótimo, 6 viáveis em 16)
    base_q_opt, base_q_viav = 1 / 16, 6 / 16
    base_v_opt, base_v_viav = uniformes_vqe()

    resumo = pd.concat([
        resumir(qaoa, base_q_opt, base_q_viav),
        resumir(vqe, base_v_opt, base_v_viav),
    ], ignore_index=True)
    resumo.to_csv(os.path.join(SAIDA, 'resumo_estudo.csv'), index=False)
    with pd.option_context('display.width', 250, 'display.max_columns', 30):
        print(resumo.round(4).to_string(index=False))


if __name__ == '__main__':
    import sys
    # Sem argumento: roda QAOA e VQE. Com 'qaoa' ou 'vqe': roda só essa etapa e reaproveita a outra do disco.
    main(tuple(sys.argv[1:]) or ('qaoa', 'vqe'))
