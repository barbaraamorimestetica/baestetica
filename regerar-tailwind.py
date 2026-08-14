#!/usr/bin/env python
"""Regera a folha compilada do Tailwind de um dos dois repositorios.

Faz a mao o que o Tailwind CLI faria, porque nao ha Node nesta maquina: monta um
HTML temporario com o CDN, o tema e uma <div> cujo class tem TODOS os tokens
usados, abre no Chrome headless e recolhe o <style> que o CDN injetou.

    python regerar-tailwind.py                  mostra o que mudaria
    python regerar-tailwind.py --aplicar        escreve as folhas

POR QUE NAO ESCREVE POR OMISSAO: esta e a operacao mais fragil do projeto, e o
erro dela e silencioso -- uma utilidade que falte nao da erro, so nao pinta. O
modo de conferencia lista os seletores que entrariam e os que sairiam, para se
poder olhar antes.

Os tokens sao extraidos pelo MESMO codigo que o conferir-classes.py usa, de
proposito: se os dois lessem o HTML de maneira diferente, a conferencia poderia
aprovar uma folha gerada sem uma classe que ela mesma procura.

COMUM AOS DOIS REPOSITORIOS -- ver COMUM.md. Depois de mexer, sincronize.
"""
import importlib.util
import os
import re
import subprocess
import sys
import tempfile

# O extractor de tokens vem do conferir-classes.py, de proposito: se os dois
# lessem o HTML de maneira diferente, este gerador poderia deixar de fora uma
# classe que a conferencia procura -- e a folha passaria a conferencia com um
# buraco. O nome do ficheiro tem hifen, que nao e nome de modulo valido, entao
# ele e carregado pelo caminho.
def _carregar_conferencia():
    caminho = os.path.join(os.path.dirname(os.path.abspath(__file__)), "conferir-classes.py")
    spec = importlib.util.spec_from_file_location("conferir_classes", caminho)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


cc = _carregar_conferencia()

CHROME = [
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    "google-chrome", "chromium",
]

VERSAO = "3.4.17"

# (pasta, folha gerada). O tema e igual nos dois: depois de a cor sair dos nomes
# de classe, nenhum nome de cor do tema antigo (roseGold, borderRose, softGray,
# darkText...) e usado em pagina nenhuma -- so as duas familias de fonte
# sobreviveram, e essas precisam de ficar, porque o preflight do Tailwind poe a
# fontFamily.sans no <html> e o .font-serif e usado 83 vezes.
REPOS = [
    ("baestetica", os.path.join("css", "site.css")),
    ("baestetica_private", os.path.join("assets", "tailwind.css")),
]

CONFIG = """
tailwind.config = {
    theme: {
        extend: {
            fontFamily: {
                sans:  ['Montserrat', 'sans-serif'],
                serif: ['Playfair Display', 'serif']
            }
        }
    }
}
"""


def chrome():
    for c in CHROME:
        if os.path.isfile(c):
            return c
    return CHROME[-2]


def tokens(raiz):
    """Todos os tokens de classe usados, pelo extractor da conferencia."""
    fora = set()
    for a in sorted(os.listdir(raiz)):
        if not a.endswith(".html") or " " in a:
            continue
        html = open(os.path.join(raiz, a), encoding="utf-8").read()
        fora.update(cc.usadas(html).keys())
    return sorted(fora)


def seletores(css):
    # Tira o comentario antes de procurar seletor. Sem isto o proprio cabecalho
    # entra na conta: css/README.md, cdn.tailwindcss.com e tailwind.config dao
    # ".md", ".tailwindcss" e ".config" como se fossem classes que sairam.
    css = re.sub(r"/\*.*?\*/", "", css, flags=re.S)
    return {re.sub(r"\\(.)", r"\1", m.group(1))
            for m in re.finditer(r"\.((?:[\w-]|\\.)+)", css)}


def gerar(raiz, toks):
    """Devolve o CSS que o CDN injeta para este conjunto de tokens."""
    html = ("<!DOCTYPE html><meta charset=\"utf-8\">\n"
            "<script src=\"https://cdn.tailwindcss.com/%s\"></script>\n"
            "<script>%s</script>\n"
            "<div class=\"%s\"></div>\n" % (VERSAO, CONFIG, " ".join(toks)))
    d = tempfile.mkdtemp(prefix="tw-")
    entrada = os.path.join(d, "harness.html")
    with open(entrada, "w", encoding="utf-8") as f:
        f.write(html)
    saida = subprocess.run(
        [chrome(), "--headless=new", "--disable-gpu", "--virtual-time-budget=30000",
         "--dump-dom", "file:///" + entrada.replace("\\", "/")],
        capture_output=True, text=True, encoding="utf-8", errors="replace").stdout
    m = re.search(r"<style[^>]*>(.*?)</style>", saida, re.S)
    if not m:
        sys.exit("Erro: o CDN nao injetou <style>. Sem rede? Veja %s" % entrada)
    import html as H
    return H.unescape(m.group(1)).strip(), entrada


def main():
    aplicar = "--aplicar" in sys.argv
    aqui = os.path.dirname(os.path.abspath(__file__))
    mae = os.path.dirname(aqui)
    problema = 0

    for nome, rel in REPOS:
        raiz = os.path.join(mae, nome)
        folha = os.path.join(raiz, rel)
        if not os.path.isfile(folha):
            print("%s: nao achei %s" % (nome, rel)); problema += 1; continue

        antigo = open(folha, encoding="utf-8").read()
        cab = antigo[:antigo.index("*/") + 2]        # o cabecalho fica
        toks = tokens(raiz)
        novo, harness = gerar(raiz, toks)

        a, b = seletores(antigo), seletores(novo)
        print("=== %s -> %s ===" % (nome, rel))
        print("    %d tokens usados no HTML" % len(toks))
        print("    %5.1f KB  ->  %5.1f KB" % (len(antigo) / 1024, (len(cab) + len(novo)) / 1024))
        saem, entram = sorted(a - b), sorted(b - a)
        print("    saem  %3d seletor(es): %s" % (len(saem), ", ".join(saem[:14]) + (" ..." if len(saem) > 14 else "")))
        print("    entram %2d seletor(es): %s" % (len(entram), ", ".join(entram[:14]) + (" ..." if len(entram) > 14 else "")))

        # guarda: nenhum token usado pode ficar sem regra na folha nova
        faltam = [t for t in toks if t not in b and re.match(r"^[a-z].*[-\[]", t)]
        if faltam:
            print("    ATENCAO  %d token(s) usados que a folha nova nao tem:" % len(faltam))
            print("             %s" % ", ".join(faltam[:20]))
            print("             (pode ser classe propria, definida a mao noutro ficheiro)")

        if aplicar:
            with open(folha, "w", encoding="utf-8", newline="") as f:
                f.write(cab + "\n" + novo + "\n")
            print("    ESCRITA.")
        else:
            print("    (nada escrito; use --aplicar)")
        print("    harness: %s" % harness)
        print()

    if not aplicar:
        print("Depois de aplicar, conferir SEMPRE com:")
        print("  python conferir-classes.py")
        print("  e a comparacao de estilo computado descrita em TAILWIND.md")
    return problema


if __name__ == "__main__":
    sys.exit(main())
