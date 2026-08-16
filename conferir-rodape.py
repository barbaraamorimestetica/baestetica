#!/usr/bin/env python
"""Confere o rodape unico das folhas que viram PDF, nos dois repositorios.

O rodape esta descrito em RODAPE.md. Aqui verifica-se, por maquina, o que a
memoria nao garante:

  - toda folha exportavel tem exatamente um rodape;
  - a numeracao forma sequencias validas (1/Y, 2/Y, ... Y/Y);
  - nao sobrou nenhum rodape no formato antigo.

As paginas sao descobertas com os.listdir, e nao por lista escrita a mao: foi
uma pagina esquecida numa lista manual que escondeu um link a 3,87:1 neste
projeto.
"""
import os
import re
import sys

PUBLICO = "baestetica"
PRIVADO = "baestetica_private"

MARCA = "Rodape unico das folhas exportadas"
FOLHA = re.compile(r'class="[^"]*\b(?:pdf-page|print-page)\b')
NUMERO = re.compile(r'P&aacute;gina (\d+)/(\d+)')
ANTIGO = re.compile(r'P(?:&aacute;|á)gina \d+ de \d+')


def raizes():
    aqui = os.path.dirname(os.path.abspath(__file__))
    mae = os.path.dirname(aqui)
    pub, pri = os.path.join(mae, PUBLICO), os.path.join(mae, PRIVADO)
    if not os.path.isdir(pub) or not os.path.isdir(pri):
        sys.exit("Erro: esperava '%s' e '%s' como pastas vizinhas de '%s'."
                 % (PUBLICO, PRIVADO, mae))
    return pub, pri


def exporta(txt):
    """A folha vira PDF? Ou pelo html2pdf, ou pela impressao do navegador."""
    return "html2pdf" in txt or "print-page" in txt


def sequencias_validas(pares):
    """[(1,2),(2,2),(1,1),(1,1)] e valido: tres documentos, um por sequencia."""
    i = 0
    while i < len(pares):
        pag, tot = pares[i]
        if pag != 1:
            return False, "a folha %d/%d nao abre uma sequencia" % (pag, tot)
        for esperado in range(1, tot + 1):
            if i >= len(pares):
                return False, "faltam folhas para fechar uma sequencia de %d" % tot
            if pares[i] != (esperado, tot):
                return False, ("esperava %d/%d e veio %d/%d"
                               % (esperado, tot, pares[i][0], pares[i][1]))
            i += 1
    return True, ""


def main():
    achados = []
    folhas_totais = 0
    paginas = 0

    for raiz in raizes():
        rotulo = os.path.basename(raiz)
        for nome in sorted(os.listdir(raiz)):
            if not nome.endswith(".html"):
                continue
            caminho = os.path.join(raiz, nome)
            with open(caminho, encoding="utf-8") as f:
                txt = f.read()
            if not exporta(txt):
                continue
            n_folhas = len(FOLHA.findall(txt))
            n_rodapes = txt.count(MARCA)
            if not n_folhas:
                continue
            paginas += 1
            folhas_totais += n_folhas
            onde = "%s/%s" % (rotulo, nome)

            if n_rodapes != n_folhas:
                achados.append("%-46s %d folha(s) e %d rodape(s)"
                               % (onde, n_folhas, n_rodapes))
            pares = [(int(a), int(b)) for a, b in NUMERO.findall(txt)]
            if len(pares) != n_rodapes:
                achados.append("%-46s %d rodape(s) e %d numeracao(oes)"
                               % (onde, n_rodapes, len(pares)))
            else:
                ok, motivo = sequencias_validas(pares)
                if not ok:
                    achados.append("%-46s numeracao: %s" % (onde, motivo))
            if ANTIGO.search(txt):
                achados.append("%-46s sobrou rodape no formato antigo" % onde)

            print("  %-46s %d folha(s), %d rodape(s)  %s"
                  % (onde, n_folhas, n_rodapes,
                     " ".join("%d/%d" % p for p in pares)))

    print()
    if achados:
        print("%d achado(s):" % len(achados))
        for a in achados:
            print("  " + a)
        return 1
    print("%d pagina(s) exportavel(is), %d folha(s): todas com o rodape unico,"
          % (paginas, folhas_totais))
    print("numeracao coerente e nenhum rodape antigo.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
