#!/usr/bin/env python
"""Instala o hook de pre-commit que impede commitar os comuns fora de sincronia.

Hooks nao viajam pelo git clone, entao numa maquina nova isto precisa de ser
rodado uma vez em cada repositorio. Rodar de novo e inofensivo.
"""
import os
import stat
import sys

PUBLICO = "baestetica"
PRIVADO = "baestetica_private"

HOOK = """#!/bin/sh
# Recusa o commit se os ficheiros comuns aos dois repositorios divergirem.
# Instalado por instalar-hooks.py; ver COMUM.md.
if [ -f sincronizar-comum.py ]; then
    if ! python sincronizar-comum.py > /tmp/sinc-comum.txt 2>&1; then
        echo ""
        cat /tmp/sinc-comum.txt
        echo ""
        echo "commit recusado: os ficheiros comuns estao fora de sincronia."
        echo "Ver COMUM.md."
        exit 1
    fi
fi
exit 0
"""


def instalar(raiz):
    hooks = os.path.join(raiz, ".git", "hooks")
    if not os.path.isdir(hooks):
        return "%s: nao achei .git/hooks" % os.path.basename(raiz)
    destino = os.path.join(hooks, "pre-commit")
    with open(destino, "w", encoding="utf-8", newline="\n") as f:
        f.write(HOOK)
    os.chmod(destino, os.stat(destino).st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)
    return "%s: hook de pre-commit instalado" % os.path.basename(raiz)


def main():
    aqui = os.path.dirname(os.path.abspath(__file__))
    mae = os.path.dirname(aqui)
    for nome in (PUBLICO, PRIVADO):
        raiz = os.path.join(mae, nome)
        if not os.path.isdir(raiz):
            print("%s: pasta nao encontrada em %s" % (nome, mae))
            continue
        print(instalar(raiz))
    return 0


if __name__ == "__main__":
    sys.exit(main())
