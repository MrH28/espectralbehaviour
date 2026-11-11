"""Gera o site estático em <projeto>/site a partir dos notebooks, figuras e código."""
import csv, html, json, re, shutil, subprocess, sys
from pathlib import Path

ROOT = Path(sys.argv[1]).resolve()
SITE = ROOT / "site"
PY = ROOT / ".venv" / "Scripts" / "python.exe"

if SITE.exists():
    shutil.rmtree(SITE)
(SITE / "notebooks").mkdir(parents=True)
(SITE / "downloads").mkdir()
shutil.copytree(ROOT / "resultados" / "figuras", SITE / "figuras")

NOTEBOOKS = [
    ("01_leitura_exploratoria", "Leitura e análise exploratória",
     "Leitura do banco, estatística descritiva, limpeza e correlação de cada banda com a argila."),
    ("02_preprocessamento", "Pré-processamento e outliers",
     "Corte das bordas, absorbância, Savitzky-Golay, 1ª derivada, SNV e outliers por z-score, T² e Q."),
    ("03_pca_clusterizacao", "PCA e clusterização",
     "Componentes principais, cotovelo, silhueta e agrupamento k-means."),
    ("04_modelagem", "Modelagem: PLSR e Random Forest",
     "Escolha do tratamento e das variáveis latentes por validação cruzada, Random Forest e domínio de aplicação."),
    ("05_visualizacao_predicao", "Visualização e predição",
     "Observado × predito, resíduos, coeficientes, VIP, importância e predição de amostras novas."),
]

CSS = (Path(__file__).parent / "site.css").read_text(encoding="utf-8")
shutil.copy(Path(__file__).parent / "nb.css", SITE / "notebooks" / "nb.css")
(SITE / "estilo.css").write_text(CSS, encoding="utf-8")


def nav(prefix, active):
    items = [("index.html", "Início"), ("index.html#pipeline", "Pipeline"),
             ("index.html#resultados", "Resultados"), ("index.html#figuras", "Figuras"),
             ("codigo.html", "Código"), ("index.html#arquivos", "Arquivos")]
    links = "".join(
        f'<a href="{prefix}{h}"{" class=active" if t == active else ""}>{t}</a>' for h, t in items)
    return (f'<header class="topo"><div class="wrap topo-in"><a class="marca" href="{prefix}index.html">'
            f'<span class="logo">λ</span> Pipeline espectral Saturin Fhl</a><nav>{links}</nav></div></header>')


def page(title, body, prefix="", active=""):
    return f"""<!doctype html>
<html lang="pt-BR"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(title)}</title>
<link rel="stylesheet" href="{prefix}estilo.css"></head>
<body>{nav(prefix, active)}{body}
<footer class="rodape"><div class="wrap">Pipeline espectral Saturin Fhl · Espectroscopia de solos com Python ·
<a href="https://geocis.github.io/geocis_tutorial/">geocis.github.io/geocis_tutorial</a></div></footer>
<script>
document.querySelectorAll('a.zoom').forEach(a=>a.addEventListener('click',e=>{{
 e.preventDefault();const d=document.getElementById('lb');d.querySelector('img').src=a.href;
 d.querySelector('p').textContent=a.dataset.cap||'';d.showModal();}}));
const lb=document.getElementById('lb'); if(lb) lb.addEventListener('click',()=>lb.close());
</script></body></html>"""


