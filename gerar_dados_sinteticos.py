"""Gera um banco sintético no formato da BSSL para praticar sem o banco real.

    python gerar_dados_sinteticos.py

Cria, na pasta dados/:
  bssl.csv           900 amostras: id, argila, mo e 431 bandas (350 a 2500 nm, passo de 5 nm)
  novas_amostras.csv 50 amostras novas (id e bandas), da mesma distribuição, sem análise

Como os espectros foram construídos (para saber o que esperar dos resultados):
  - reflectância crescente com o comprimento de onda, entre ~0,06 e ~0,5;
  - feições de absorção simuladas apenas perto de 1400, 1900 e 2200 nm, mais profundas
    quanto maior a argila (relação praticamente linear em absorbância);
  - espalhamento e matéria orgânica (mo) escurecem o espectro inteiro de forma
    multiplicativa, o que vira um deslocamento constante em absorbância (o SNV remove);
  - ruído baixo, amplificado nas bordas (abaixo de 450 e acima de 2450 nm);
  - 40 amostras sem argila e 8 espectros anômalos de propósito (S0000 a S0007).

Os dados são "bem comportados" de propósito: servem para ver o efeito de cada etapa,
e os números obtidos com eles NÃO são resultados científicos.
"""

from pathlib import Path

import numpy as np
import pandas as pd

import config as cfg

N_AMOSTRAS = 900
N_NOVAS = 50
N_ANOMALOS = 8
N_SEM_ARGILA = 40
WL = np.arange(350, 2501, 5)              # 431 bandas


def _gauss(centro, largura):
    return np.exp(-0.5 * ((WL - centro) / largura) ** 2)


def gerar_espectros(rng, n):
    """Atributos e reflectâncias de n amostras normais."""
    argila = np.clip(rng.beta(1.5, 2.6, n) * 100, 1.0, 99.0)
    mo = rng.gamma(3.3, 6.0, n)

    # forma geral: reflectância que cresce com o comprimento de onda
    base = 0.10 + 0.32 * (1 - np.exp(-(WL - 330) / 650))
    # feições ligadas à argila (OH e água em 1400 e 1900 nm; Al-OH em 2200 nm)
    feicoes = 0.15 * _gauss(1415, 30) + 0.32 * _gauss(1915, 45) + 0.24 * _gauss(2205, 30)
    absorcao = (argila / 100)[:, None] * feicoes[None, :]
    # espalhamento e matéria orgânica: fator multiplicativo no espectro inteiro
    escurecimento = np.exp(-0.013 * mo + rng.normal(0, 0.12, n))
    R = base[None, :] * np.exp(-absorcao) * escurecimento[:, None]

    ruido = np.where((WL < 450) | (WL > 2450), 0.010, 0.0015)
    R = R + rng.normal(0, 1, R.shape) * ruido[None, :]
    # erro do laboratório: a argila "medida" difere um pouco da que gerou o espectro
    argila_medida = np.clip(argila + rng.normal(0, 2.8, n), 0.5, 100)
    return np.clip(R, 0.01, 1.0), argila_medida, mo


def main():
    rng = np.random.default_rng(cfg.SEED)
    R, argila, mo = gerar_espectros(rng, N_AMOSTRAS)

    # espectros anômalos (reflectâncias altas e formas irregulares) nas primeiras linhas
    R[:N_ANOMALOS] = rng.uniform(0.05, 0.9, (N_ANOMALOS, len(WL)))
    # atributo-alvo faltante em 40 amostras normais
    argila = argila.astype(float)
    argila[rng.choice(np.arange(N_ANOMALOS, N_AMOSTRAS), N_SEM_ARGILA, replace=False)] = np.nan

    df = pd.DataFrame(R.round(5), columns=[str(w) for w in WL])
    df.insert(0, "mo", mo.round(2))
    df.insert(0, "argila", np.round(argila, 2))
    df.insert(0, "id", [f"S{i:04d}" for i in range(N_AMOSTRAS)])

    Rn, _, _ = gerar_espectros(np.random.default_rng(cfg.SEED + 1), N_NOVAS)
    novas = pd.DataFrame(Rn.round(5), columns=[str(w) for w in WL])
    novas.insert(0, "id", [f"N{i:04d}" for i in range(N_NOVAS)])

    Path(cfg.ARQUIVO).parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(cfg.ARQUIVO, index=False)
    novas.to_csv(cfg.ARQUIVO_NOVAS, index=False)
    print(f"{cfg.ARQUIVO}: {df.shape[0]} amostras, {len(WL)} bandas ({WL[0]}-{WL[-1]} nm), "
          f"{df['argila'].isna().sum()} sem {cfg.COL_ALVO}, {N_ANOMALOS} espectros anômalos")
    print(f"{cfg.ARQUIVO_NOVAS}: {novas.shape[0]} amostras novas")


if __name__ == "__main__":
    main()
