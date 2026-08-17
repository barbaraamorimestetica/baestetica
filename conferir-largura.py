#!/usr/bin/env python
"""Procura transbordo lateral nas paginas, em ecras estreitos.

Uma pagina que empurra de lado obriga a paciente a arrastar para ler, e no
telefone isso e o defeito que mais se sente. Nao aparece em nenhuma das outras
conferencias: o contraste passa, as classes tem regra, o rodape esta certo, e
mesmo assim o texto sai fora da tela.

Ja mordeu duas vezes neste projeto, as duas por motivos diferentes:

  - o rodape tinha white-space:nowrap na linha da credencial, que tem 314px
    e nao cabia num ecra de 320;
  - o embed do Instagram traz min-width:326px no atributo style.

POR QUE ISTO NAO E UM SCREENSHOT: o Chrome headless nao aceita janela abaixo
de 500px -- pedir --window-size=375 devolve innerWidth=500 e recorta a imagem
em 375, o que parece corte de texto e nao e. A unica forma de ter um viewport
de telefone a serio e por iframe, que e o que se faz aqui.

Elementos dentro de um contentor que rola de proposito (o carrossel) ficam de
fora: eles PODEM passar da borda, e para isso que servem.
"""
import json
import os
import re
import subprocess
import sys
import tempfile

LARGURAS = [320, 360, 375, 414]

# folha A4 de largura fixa: transborda num ecra estreito por desenho
FORA = {"catalogo-impressao.html"}

# O servidor tem de estar na pasta MAE, e nao dentro do repositorio: o 404.html
# referencia /baestetica/css/... em caminho absoluto, porque e assim que o
# GitHub Pages o serve. Com a pasta como raiz ele fica sem folha nenhuma, e o
# botao de WhatsApp aparece com 448px -- defeito que so existe no ambiente de
# teste. Medir com o enderecamento da producao evita perseguir fantasmas.
BASE = os.environ.get("BASE_CONFERE", "/baestetica/")

CHROME = [
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    "/usr/bin/google-chrome", "/usr/bin/chromium",
]

HARNESS = """<!DOCTYPE html><meta charset="utf-8"><body><pre id="s">...</pre>
<script>
var ALVOS = %s, PRAZO = 9000;
var saida = [], falta = ALVOS.length;

function medir(f, rot) {
  var o = { alvo: rot };
  try {
    var d = f.contentDocument, de = d.documentElement, lim = de.clientWidth;
    o.viewport = lim;
    o.transbordo = de.scrollWidth - lim;
    o.culpados = [].slice.call(d.querySelectorAll("body *")).filter(function (e) {
      if (e.closest(".carrossel-trilho")) { return false; }   // rola de proposito
      var b = e.getBoundingClientRect();
      return b.right > lim + 0.5 && b.width > 0;
    }).slice(0, 4).map(function (e) {
      return e.tagName + "." + String(e.className || "").slice(0, 40)
           + " larg=" + Math.round(e.getBoundingClientRect().width);
    });
  } catch (err) { o.erro = String(err); }
  saida.push(o);
  if (--falta === 0) { document.getElementById("s").textContent = JSON.stringify(saida); }
}

ALVOS.forEach(function (a) {
  var f = document.createElement("iframe");
  f.style.cssText = "width:" + a[0] + "px;height:900px;border:0;position:absolute;"
                  + "left:0;top:0;visibility:hidden";
  var feito = false;
  function uma() { if (!feito) { feito = true; medir(f, a[0] + "  " + a[1]); } }
  f.onload = uma;
  setTimeout(uma, PRAZO);       // uma pagina que nunca carrega nao trava a conta
  f.src = a[1];
  document.body.appendChild(f);
});
</script>
"""


def chrome():
    for c in CHROME:
        if os.path.isfile(c):
            return c
    sys.exit("Erro: nao achei o Chrome.")


def paginas(raiz):
    return sorted(a for a in os.listdir(raiz)
                  if a.endswith(".html") and a not in FORA and not a.startswith("_"))


def main():
    raiz = os.path.dirname(os.path.abspath(__file__))
    alvos = [[L, BASE + a] for a in paginas(raiz) for L in LARGURAS]
    nome = "_largura_%d.html" % os.getpid()
    caminho = os.path.join(raiz, nome)
    with open(caminho, "w", encoding="utf-8") as f:
        f.write(HARNESS % json.dumps(alvos))

    porta = os.environ.get("PORTA_CONFERE", "8792")
    perfil = tempfile.mkdtemp(prefix="larg-")
    try:
        saida = subprocess.run(
            [chrome(), "--headless=new", "--disable-gpu", "--no-sandbox",
             "--disk-cache-size=1", "--user-data-dir=" + perfil,
             "--window-size=1200,1000", "--virtual-time-budget=90000",
             "--dump-dom", "http://127.0.0.1:%s%s%s" % (porta, BASE, nome)],
            capture_output=True, text=True, timeout=300).stdout
    finally:
        os.remove(caminho)

    m = re.search(r'<pre id="s">(.*?)</pre>', saida, re.S)
    if not m or m.group(1).strip() == "...":
        sys.exit("Erro: a medicao nao terminou. O servidor tem de estar na pasta MAE.\n"
                 "  Esperava http://127.0.0.1:%s%s" % (porta, BASE))

    dados = sorted(json.loads(m.group(1).replace("&amp;", "&")),
                   key=lambda o: o["alvo"].split()[1] + o["alvo"].split()[0])
    achados = 0
    print("%-34s %9s %11s" % ("pagina e largura", "viewport", "transbordo"))
    print("-" * 58)
    for o in dados:
        if "erro" in o:
            print("%-34s %s" % (o["alvo"], o["erro"]))
            achados += 1
            continue
        mau = o["transbordo"] > 0
        achados += mau
        print("%-34s %9d %11d %s" % (o["alvo"], o["viewport"], o["transbordo"],
                                     "<-- EMPURRA DE LADO" if mau else ""))
        if mau:
            for c in o["culpados"]:
                print("      %s" % c)
    print()
    if achados:
        print("%d medicao(oes) com transbordo." % achados)
        return 1
    print("nenhuma pagina empurra de lado, de %dpx a %dpx."
          % (LARGURAS[0], LARGURAS[-1]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
