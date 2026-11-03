"""Funções comuns dos coletores: baixar com pausa, gravar CSV e registrar status."""
import csv, json, pathlib, time, urllib.request, datetime

RAIZ = pathlib.Path(__file__).resolve().parent.parent
DADOS = RAIZ / "dados"
UA = "Mozilla/5.0 (coletor-dados; pesquisa de mercado)"


def agora():
    return datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=-3))).strftime("%Y-%m-%d %H:%M")


def baixar_json(url, pausa=2.0, timeout=30):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read().decode())
    finally:
        time.sleep(pausa)


def linhas_config(nome):
    p = RAIZ / "config" / nome
    return [l.strip() for l in p.read_text(encoding="utf-8").splitlines() if l.strip() and not l.startswith("#")]


def gravar_csv(caminho, linhas, modo="w"):
    caminho.parent.mkdir(parents=True, exist_ok=True)
    if not linhas:
        return
    novo = modo == "w" or not caminho.exists()
    with caminho.open(modo, newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(linhas[0]))
        if novo:
            w.writeheader()
        w.writerows(linhas)


def ler_csv(caminho):
    if not caminho.exists():
        return []
    with caminho.open(encoding="utf-8") as f:
        return list(csv.DictReader(f))


def registrar_status(coletor, info):
    p = DADOS / "status.json"
    st = json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}
    st[coletor] = {"quando": agora(), **info}
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(st, ensure_ascii=False, indent=1), encoding="utf-8")
