"""Pré-render do Quarto: gera a tabela de métricas e a página de código a partir dos arquivos atuais."""
import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# Tabela de métricas (incluída em index.qmd e resultados.qmd)
with open(ROOT / "resultados" / "metricas.csv", encoding="utf-8") as fh:
    met = list(csv.DictReader(fh))
linhas = ["| Modelo | Conjunto | R² | RMSE (g/kg) | RPD | RPIQ | Viés |",
          "|:--|:--|--:|--:|--:|--:|--:|"]
for r in met:
    linhas.append(f"| {r['Modelo']} | {r['Conjunto']} | {float(r['R2']):.3f} | {float(r['RMSE']):.1f} | "
                  f"{float(r['RPD']):.2f} | {float(r['RPIQ']):.2f} | {float(r['Viés']):.2f} |")
(ROOT / "_metricas.md").write_text("\n".join(linhas) + "\n", encoding="utf-8")

# Página de código
partes = ["---", 'title: "Código-fonte"',
          'description: "Módulos Python importados pelos notebooks."', "---", ""]
for nome, desc in [("config.py", "Caminhos e parâmetros do dataset e de todas as etapas."),
                   ("utils.py", "Bandas, pré-processamento, métricas, T², Q, VIP e reamostragem."),
                   ("gerar_dados_sinteticos.py", "Gera um banco sintético no formato da BSSL para praticar.")]:
    src = (ROOT / nome).read_text(encoding="utf-8").rstrip()
    partes += [f"## `{nome}`", "", f"{desc} [Baixar]({nome}){{download=\"{nome}\"}}", "",
               f'```{{.python filename="{nome}"}}', src, "```", ""]
(ROOT / "codigo.qmd").write_text("\n".join(partes), encoding="utf-8")
