"""Busca pública no Mercado Livre Brasil: preço, vendedor e vendidos dos primeiros resultados.

Saída: dados/mercadolivre/historico.csv (uma linha por anúncio por coleta).
Se a API pública recusar (403/401), registra no status e não tenta contornar.
"""
import urllib.error
import urllib.parse
from comum import DADOS, agora, baixar_json, gravar_csv, linhas_config, registrar_status


def main():
    quando, linhas, resumo = agora(), [], {}
    for termo in linhas_config("termos_ml.txt"):
        url = "https://api.mercadolibre.com/sites/MLB/search?limit=50&q=" + urllib.parse.quote(termo)
        try:
            res = baixar_json(url, pausa=3).get("results", [])
        except urllib.error.HTTPError as e:
            resumo[termo] = f"recusado HTTP {e.code}"
            print(termo, resumo[termo])
            if e.code in (401, 403):
                break
            continue
        for it in res:
            linhas.append({
                "quando": quando, "termo": termo, "titulo": it.get("title"), "preco": it.get("price"),
                "preco_original": it.get("original_price") or "", "frete_gratis": (it.get("shipping") or {}).get("free_shipping"),
                "vendidos": it.get("sold_quantity", ""), "vendedor_id": (it.get("seller") or {}).get("id"),
                "full": (it.get("shipping") or {}).get("logistic_type") == "fulfillment", "link": it.get("permalink"),
            })
        resumo[termo] = f"{len(res)} anúncios"
        print(termo, resumo[termo])
    gravar_csv(DADOS / "mercadolivre" / "historico.csv", linhas, modo="a")
    registrar_status("mercadolivre", resumo)


if __name__ == "__main__":
    main()
