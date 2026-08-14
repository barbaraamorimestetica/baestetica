#!/usr/bin/env python
"""Confere o sitemap.xml contra as paginas que existem de facto.

    python conferir-sitemap.py           confere o local
    python conferir-sitemap.py --ar      confere tambem o que esta publicado

SO DESTE REPOSITORIO: a ferramenta interna nao e indexada nem tem sitemap.

O QUE ELE PEGA, e por que cada coisa importa para o Google:

  - XML invalido. O Search Console rejeita o ficheiro inteiro, nao a linha.
  - URL no sitemap sem ficheiro correspondente. Da erro de rastreio.
  - URL no sitemap com <meta name="robots" content="noindex">. E contraditorio:
    o sitemap diz "indexa isto" e a pagina diz "nao indexa". O Google obedece a
    pagina e registra o conflito.
  - canonical que nao bate com a URL do sitemap, ao caractere. Se diferirem, o
    Google segue o canonical e o sitemap passa a apontar para o lugar errado.
  - lastmod que nao bate com a ultima alteracao real no git. O Google usa o
    lastmod quando ele e consistente e passa a ignora-lo quando nao e.
  - pagina indexavel que ficou FORA do sitemap. Aqui as tres excluidas tem
    noindex, e por isso e correto ficarem fora -- mas isso e verificado, nao
    presumido.

O modo --ar diz o que esta publicado, que nem sempre e o que esta aqui: o
sitemap deste repositorio ja esteve 39 commits a frente do site no ar, com a
URL a devolver 404. Enviar o sitemap ao Search Console nesse estado falha, e a
falha nao e do sitemap.
"""
import os
import re
import subprocess
import sys
import xml.etree.ElementTree as ET

NS = "{http://www.sitemaps.org/schemas/sitemap/0.9}"
BASE = "https://barbaraamorimestetica.github.io/baestetica/"
FICHEIRO = "sitemap.xml"


def robots(caminho):
    t = open(caminho, encoding="utf-8").read()
    m = re.search(r'<meta[^>]+name=["\']robots["\'][^>]+content=["\']([^"\']+)', t)
    return (m.group(1) if m else ""), t


def canonical(t):
    m = re.search(r'<link[^>]+rel=["\']canonical["\'][^>]+href=["\']([^"\']+)', t)
    return m.group(1) if m else None


def git_data(rel):
    d = subprocess.run(["git", "log", "-1", "--format=%ad", "--date=short", "--", rel],
                       capture_output=True, text=True).stdout.strip()
    return d or None


def main():
    aqui = os.path.dirname(os.path.abspath(__file__))
    os.chdir(aqui)
    problemas = []

    if not os.path.isfile(FICHEIRO):
        print("ERRO: nao achei %s" % FICHEIRO)
        return 1

    try:
        raiz = ET.parse(FICHEIRO).getroot()
    except ET.ParseError as e:
        print("ERRO: XML invalido -- o Search Console rejeita o ficheiro inteiro.")
        print("      %s" % e)
        return 1

    entradas = {}
    for u in raiz.findall(NS + "url"):
        entradas[u.findtext(NS + "loc")] = u.findtext(NS + "lastmod")

    print("%s: XML valido, %d URL(s)" % (FICHEIRO, len(entradas)))
    print()
    print("%-28s %-8s %-9s %-10s %s" % ("ficheiro", "existe", "noindex", "canonical", "lastmod"))
    print("-" * 78)

    for loc, lastmod in sorted(entradas.items()):
        if not loc.startswith(BASE):
            problemas.append("%s: fora do endereco base %s" % (loc, BASE))
            print("%-28s %s" % (loc[:28], "FORA DA BASE"))
            continue
        rel = loc[len(BASE):] or "index.html"
        if not os.path.isfile(rel):
            problemas.append("%s: no sitemap mas o ficheiro nao existe" % rel)
            print("%-28s %-8s" % (rel, "FALTA"))
            continue

        rb, t = robots(rel)
        tem_noindex = "noindex" in rb
        if tem_noindex:
            problemas.append("%s: esta no sitemap E tem noindex -- contraditorio" % rel)

        can = canonical(t)
        if can is None:
            problemas.append("%s: sem canonical" % rel)
            est_can = "FALTA"
        elif can != loc:
            problemas.append("%s: canonical %s != URL do sitemap %s" % (rel, can, loc))
            est_can = "DIFERE"
        else:
            est_can = "bate"

        d = git_data(rel)
        if d and lastmod != d:
            problemas.append("%s: lastmod %s mas a ultima alteracao no git e %s" % (rel, lastmod, d))
            est_lm = "%s != git %s" % (lastmod, d)
        else:
            est_lm = lastmod or "AUSENTE"
            if not lastmod:
                problemas.append("%s: sem lastmod" % rel)

        print("%-28s %-8s %-9s %-10s %s" % (rel, "sim", "SIM" if tem_noindex else "nao",
                                            est_can, est_lm))

    print()
    print("paginas do repositorio fora do sitemap:")
    for a in sorted(os.listdir(".")):
        if not a.endswith(".html"):
            continue
        url = BASE + ("" if a == "index.html" else a)
        if url in entradas:
            continue
        rb, _ = robots(a)
        if "noindex" in rb:
            print("  %-32s tem noindex -- correto ficar fora" % a)
        elif a == "404.html":
            print("  %-32s pagina de erro -- correto ficar fora" % a)
        else:
            problemas.append("%s: indexavel e fora do sitemap" % a)
            print("  %-32s INDEXAVEL E FORA -- devia estar no sitemap" % a)

    if "--ar" in sys.argv:
        print()
        print("o que esta publicado (o envio ao Search Console atua NISTO):")
        import urllib.error
        import urllib.request
        for alvo in [BASE + FICHEIRO, BASE, "https://barbaraamorimestetica.github.io/robots.txt"]:
            try:
                with urllib.request.urlopen(alvo, timeout=15) as r:
                    print("  %-62s %s" % (alvo, r.status))
            except urllib.error.HTTPError as e:
                print("  %-62s %s" % (alvo, e.code))
                if alvo.endswith(FICHEIRO):
                    problemas.append("o sitemap publicado devolve %s: enviar agora falha" % e.code)
            except Exception as e:
                print("  %-62s sem rede? %s" % (alvo, str(e)[:30]))

    print()
    if problemas:
        print("%d problema(s):" % len(problemas))
        for p in problemas:
            print("  - %s" % p)
        return 1
    print("nenhum problema: o sitemap concorda com as paginas, com os canonicals")
    print("e com o historico do git.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
