"""Gera o site e publica a pasta site/ no Netlify (cria o site na 1ª vez, atualiza nas seguintes).

Uso (a partir da pasta do projeto):
    .venv\\Scripts\\python.exe gerar_site\\publicar_netlify.py
    .venv\\Scripts\\python.exe gerar_site\\publicar_netlify.py --nome meu-site   # nome do endereço
    .venv\\Scripts\\python.exe gerar_site\\publicar_netlify.py --sem-gerar        # só publica

Precisa da variável de ambiente NETLIFY_AUTH_TOKEN (token pessoal do Netlify:
app.netlify.com > User settings > Applications > Personal access tokens).
O id do site fica salvo em gerar_site/netlify_site.json para as próximas publicações.
"""
import argparse, io, json, os, subprocess, sys, time, urllib.error, urllib.request, zipfile
from pathlib import Path

API = "https://api.netlify.com/api/v1"
AQUI = Path(__file__).resolve().parent
ROOT = AQUI.parent
SITE = ROOT / "site"
ESTADO = AQUI / "netlify_site.json"


def token():
    t = os.environ.get("NETLIFY_AUTH_TOKEN")
    if not t and os.name == "nt":  # variável definida com setx ainda não visível neste terminal
        try:
            import winreg
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Environment") as k:
                t = winreg.QueryValueEx(k, "NETLIFY_AUTH_TOKEN")[0]
        except OSError:
            pass
    if not t:
        sys.exit("Defina NETLIFY_AUTH_TOKEN. Crie o token em "
                 "https://app.netlify.com/user/applications#personal-access-tokens e rode:\n"
                 '  setx NETLIFY_AUTH_TOKEN "seu-token"')
    return t


def req(metodo, caminho, tk, corpo=None, tipo="application/json"):
    if isinstance(corpo, dict):
        corpo = json.dumps(corpo).encode()
    r = urllib.request.Request(API + caminho, data=corpo, method=metodo,
                               headers={"Authorization": f"Bearer {tk}", "Content-Type": tipo,
                                        "User-Agent": "publicar-site-script"})
    try:
        with urllib.request.urlopen(r, timeout=300) as resp:
            return json.loads(resp.read() or b"{}")
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"{metodo} {caminho}: HTTP {e.code} {e.read().decode(errors='replace')[:300]}")


def zipar(pasta):
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        for f in sorted(pasta.rglob("*")):
            if f.is_file():
                z.write(f, f.relative_to(pasta).as_posix())
    return buf.getvalue()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--nome", default="pipeline-espectral-saturin-fhl",
                    help="subdomínio desejado em .netlify.app (só na criação)")
    ap.add_argument("--sem-gerar", action="store_true", help="não regenerar o site antes")
    a = ap.parse_args()
    tk = token()

    if not a.sem_gerar:
        print("Gerando o site...")
        subprocess.run([sys.executable, str(AQUI / "build_site.py"), str(ROOT)], check=True)

    if ESTADO.exists():
        site_id = json.loads(ESTADO.read_text())["site_id"]
        print(f"Atualizando o site existente {site_id}")
    else:
        try:
            s = req("POST", "/sites", tk, {"name": a.nome})
        except RuntimeError as e:
            if "422" not in str(e):
                raise
            print(f"O nome '{a.nome}' já está em uso; criando com nome automático.")
            s = req("POST", "/sites", tk, {})
        site_id = s["id"]
        ESTADO.write_text(json.dumps({"site_id": site_id, "nome": s["name"]}, indent=2))
        print(f"Site criado: {s['name']}")

    dados = zipar(SITE)
    print(f"Enviando {len(dados) // 1024} KB...")
    d = req("POST", f"/sites/{site_id}/deploys", tk, dados, "application/zip")
    for _ in range(90):
        if d.get("state") in ("ready", "error"):
            break
        time.sleep(2)
        d = req("GET", f"/deploys/{d['id']}", tk)
    if d.get("state") != "ready":
        sys.exit(f"Publicação não concluída (estado: {d.get('state')}): {d.get('error_message', '')}")
    s = req("GET", f"/sites/{site_id}", tk)
    print("\nPublicado em:", s.get("ssl_url") or s.get("url"))


if __name__ == "__main__":
    main()