# ---------- notebooks -> HTML ----------
for i, (stem, titulo, _) in enumerate(NOTEBOOKS):
    out = SITE / "notebooks"
    subprocess.run([str(PY), "-m", "nbconvert", "--to", "html", "--template", "lab",
                    "--embed-images", "--output-dir", str(out), str(ROOT / f"{stem}.ipynb")],
                   check=True, capture_output=True)
    f = out / f"{stem}.html"
    txt = f.read_text(encoding="utf-8")
    prev = f'<a href="{NOTEBOOKS[i-1][0]}.html">← {NOTEBOOKS[i-1][1]}</a>' if i else "<span></span>"
    nxt = f'<a href="{NOTEBOOKS[i+1][0]}.html">{NOTEBOOKS[i+1][1]} →</a>' if i < 4 else "<span></span>"
    bar = (f'<link rel="stylesheet" href="nb.css">{nav("../", "Pipeline")}'
           f'<div class="nbbar wrap">{prev}<span class="etapa">Notebook {i+1:02d} de 05 · '
           f'<a href="../downloads/{stem}.ipynb" download>baixar .ipynb</a></span>{nxt}</div>')
    txt = re.sub(r"<body([^>]*)>", lambda m: f"<body{m.group(1)}>{bar}", txt, count=1)
    txt = txt.replace("</body>", f'<div class="nbbar wrap">{prev}<span></span>{nxt}</div></body>', 1)
    txt = re.sub(r"<title>.*?</title>", f"<title>{i+1:02d} · {titulo}</title>", txt, count=1, flags=re.S)
    f.write_text(txt, encoding="utf-8")

# ---------- downloads ----------
for name in ["README.md", "config.py", "utils.py", "gerar_dados_sinteticos.py", "requirements.txt"] + \
        [f"{s}.ipynb" for s, _, _ in NOTEBOOKS]:
    shutil.copy(ROOT / name, SITE / "downloads" / name)
for name in ["metricas.csv", "predicoes_validacao.csv"]:
    shutil.copy(ROOT / "resultados" / name, SITE / "downloads" / name)

# ---------- código ----------
from pygments import highlight
from pygments.formatters import HtmlFormatter
from pygments.lexers import PythonLexer

fmt = HtmlFormatter(cssclass="hl", linenos=False)
blocos = []
for name, desc in [("config.py", "Caminhos e parâmetros do dataset e de todas as etapas."),
                   ("utils.py", "Bandas, pré-processamento, métricas, T², Q, VIP e reamostragem."),
                   ("gerar_dados_sinteticos.py", "Gera um banco sintético no formato da BSSL para praticar.")]:
    src = (ROOT / name).read_text(encoding="utf-8")
    blocos.append(f'<section class="arq" id="{name}"><div class="arq-cab"><h2>{name}</h2>'
                  f'<p>{desc}</p><a class="btn sec" href="downloads/{name}" download>Baixar</a></div>'
                  f'{highlight(src, PythonLexer(), fmt)}</section>')
pyg_css = HtmlFormatter(style="default").get_style_defs(".hl")
pyg_dark = HtmlFormatter(style="monokai").get_style_defs(".hl")
(SITE / "estilo.css").write_text(
    CSS + "\n/* pygments */\n" + pyg_css +
    "\n@media (prefers-color-scheme: dark){\n"
    + pyg_dark.replace(".hl", ':root:not([data-theme="light"]) .hl') + "}\n"
    + pyg_dark.replace(".hl", ':root[data-theme="dark"] .hl')
    + "\n.hl{background:var(--code)!important}\n",
    encoding="utf-8")
toc = " · ".join(f'<a href="#{n}">{n}</a>' for n in ["config.py", "utils.py", "gerar_dados_sinteticos.py"])
(SITE / "codigo.html").write_text(page("Código · Pipeline espectral Saturin Fhl",
    f'<main class="wrap"><h1 class="pg">Código-fonte</h1><p class="lead">Módulos Python importados '
    f'pelos notebooks. {toc}</p>{"".join(blocos)}</main>', active="Código"), encoding="utf-8")

# ---------- index ----------
with open(ROOT / "resultados" / "metricas.csv", encoding="utf-8") as fh:
    met = list(csv.DictReader(fh))
