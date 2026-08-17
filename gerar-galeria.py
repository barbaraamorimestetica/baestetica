#!/usr/bin/env python
"""Escreve no HTML uma copia do que a galeria monta, para o Google ler.

A Resultados.html monta as seccoes em JavaScript, a partir da folha (ver
RESULTADOS.md). Isso da autonomia para acrescentar um resultado sem mexer no
site, e cobra um preco: o Googlebot executa JavaScript, mas nem sempre e nem
depressa. O texto das dez seccoes e hoje o maior do site, e a pagina e uma das
tres do sitemap.

Aqui o preco deixa de existir. Este script le a mesma folha e escreve os
titulos e as descricoes direto no HTML, entre marcadores. O que fica no
ficheiro:

  - e o que o Google le, sem depender de script nenhum;
  - e o que a paciente ve se a folha nao responder;
  - e o que o js/galeria.js substitui, quando a folha responde.

NAO entram os <blockquote> do Instagram. Se entrassem, o embed.js podia
processa-los antes de o galeria.js os trocar, e os 18 embeds carregariam de
uma vez -- exatamente o que o carregamento tardio existe para evitar. Em vez
disso fica um link por post, que serve ao Google, a quem nao tem JavaScript,
e a quem usa leitor de ecra.

Correr antes de publicar, sempre que a folha mudar:

    python gerar-galeria.py            mostra o que mudaria
    python gerar-galeria.py --aplicar  escreve no Resultados.html
"""
import csv
import html
import io
import os
import re
import sys
import urllib.parse
import urllib.request

FOLHA = "1aO-AGvUPBe8y71UP7hlnF3a4dH24Jxq3dUv9f2QE6VI"
PAGINA = "Resultados.html"
INICIO = "<!-- galeria:inicio -->"
FIM = "<!-- galeria:fim -->"
COMBINADOS = "Harmonização facial (mais de 1 procedimento)"

ABAS = {
    "Links": ["ID", "Link", "Procedimento"],
    "Procedimentos": ["Procedimento", "Ordem", "Descricao"],
}


def aba(nome):
    url = ("https://docs.google.com/spreadsheets/d/%s/gviz/tq?tqx=out:csv&sheet=%s"
           % (FOLHA, urllib.parse.quote(nome)))
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    txt = urllib.request.urlopen(req, timeout=30).read().decode("utf-8-sig")
    linhas = [l for l in csv.reader(io.StringIO(txt)) if any(c.strip() for c in l)]
    cab = [c.strip() for c in linhas[0]]
    esperado = ABAS[nome]
    if cab[:len(esperado)] != esperado:
        # o Sheets responde 200 com a PRIMEIRA aba quando o nome nao existe
        sys.exit("Erro: a aba %s devolveu o cabecalho %s, esperava %s.\n"
                 "  O nome da aba mudou?" % (nome, cab, esperado))
    return [dict(zip(cab, l)) for l in linhas[1:]]


def paragrafos(texto):
    saida = []
    for bloco in re.split(r"\n\s*\n", texto.replace("\r\n", "\n")):
        p = " ".join(l.strip() for l in bloco.split("\n")).strip()
        if p:
            saida.append(p)
    return saida


def agrupar(links, definidos):
    mapa = {}
    juntar = COMBINADOS in definidos
    for l in links:
        if not l["Link"]:
            continue
        ps = [p.strip() for p in l["Procedimento"].split(";") if p.strip()]
        if not ps:
            continue
        if len(ps) > 1 and juntar:
            mapa.setdefault(COMBINADOS, []).append(l)
        else:
            for p in ps:
                mapa.setdefault(p, []).append(l)
    return mapa


def secao(i, nome, descricao, posts):
    e = html.escape
    partes = ['        <section class="secao-resultado bg-white rounded-3xl'
              ' gold-border-glow mb-10" data-piso>',
              '            <div class="text-left mb-6">',
              '                <span class="tinta-forte font-bold text-xs uppercase'
              ' tracking-widest">Procedimento %02d</span>' % i,
              '                <h3 class="font-serif text-2xl font-bold tinta-texto">'
              '%s</h3>' % e(nome),
              '            </div>',
              '            <div class="mb-8 text-left">']
    for p in paragrafos(descricao):
        partes.append('                <p class="text-sm tinta-texto leading-relaxed'
                      ' text-justify medida-leitura mb-4 last:mb-0">%s</p>' % e(p))
    partes.append('            </div>')
    if posts:
        partes.append('            <ul class="flex flex-wrap justify-center gap-4'
                      ' text-sm">')
        for n, l in enumerate(posts, 1):
            partes.append('                <li><a href="%s" target="_blank"'
                          ' rel="noopener" class="tinta-forte alvo-toque underline">'
                          'Resultado %d de %s no Instagram</a></li>'
                          % (e(l["Link"]), n, e(nome)))
        partes.append('            </ul>')
    else:
        partes.append('            <p class="text-center text-sm tinta-suave italic'
                      ' border borda-marca rounded-xl py-6">Resultados em breve.</p>')
    partes.append('        </section>')
    return "\n".join(partes)


def montar():
    links = aba("Links")
    procs = aba("Procedimentos")
    ordenados = sorted(procs, key=lambda p: int(p["Ordem"] or 0))
    definidos = {p["Procedimento"].strip() for p in ordenados}
    porProc = agrupar(links, definidos)

    orfaos = sorted(set(porProc) - definidos)
    if orfaos:
        print("AVISO: sem linha na aba Procedimentos, ficam de fora: %s"
              % ", ".join(orfaos))

    blocos = []
    for i, p in enumerate(ordenados, 1):
        nome = p["Procedimento"].strip()
        blocos.append(secao(i, nome, p["Descricao"], porProc.get(nome, [])))
    return ordenados, porProc, "\n\n".join(blocos)


def main():
    aplicar = "--aplicar" in sys.argv
    raiz = os.path.dirname(os.path.abspath(__file__))
    caminho = os.path.join(raiz, PAGINA)
    t = io.open(caminho, encoding="utf-8").read()
    if t.count(INICIO) != 1 or t.count(FIM) != 1:
        sys.exit("Erro: %s precisa de um %s e um %s." % (PAGINA, INICIO, FIM))

    ordenados, porProc, novo = montar()
    a, b = t.index(INICIO) + len(INICIO), t.index(FIM)
    antigo = t[a:b]
    corpo = "\n" + novo + "\n\n        "

    print("%-46s %s" % ("seccao", "posts"))
    print("-" * 58)
    for p in ordenados:
        n = len(porProc.get(p["Procedimento"].strip(), []))
        print("%-46s %s" % (p["Procedimento"], n or "(em breve)"))
    print()

    if antigo == corpo:
        print("o HTML ja esta igual a folha; nada a fazer.")
        return 0
    print("o HTML difere da folha: %d -> %d caracteres." % (len(antigo), len(corpo)))
    if not aplicar:
        print("Rode 'python gerar-galeria.py --aplicar' para escrever.")
        return 1
    io.open(caminho, "w", encoding="utf-8", newline="").write(t[:a] + corpo + t[b:])
    print("escrito em %s." % PAGINA)
    return 0


if __name__ == "__main__":
    sys.exit(main())
