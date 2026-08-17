#!/usr/bin/env python
"""Diz quais posts do Instagram nao embutem.

Um post apagado, arquivado, restrito ou de conta que bloqueia embed continua a
responder HTTP 200 -- o Instagram devolve 200 ate no muro de login, entao pedir
o endereco nao prova nada. O que prova e o iframe: quando o post nao embute, o
embed.js cria o iframe na mesma e ele colapsa para uns poucos pixels.

Foi assim que se descobriu o do Preenchimento de Zigomatico, e por acaso: a
paciente veria um cartao "Ver este resultado no Instagram" onde devia estar o
resultado. Isto existe para dar por isso antes dela.

Le os links da mesma folha que a galeria usa, entao nao ha lista a manter.

    python conferir-embeds.py
"""
import json
import os
import re
import subprocess
import sys
import tempfile
import urllib.parse
import urllib.request

FOLHA = "1aO-AGvUPBe8y71UP7hlnF3a4dH24Jxq3dUv9f2QE6VI"
ABA = "Links"
ALTURA_MINIMA = 200      # abaixo disto o iframe colapsou; os bons dao 800-1000

CHROME = [
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    "/usr/bin/google-chrome", "/usr/bin/chromium",
]

HARNESS = """<!DOCTYPE html><meta charset="utf-8"><body><pre id="s">...</pre>
<div id="alvo"></div>
<script>
var POSTS = %s, alvo = document.getElementById("alvo");
POSTS.forEach(function (p) {
  var d = document.createElement("div");
  d.dataset.id = p[0];
  d.dataset.link = p[1];
  d.innerHTML = '<blockquote class="instagram-media" data-instgrm-captioned'
    + ' data-instgrm-permalink="' + p[1] + '" data-instgrm-version="14"></blockquote>';
  alvo.appendChild(d);
});
var s = document.createElement("script");
s.src = "https://www.instagram.com/embed.js";
s.onload = function () { if (window.instgrm) { window.instgrm.Embeds.process(); } };
s.onerror = function () {
  document.getElementById("s").textContent = '"SEM_EMBED_JS"';
};
document.head.appendChild(s);
setTimeout(function () {
  var out = [].map.call(alvo.children, function (d) {
    var f = d.querySelector("iframe");
    return { id: d.dataset.id, link: d.dataset.link,
             altura: f ? Math.round(f.getBoundingClientRect().height) : 0 };
  });
  document.getElementById("s").textContent = JSON.stringify(out);
}, %d);
</script>
"""


def chrome():
    for c in CHROME:
        if os.path.isfile(c):
            return c
    sys.exit("Erro: nao achei o Chrome.")


def links():
    url = ("https://docs.google.com/spreadsheets/d/%s/gviz/tq?tqx=out:csv&sheet=%s"
           % (FOLHA, urllib.parse.quote(ABA)))
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    txt = urllib.request.urlopen(req, timeout=30).read().decode("utf-8-sig")
    import csv, io
    linhas = [l for l in csv.reader(io.StringIO(txt)) if any(c.strip() for c in l)]
    cab = [c.strip() for c in linhas[0]]
    if cab[:3] != ["ID", "Link", "Procedimento"]:
        sys.exit("Erro: a aba %s devolveu o cabecalho %s.\n"
                 "  O nome da aba mudou? O Sheets responde 200 com a primeira "
                 "aba quando o nome nao existe." % (ABA, cab))
    return [dict(zip(cab, l)) for l in linhas[1:]]


def main():
    regs = links()
    # o mesmo post pode estar em duas linhas; basta testa-lo uma vez
    vistos, posts = set(), []
    for r in regs:
        if r["Link"] and r["Link"] not in vistos:
            vistos.add(r["Link"])
            posts.append([r["ID"], r["Link"], r["Procedimento"]])
    print("a testar %d post(s) distinto(s)... (leva ~1 min)" % len(posts))

    espera = 15000 + 700 * len(posts)
    d = tempfile.mkdtemp(prefix="embeds-")
    p = os.path.join(d, "h.html")
    with open(p, "w", encoding="utf-8") as f:
        f.write(HARNESS % (json.dumps([[a, b] for a, b, _ in posts]), espera))
    saida = subprocess.run(
        [chrome(), "--headless=new", "--disable-gpu", "--no-sandbox",
         "--user-data-dir=" + os.path.join(d, "perfil"),
         "--window-size=700,1200",
         "--virtual-time-budget=%d" % (espera + 20000), "--dump-dom",
         "file:///" + p.replace("\\", "/")],
        capture_output=True, text=True, timeout=espera / 1000 + 120).stdout

    m = re.search(r'<pre id="s">(.*?)</pre>', saida, re.S)
    bruto = m.group(1).strip() if m else "..."
    if bruto == "...":
        sys.exit("Erro: a medicao nao terminou.")
    if bruto == '"SEM_EMBED_JS"':
        sys.exit("Erro: o embed.js do Instagram nao carregou. Sem rede?")

    proc = {a: c for a, b, c in posts}
    dados = json.loads(bruto)
    mortos = []
    print()
    print("%-5s %-9s %-46s %s" % ("ID", "altura", "procedimento", "post"))
    print("-" * 92)
    for o in sorted(dados, key=lambda x: int(x["id"]) if x["id"].isdigit() else 0):
        mau = o["altura"] < ALTURA_MINIMA
        if mau:
            mortos.append(o)
        print("%-5s %-9s %-46s %s %s"
              % (o["id"], o["altura"], proc.get(o["id"], "?")[:45],
                 o["link"].split("/p/")[-1].rstrip("/"),
                 "<-- NAO EMBUTE" if mau else ""))
    print()
    if mortos:
        print("%d post(s) nao embutem. A paciente ve, no lugar deles, o cartao"
              % len(mortos))
        print("\"Ver este resultado no Instagram\".")
        print()
        print("Troque o link na planilha por outro do mesmo procedimento, ou")
        print("apague a linha -- a seccao passa a dizer \"Resultados em breve\".")
        return 1
    print("os %d posts embutem." % len(dados))
    return 0


if __name__ == "__main__":
    sys.exit(main())
