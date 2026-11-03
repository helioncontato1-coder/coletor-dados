"""Catálogo público de lojas Shopify (/products.json) e registro do que mudou.

Saída:
  dados/lojas/<dominio>.csv   foto atual do catálogo
  dados/lojas/mudancas.csv    histórico: produto novo, removido, preço mudou, esgotou/voltou
"""
from comum import DADOS, agora, baixar_json, gravar_csv, ler_csv, linhas_config, registrar_status

PASTA = DADOS / "lojas"


def catalogo(host):
    itens = []
    for n in range(1, 21):
        prods = baixar_json(f"https://{host}/products.json?limit=250&page={n}").get("products", [])
        if not prods:
            break
        for p in prods:
            vs = p.get("variants", [])
            precos = [float(v["price"]) for v in vs if v.get("price")]
            des = [float(v["compare_at_price"]) for v in vs if v.get("compare_at_price")]
            tags = p.get("tags", [])
            itens.append({
                "id": str(p.get("id")), "produto": p.get("title"), "tipo": p.get("product_type"),
                "preco_min": min(precos) if precos else "", "preco_max": max(precos) if precos else "",
                "preco_de_max": max(des) if des else "", "variantes": len(vs),
                "disponivel": str(any(v.get("available") for v in vs)),
                "criado_em": (p.get("created_at") or "")[:10],
                "tags": (", ".join(tags) if isinstance(tags, list) else str(tags))[:200],
                "link": f"https://{host}/products/{p.get('handle')}",
            })
    return itens


def comparar(host, antes, depois):
    quando, mud = agora(), []
    a = {r["id"]: r for r in antes}
    d = {r["id"]: r for r in depois}
    for i, r in d.items():
        if i not in a:
            mud.append(("produto novo", r, "", r["preco_min"]))
        else:
            o = a[i]
            if str(o["preco_min"]) != str(r["preco_min"]):
                mud.append(("preço mudou", r, o["preco_min"], r["preco_min"]))
            if o["disponivel"] != r["disponivel"]:
                mud.append(("esgotou" if r["disponivel"] == "False" else "voltou ao estoque", r, o["disponivel"], r["disponivel"]))
    for i, o in a.items():
        if i not in d:
            mud.append(("produto removido", o, o["preco_min"], ""))
    return [{"quando": quando, "loja": host, "mudanca": t, "produto": r["produto"],
             "antes": an, "agora": ag, "link": r["link"]} for t, r, an, ag in mud]


def main():
    resumo = {}
    for host in linhas_config("lojas.txt"):
        arq = PASTA / f"{host}.csv"
        try:
            novo = catalogo(host)
        except Exception as e:  # noqa: BLE001
            resumo[host] = f"erro: {str(e)[:80]}"
            print(host, "erro", e)
            continue
        antes = ler_csv(arq)
        mud = comparar(host, antes, novo) if antes else []
        gravar_csv(arq, novo)
        gravar_csv(PASTA / "mudancas.csv", mud, modo="a")
        resumo[host] = f"{len(novo)} produtos, {len(mud)} mudanças"
        print(host, resumo[host])
    registrar_status("lojas_shopify", resumo)


if __name__ == "__main__":
    main()
