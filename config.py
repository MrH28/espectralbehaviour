"""Configuração do pipeline espectral Saturin: caminhos e parâmetros das etapas.

Todos os notebooks importam este arquivo (`import config as cfg`). Para usar outro
banco ou mudar uma decisão metodológica, altere aqui e rode os notebooks de novo.
Os caminhos são relativos à pasta do projeto e os CSVs são lidos em latin1.
"""

from pathlib import Path

# --- Arquivos ---------------------------------------------------------------
ARQUIVO = Path("dados/raw_nir_data_Saturin.csv")
ARQUIVO_MIR = Path("dados/raw_mir_data_Saturin.csv")
ARQUIVO_NOVAS = None                                # não há amostras sem análise na pasta dados
ENCODING = "latin1"
MAX_AMOSTRAS = 5000                                # 0 = usar todas as amostras
PASTA = Path("resultados")                          # saídas de cada notebook
PASTA_FIG = PASTA / "figuras"

# --- Colunas ----------------------------------------------------------------
COL_ID = "ID_Unico"
COL_ALVO = "Clay_gkg"
PREFIXO = ""                                      # ex.: "X" para bandas X350, X351, ...

# --- Reprodutibilidade ------------------------------------------------------------
SEED = 42

# --- Pré-processamento (notebook 02) -----------------------------------------
WL_MIN, WL_MAX = 450, 2450     # corte das bordas ruidosas (nm)
SG_JANELA = 11                 # janela do Savitzky-Golay (nº ímpar de bandas)
SG_GRAU = 2                    # grau do polinômio do Savitzky-Golay

# --- Outliers (notebook 02) ----------------------------------------------------
Z_OUTLIER = 3                  # limite do z-score do espectro médio
N_PCS_OUTLIER = 5              # PCs usados no T² e no Q
PERC_OUTLIER = 99              # percentil que define os limites de T² e Q

# --- PCA e clusterização (notebook 03) ------------------------------------------
N_PCS_EXPLORA = 10             # PCs da análise exploratória
N_PCS_CLUSTER = 5              # PCs usados no k-means
K_MAX = 10                     # maior k testado no cotovelo e na silhueta
K = 3                          # número de grupos escolhido

# --- Modelagem (notebook 04) --------------------------------------------------
TEST_SIZE = 0.3                # fração para validação (divisão estratificada por grupo)
CV_FOLDS = 10                  # partições da validação cruzada
MAX_LV = 20                    # maior nº de variáveis latentes testado no PLSR
TRATAMENTOS = ("sg", "d1", "snv")
TRATAMENTO_FIXO = None         # None = escolhe pelo menor RMSECV; ou 'sg', 'd1', 'snv'

BUSCA_RF = True                # busca aleatória de hiperparâmetros do Random Forest
N_ITER_BUSCA = 15              # combinações testadas na busca
N_ARVORES = 300                # árvores do Random Forest
N_PCS_RF = 20                  # PCs de entrada do Random Forest quando BUSCA_RF = False

# --- Domínio de aplicação (notebooks 04 e 05) ------------------------------------
N_PCS_DOMINIO = 5              # PCs do PCA do domínio
PERC_DOMINIO = 99              # percentil da calibração que define os limites de T² e Q
