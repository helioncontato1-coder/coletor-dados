"""Estrategista de tendências: lê o que os coletores juntaram e escreve o briefing do dia
para o setor de marketing (lido pelo Claude via raw.githubusercontent.com).

Sem GEMINI_API_KEY, gera só a parte de números (sem IA).
Saída: dados/briefings/AAAA-MM-DD.md e dados/briefings/ultimo.md
"""
import collections, csv, datetime, json, os, urllib.error, urllib.request
from comum import DADOS, agora, ler_csv, linhas_config

BASE = "https://generativelanguage.googleapis.com/v1beta"
CHAVE = os.environ.get("GEMINI_API_KEY", "")


def numeros():
    hoje = datetime.date.today()
    corte = (hoje - datetime.timedelta(days=30)).isoformat()
    mud = [m for m in ler_csv(DADOS / "lojas" / "mudancas.csv") if m["quando"][:10] >= (hoje - datetime.timedelta(days=2)).isoformat()]
    novos, tipos, precos = [], collections.Counter(), []
    for host in linhas_config("lojas.txt"):
        for p in ler_csv(DADOS / "lojas" / f"{host}.csv"):
            tipos[(p.get("tipo") or "sem tipo").strip().lower()] += 1
            if p.get("criado_em", "") >= corte:
                novos.append(f"{host} | {p['produto']} | R$/US$ {p['preco_min']} | {p['link']}")
            try:
                precos.append(float(p["preco_min"]))
            except (ValueError, KeyError):
                pass
    linhas = [f"Mudanças nas lojas (últimas 48h): {len(mud)}"]
    linhas += [f"- {m['loja']}: {m['mudanca']} — {m['produto']} ({m['antes']} → {m['agora']})" for m in mud[:40]]
    linhas.append(f"\nProdutos lançados nos últimos 30 dias: {len(novos)}")
    linhas += [f"- {n}" for n in novos[:60]]
    linhas.append("\nTipos de produto mais comuns nas lojas: " + ", ".join(f"{t} ({n})" for t, n in tipos.most_common(15)))
    return "\n".join(linhas)


def gemini(texto):
    lista = json.load(urllib.request.urlopen(urllib.request.Request(
        f"{BASE}/models?pageSize=200", headers={"x-goog-api-key": CHAVE}), timeout=60))["models"]
    nomes = sorted(m["name"] for m in lista if "generateContent" in m.get("supportedGenerationMethods", [])
                   and "flash" in m["name"] and not any(x in m["name"] for x in ("lite", "image", "tts", "live", "preview", "omni")))
    pedido = ("Você é o estrategista de tendências de uma loja brasileira de achados pet e casa (Helion, dropshipping, "
              "compra por emoção, tráfego no Instagram). Com os DADOS abaixo (coletados hoje de lojas concorrentes), escreva "
              "um briefing curto em português para o diretor de marketing, com: 1) 3 a 5 tendências que os dados mostram "
              "(cite o produto/loja); 2) 3 ângulos de conteúdo para Instagram que aproveitem essas tendências; 3) produtos "
              "que valem pesquisar fornecedor no Brasil; 4) alertas (preço caindo, item esgotando, lançamento). "
              "Use só o que está nos dados; não invente números.\n\nDADOS:\n" + texto)
    corpo = json.dumps({"contents": [{"parts": [{"text": pedido}]}]}).encode()
    preferidos = [n for n in nomes if n.endswith("gemini-3.5-flash")] + [n for n in reversed(nomes) if not n.endswith("gemini-3.5-flash")]
    for nome in preferidos[:4]:
        try:
            req = urllib.request.Request(f"{BASE}/{nome}:generateContent", data=corpo,
                                         headers={"Content-Type": "application/json", "x-goog-api-key": CHAVE})
            r = json.load(urllib.request.urlopen(req, timeout=300))
            return nome, r["candidates"][0]["content"]["parts"][0]["text"]
        except Exception as e:  # noqa: BLE001
            print("Falhou", nome, str(e)[:200])
    return None, None


def main():
    dados = numeros()
    try:
        modelo, analise = (gemini(dados) if CHAVE else (None, None))
    except Exception as e:  # noqa: BLE001
        print("IA indisponível:", str(e)[:200])
        modelo, analise = None, None
    data = datetime.date.today().isoformat()
    texto = f"# Briefing de tendências — {data}\n\nGerado em {agora()} (Brasília). Modelo: {modelo or 'sem IA (só números)'}\n\n"
    if analise:
        texto += "## Análise do estrategista\n\n" + analise.strip() + "\n\n"
    texto += "## Números da coleta\n\n" + dados + "\n"
    pasta = DADOS / "briefings"
    pasta.mkdir(parents=True, exist_ok=True)
    (pasta / f"{data}.md").write_text(texto, encoding="utf-8")
    (pasta / "ultimo.md").write_text(texto, encoding="utf-8")
    print(texto[:1500])


if __name__ == "__main__":
    main()