linhas = "".join(
    f"<tr><td>{r['Modelo']}</td><td>{r['Conjunto']}</td><td>{float(r['R2']):.3f}</td>"
    f"<td>{float(r['RMSE']):.1f}</td><td>{float(r['RPD']):.2f}</td><td>{float(r['RPIQ']):.2f}</td>"
    f"<td>{float(r['Viés']):.2f}</td></tr>" for r in met)
val = {r["Modelo"]: r for r in met if r["Conjunto"] == "Validação"}

FIG_CAP = {
    "01_espectros_brutos": "Espectros brutos (350–2500 nm)",
    "01_distribuicao_alvo": "Distribuição da argila (g/kg)",
    "01_correlacao_bandas": "Correlação de cada banda com a argila",
    "02_etapas_preprocessamento": "Etapas do pré-processamento",
    "02_outliers": "Outliers: z-score, T² e Q",
    "03_variancia_pca": "Variância explicada pelos PCs",
    "03_escores_loadings": "Escores e loadings do PCA",
    "03_cotovelo_silhueta": "Cotovelo e silhueta",
    "03_clusters": "Grupos do k-means",
    "04_rmsecv_plsr": "RMSECV do PLSR por tratamento e nº de VLs",
    "05_observado_predito": "Observado × predito (validação)",
    "05_plsr_coef_vip": "Coeficientes e VIP do PLSR",
    "05_rf_importancia": "Importância no Random Forest",
}
figs = "".join(
    f'<figure><a class="zoom" href="figuras/{k}.png" data-cap="{v}"><img loading="lazy" '
    f'src="figuras/{k}.png" alt="{v}"></a><figcaption><b>{k[:2]}</b> {v}</figcaption></figure>'
    for k, v in FIG_CAP.items())

DESTAQUES = {
    "01_leitura_exploratoria": "5000 → 1150 amostras · maior |r| 0,47 em 2206 nm",
    "02_preprocessamento": "2151 → 2001 bandas · 25 outliers removidos",
    "03_pca_clusterizacao": "PC1 63,7% · 5 PCs 95,0% · k = 3",
    "04_modelagem": "787 calibração / 338 validação · tratamento sg, 17 VLs",
    "05_visualizacao_predicao": "Sem amostras novas configuradas",
}
cards = "".join(
    f'<a class="passo" href="notebooks/{s}.html"><span class="num">{i+1:02d}</span>'
    f'<h3>{t}</h3><p>{d}</p><span class="tag">{DESTAQUES[s]}</span></a>'
    for i, (s, t, d) in enumerate(NOTEBOOKS))

dl = [("Notebooks", [(f"{s}.ipynb", t) for s, t, _ in NOTEBOOKS]),
      ("Código e configuração", [("config.py", "Parâmetros"), ("utils.py", "Funções"),
                                 ("gerar_dados_sinteticos.py", "Dados sintéticos"),
                                 ("requirements.txt", "Dependências"), ("README.md", "Leia-me")]),
      ("Resultados", [("metricas.csv", "Métricas dos modelos"),
                      ("predicoes_validacao.csv", "Predições na validação (338 amostras)")])]
dlhtml = "".join(
    f'<div class="dlcol"><h3>{g}</h3><ul>' +
    "".join(f'<li><a href="downloads/{n}" download><code>{n}</code></a><span>{d}</span></li>' for n, d in itens) +
    "</ul></div>" for g, itens in dl)

