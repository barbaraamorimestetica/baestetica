#!/usr/bin/env python
"""Acha classe usada no HTML que nao tem regra em folha de estilo nenhuma.

E o modo de falhar deste projeto. Uma classe do Tailwind que nao esteja na folha
compilada nao tem efeito e nao da erro: nao aparece no console, nao quebra nada,
so nao pinta. O mesmo vale para uma classe que nem existe no Tailwind -- text-md
parece plausivel e nao faz parte da escala (vai de text-sm para text-base).

Como funciona: para cada pagina, junta as folhas que ela carrega mais o <style>
dela, extrai todo seletor de classe definido, e compara com toda classe usada --
inclusive as que so aparecem dentro de JavaScript, que uma varredura do HTML nao
encontra.

    python conferir-classes.py            confere os dois repositorios
    python conferir-classes.py --listar   mostra tambem as classes ignoradas

COMUM AOS DOIS REPOSITORIOS -- ver COMUM.md. Depois de mexer, sincronize.
"""
import os
import re
import sys

PUBLICO = "baestetica"
PRIVADO = "baestetica_private"

# Classes que existem para o JavaScript agarrar ou para o CSS de terceiros, e
# que por isso nao precisam de regra propria. Cada uma tem de ganhar o seu lugar
# aqui por um motivo escrito, senao a lista vira tapete para esconder defeito.
SEM_REGRA_DE_PROPOSITO = {
    "html2pdf__page-break": "o html2pdf procura esta classe para cortar folha",
    "instagram-media":      "e o embed.js do Instagram que estiliza este bloco",
    "group":                "marcador do Tailwind; quem pinta e o group-hover:",
    "val-parcela":          "gancho de querySelectorAll no fluxo-de-caixa",
}


def folhas_e_estilo(caminho, raiz):
    """Devolve o CSS que a pagina realmente carrega, concatenado."""
    t = open(caminho, encoding="utf-8").read()
    css = []
    for m in re.finditer(r'<link[^>]+rel=["\']stylesheet["\'][^>]*>', t):
        h = re.search(r'href=["\']([^"\']+)["\']', m.group(0))
        if not h:
            continue
        ref = h.group(1)
        if ref.startswith("http"):
            continue                      # Google Fonts: nao define classe
        rel = ref.lstrip("/")
        for tentativa in (os.path.join(raiz, rel),
                          os.path.join(raiz, rel.split("/", 1)[-1])):
            if os.path.isfile(tentativa):
                css.append(open(tentativa, encoding="utf-8").read())
                break
    for m in re.finditer(r"<style[^>]*>(.*?)</style>", t, re.S):
        css.append(m.group(1))
    return t, "\n".join(css)


def definidas(css):
    """Todo seletor de classe presente no CSS, ja desescapado."""
    fora = set()
    for m in re.finditer(r"\.((?:[\w-]|\\.)+)", css):
        fora.add(re.sub(r"\\(.)", r"\1", m.group(1)))
    return fora


def usadas(html):
    """Toda classe usada: em class=, em classList e dentro de string de JS."""
    fora = {}

    def guarda(valor, origem):
        # Dentro de um class= pode haver interpolacao de template literal. As
        # classes que interessam sao as string literais de dentro dela; o resto
        # e expressao. Sem isto, um ternario como
        #     class="... ${x === 'A' ? 'text-green-700' : 'text-red-600'}"
        # entra como os pedacos ===, ?, : -- e as duas classes de verdade
        # passam sem ser conferidas, que e justamente o caso que este script
        # existe para pegar.
        def interpolacao(m):
            expr = m.group(1)
            # Nem toda string literal numa expressao e nome de classe: o operando
            # de uma comparacao nao e. Em
            #     ${e.tipo === 'Recebimento' ? 'text-green-700' : 'text-red-600'}
            # as classes sao as duas ultimas, e 'Recebimento' e um valor de
            # dados. Sem descartar o operando, ele entrava como classe sem regra.
            expr = re.sub(r"""(?:===?|!==?)\s*['"][^'"]*['"]""", " ", expr)
            for s in re.finditer(r"""['"]([^'"]*)['"]""", expr):
                for c in s.group(1).split():
                    if c:
                        fora.setdefault(c, set()).add(origem + ":interpolado")
            return " "
        valor = re.sub(r"\$\{([^}]*)\}", interpolacao, valor)
        for c in valor.split():
            if c and "$" not in c and "{" not in c and "}" not in c:
                fora.setdefault(c, set()).add(origem)

    # atributo class= no HTML e dentro de string de JavaScript
    for m in re.finditer(r'class\s*=\s*(["\'])(.*?)\1', html, re.S):
        guarda(m.group(2), "class=")
    # class=\"...\" escapado dentro de string de JS
    for m in re.finditer(r'class\s*=\s*\\(["\'])(.*?)\\\1', html, re.S):
        guarda(m.group(2), "js")
    # classList.add('a','b') / .remove(...) / .toggle(...)
    for m in re.finditer(r"classList\.(add|remove|toggle)\(([^)]*)\)", html):
        args = m.group(2)
        # toggle(classe, forca): so o primeiro argumento e classe. Sem isto o
        # segundo argumento entra como classe -- foi assim que o id
        # 'is_parcelado' apareceu na lista de classes sem regra.
        if m.group(1) == "toggle":
            args = args.split(",", 1)[0]
        for s in re.finditer(r'["\']([^"\']+)["\']', args):
            guarda(s.group(1), "classList")
    # className = '...'
    for m in re.finditer(r'className\s*=\s*(["\'`])(.*?)\1', html, re.S):
        guarda(m.group(2), "className")
    return fora


def conferir(raiz, rotulo):
    problemas = []
    total_usadas = set()
    for a in sorted(os.listdir(raiz)):
        if not a.endswith(".html"):
            continue
        # Nao ha excecao para nome com espaco. Havia, e ela custou caro: o
        # "Catalogo de Procedimentos.html" ficou fora de toda a verificacao deste
        # projeto, e escondeu um link a 3,72:1 -- a mesma reprova de contraste que
        # foi fechada 61 vezes em outras paginas. Nada aqui precisava do salto.
        html, css = folhas_e_estilo(os.path.join(raiz, a), raiz)
        tem = definidas(css)
        for c, origens in usadas(html).items():
            total_usadas.add(c)
            if c in tem or c in SEM_REGRA_DE_PROPOSITO:
                continue
            problemas.append((a, c, ",".join(sorted(origens))))
    print("=== %s: %d classes distintas usadas ===" % (rotulo, len(total_usadas)))
    if not problemas:
        print("    toda classe usada tem regra em alguma folha.")
        return 0
    print("    %d classe(s) SEM REGRA -- nao pintam, e nao dao erro:" % len(problemas))
    for a, c, origens in problemas:
        print("      %-28s %-34s (%s)" % (a, c, origens))
    return len(problemas)


def main():
    aqui = os.path.dirname(os.path.abspath(__file__))
    mae = os.path.dirname(aqui)
    ruim = 0
    for nome in (PUBLICO, PRIVADO):
        raiz = os.path.join(mae, nome)
        if not os.path.isdir(raiz):
            print("%s: pasta nao encontrada em %s" % (nome, mae))
            continue
        ruim += conferir(raiz, nome)
        print()
    return 1 if ruim else 0


if __name__ == "__main__":
    sys.exit(main())
