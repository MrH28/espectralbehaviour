"""Funções do pipeline espectral: leitura, pré-processamento e métricas.

Os valores-padrão dos parâmetros são lidos de config.py **no momento da chamada**:
se você mudar cfg.WL_MIN no notebook, a próxima chamada já usa o novo valor.
"""

import numpy as np
from scipy.signal import savgol_filter

import config as cfg

TRATAMENTOS_VALIDOS = ("abs", "sg", "d1", "snv")


# --- Leitura -----------------------------------------------------------------

def identificar_colunas(df, prefixo=""):
    """Separa as colunas espectrais (nome = comprimento de onda) das de referência.

    Retorna (cols_esp, cols_ref).
    """
    def eh_banda(c):
        nome = str(c)
        if prefixo and not nome.startswith(prefixo):
            return False
        banda = nome[len(prefixo):]
        try:
            float(banda)
        except ValueError:
            return False
        return True

    cols_esp = [c for c in df.columns if eh_banda(c)]
    cols_ref = [c for c in df.columns if c not in cols_esp]
    return cols_esp, cols_ref


def comprimentos_onda(cols_esp, prefixo=""):
    """Converte os nomes das colunas espectrais em comprimentos de onda (nm).

    Exige ordem crescente: se as colunas estiverem fora de ordem, o erro aparece
    aqui, e não silenciosamente nos gráficos e nos filtros.
    """
    if not cols_esp:
        raise ValueError("Nenhuma coluna espectral foi encontrada.")
    wl = np.array([float(str(c)[len(prefixo):]) for c in cols_esp])
    if np.any(np.diff(wl) <= 0):
        raise ValueError("As colunas espectrais precisam estar em ordem crescente de comprimento de onda.")
    return wl


# --- Pré-processamento ---------------------------------------------------------

def corta(X, wl, wl_min=None, wl_max=None):
    """Mantém as bandas entre wl_min e wl_max (inclusive). Retorna (wl_cortado, X_cortado)."""
    wl_min = cfg.WL_MIN if wl_min is None else wl_min
    wl_max = cfg.WL_MAX if wl_max is None else wl_max
    X = np.asarray(X, dtype=float)
    wl = np.asarray(wl, dtype=float)
    if X.ndim != 2 or X.shape[1] != len(wl):
        raise ValueError("X deve ter uma coluna para cada comprimento de onda.")
    mask = (wl >= wl_min) & (wl <= wl_max)
    return wl[mask], np.asarray(X, dtype=float)[:, mask]


def snv(A):
    """Standard Normal Variate: centra e escala cada espectro (linha) pela própria média e desvio."""
    A = np.asarray(A, dtype=float)
    dp = A.std(axis=1, keepdims=True)
    if np.any(dp <= np.finfo(float).eps):
        raise ValueError("Há espectros constantes (desvio-padrão zero): o SNV não pode ser aplicado a eles.")
    return (A - A.mean(axis=1, keepdims=True)) / dp


def preprocessa(X, wl, tratamento="snv", wl_min=None, wl_max=None, janela=None, grau=None):
    """Aplica a sequência de pré-processamento do projeto. Retorna (wl_cortado, X_tratado).

    tratamento:
      'abs' -> corte + absorbância, log10(1/R)
      'sg'  -> 'abs' + suavização de Savitzky-Golay
      'd1'  -> 'abs' + 1ª derivada de Savitzky-Golay
      'snv' -> 'sg' + SNV
    """
    if tratamento not in TRATAMENTOS_VALIDOS:
        raise ValueError(f"tratamento deve ser um de {TRATAMENTOS_VALIDOS}, não {tratamento!r}")
    janela = cfg.SG_JANELA if janela is None else janela
    grau = cfg.SG_GRAU if grau is None else grau

    wl_c, Xc = corta(X, wl, wl_min, wl_max)
    A = np.log10(1 / np.clip(Xc, 1e-6, None))
    if tratamento == "abs":
        return wl_c, A
    if tratamento == "d1":
        return wl_c, savgol_filter(A, janela, grau, deriv=1, axis=1)
    A_sg = savgol_filter(A, janela, grau, deriv=0, axis=1)
    return wl_c, (A_sg if tratamento == "sg" else snv(A_sg))


def reamostra(X, wl_de, wl_para):
    """Interpola cada espectro da grade wl_de para a grade wl_para (ex.: outro sensor)."""
    X = np.atleast_2d(np.asarray(X, dtype=float))
    wl_de = np.asarray(wl_de, dtype=float)
    wl_para = np.asarray(wl_para, dtype=float)
    if X.shape[1] != len(wl_de):
        raise ValueError("X deve ter uma coluna para cada comprimento de onda de origem.")
    if len(wl_de) < 2 or np.any(np.diff(wl_de) <= 0):
        raise ValueError("A grade de origem deve ter pelo menos dois comprimentos crescentes.")
    if wl_para.min() < wl_de.min() or wl_para.max() > wl_de.max():
        raise ValueError("A grade de destino deve estar contida na grade de origem.")
    return np.vstack([np.interp(wl_para, wl_de, linha) for linha in X])


# --- Métricas --------------------------------------------------------------------

def avalia(y_obs, y_pred):
    """R², RMSE, RPD, RPIQ e viés de um conjunto de predições."""
    y_obs = np.asarray(y_obs, dtype=float).ravel()
    y_pred = np.asarray(y_pred, dtype=float).ravel()
    rmse = float(np.sqrt(np.mean((y_obs - y_pred) ** 2)))
    q75, q25 = np.percentile(y_obs, [75, 25])
    ss_tot = np.sum((y_obs - y_obs.mean()) ** 2)
    r2 = np.nan if ss_tot == 0 else 1 - np.sum((y_obs - y_pred) ** 2) / ss_tot
    return {
        "R2": float(r2),
        "RMSE": rmse,
        "RPD": float(y_obs.std() / rmse),
        "RPIQ": float((q75 - q25) / rmse),
        "Viés": float(np.mean(y_pred - y_obs)),
    }


# --- T², Q e VIP ---------------------------------------------------------------------

def t2_q(pca, X):
    """T² de Hotelling e resíduo Q de cada amostra em relação a um PCA já ajustado."""
    X = np.asarray(X, dtype=float)
    sc = pca.transform(X)
    t2 = ((sc ** 2) / pca.explained_variance_).sum(axis=1)
    q = ((X - pca.inverse_transform(sc)) ** 2).sum(axis=1)
    return t2, q


def vip(pls):
    """Variable Importance in Projection de um PLSRegression ajustado (VIP > 1 = banda relevante)."""
    t, w, q = pls.x_scores_, pls.x_weights_, pls.y_loadings_
    p = w.shape[0]
    ss = (q ** 2).sum(axis=0) * (t ** 2).sum(axis=0)
    wn = (w / np.linalg.norm(w, axis=0)) ** 2
    return np.sqrt(p * (wn @ ss) / ss.sum())


# --- Figuras --------------------------------------------------------------------

def salva_figura(fig, nome):
    """Salva a figura em resultados/figuras/ (PNG, 150 dpi) e devolve o caminho."""
    cfg.PASTA_FIG.mkdir(parents=True, exist_ok=True)
    caminho = cfg.PASTA_FIG / nome
    fig.savefig(caminho, dpi=150, bbox_inches="tight")
    return caminho