body = f"""
<section class="hero"><div class="wrap">
 <p class="eyebrow">Espectroscopia de solos com Python</p>
 <h1>Predição de argila a partir de espectros Vis-NIR-SWIR</h1>
 <p class="lead">Pipeline em Python e Jupyter que lê o banco espectral Saturin, trata os espectros,
 explora a variação com PCA e k-means e ajusta modelos PLSR e Random Forest para estimar o teor de
 argila (<code>Clay_gkg</code>), com verificação do domínio de aplicação por T² e Q.</p>
 <div class="acoes"><a class="btn" href="notebooks/01_leitura_exploratoria.html">Começar pelo notebook 01</a>
 <a class="btn sec" href="#resultados">Ver resultados</a></div>
 <div class="kpis">
  <div><b>1125</b><span>amostras modeladas</span></div>
  <div><b>2001</b><span>bandas (450–2450 nm)</span></div>
  <div><b>{float(val['Random Forest']['R2']):.2f}</b><span>R² validação · RF</span></div>
  <div><b>{float(val['PLSR']['R2']):.2f}</b><span>R² validação · PLSR</span></div>
 </div>
</div></section>
<main class="wrap">
<section id="pipeline"><h2>Pipeline</h2>
<p class="sub">Execute os notebooks em ordem. Cada um lê o que o anterior salvou em <code>resultados/</code>.</p>
<div class="passos">{cards}</div></section>

<section id="resultados"><h2>Resultados</h2>
<p class="sub">Alvo: argila (g/kg). Amostra aleatória de 5000 linhas do arquivo NIR (SEED = 42).</p>
<div class="tabwrap"><table><thead><tr><th>Modelo</th><th>Conjunto</th><th>R²</th><th>RMSE (g/kg)</th>
<th>RPD</th><th>RPIQ</th><th>Viés</th></tr></thead><tbody>{linhas}</tbody></table></div>
<div class="nota"><b>Leitura:</b> na validação independente os dois modelos ficam próximos
(R² ≈ 0,49–0,54, RPD ≈ 1,4–1,5). O R² de 0,94 do Random Forest na calibração, contra 0,54 na validação,
indica sobreajuste; o PLSR usou o tratamento Savitzky-Golay com 17 variáveis latentes.</div>
<div class="duo">
 <figure><a class="zoom" href="figuras/05_observado_predito.png" data-cap="Observado × predito (validação)">
 <img src="figuras/05_observado_predito.png" alt="Observado × predito"></a><figcaption>Observado × predito na validação</figcaption></figure>
 <figure><a class="zoom" href="figuras/04_rmsecv_plsr.png" data-cap="RMSECV do PLSR">
 <img src="figuras/04_rmsecv_plsr.png" alt="RMSECV"></a><figcaption>Escolha do tratamento e do nº de VLs</figcaption></figure>
</div></section>

<section id="figuras"><h2>Galeria de figuras</h2>
<p class="sub">Clique para ampliar.</p><div class="galeria">{figs}</div></section>

<section id="uso"><h2>Como executar</h2>
<pre class="cmd">pip install -r requirements.txt
jupyter lab   # abra 01 a 05 e execute todas as células</pre>
<ul class="lista">
<li>Dados: <code>dados/raw_nir_data_Saturin.csv</code> (latin1), identificador <code>ID_Unico</code>; <code>raw_mir_data_Saturin.csv</code> é a fonte MIR alternativa. Os CSVs (~1,4 GB) não estão incluídos neste site.</li>
<li>Para outro banco, ajuste <code>ARQUIVO</code>, <code>COL_ALVO</code> e <code>PREFIXO</code> em <a href="codigo.html#config.py"><code>config.py</code></a> e revise <code>WL_MIN</code>, <code>WL_MAX</code>, <code>SG_JANELA</code> e <code>K</code>.</li>
<li><code>gerar_dados_sinteticos.py</code> cria um banco sintético para praticar; os números obtidos com ele não são resultados científicos.</li>
</ul></section>

<section id="arquivos"><h2>Arquivos</h2><div class="dl">{dlhtml}</div></section>
</main>
<dialog id="lb"><img alt=""><p></p></dialog>"""
(SITE / "index.html").write_text(page("Pipeline espectral Saturin Fhl", body, active="Início"), encoding="utf-8")
(SITE / "codigo.html").write_text(
    (SITE / "codigo.html").read_text(encoding="utf-8"), encoding="utf-8")
print("ok", sum(f.stat().st_size for f in SITE.rglob("*") if f.is_file()) // 1024, "KB")
