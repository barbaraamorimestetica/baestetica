#!/usr/bin/env python
"""Mantem identicos os ficheiros comuns aos dois repositorios baestetica.

Os dois repositorios sao separados -- um publico, um privado -- e nao ha etapa
de build nem Node na maquina, entao nao da para publicar um pacote nem usar
submodulo sem trazer um terceiro repositorio para manter. A escolha foi
duplicacao controlada: o ficheiro existe nos dois lados, identico, e a copia e
verificada por maquina em vez de por memoria.

Como se usa, de dentro de qualquer um dos dois repositorios:

    python sincronizar-comum.py            confere e diz o que divergiu
    python sincronizar-comum.py --aplicar  copia do canonico para o outro lado

O lado canonico e o publico (baestetica). Nao por hierarquia: e so preciso que
um dos dois seja, e o publico e o que define a identidade visual da marca.

O hook de pre-commit de cada repositorio chama isto no modo de conferencia e
recusa o commit se houver divergencia. E por isso que "atualizar em conjunto"
deixa de depender de lembrar.
"""
import filecmp
import hashlib
import os
import shutil
import sys

# nome do repositorio publico e do privado, como pastas vizinhas
PUBLICO = "baestetica"
PRIVADO = "baestetica_private"

# cada par: (caminho dentro do publico, caminho dentro do privado)
PARES = [
    (os.path.join("css", "tokens.css"), os.path.join("assets", "tokens.css")),
    (os.path.join("css", "componentes.css"), os.path.join("assets", "componentes.css")),
    ("sincronizar-comum.py", "sincronizar-comum.py"),
    ("COMUM.md", "COMUM.md"),
]


def raizes():
    """Descobre a pasta dos dois repositorios a partir de onde o script esta."""
    aqui = os.path.dirname(os.path.abspath(__file__))
    mae = os.path.dirname(aqui)
    pub, pri = os.path.join(mae, PUBLICO), os.path.join(mae, PRIVADO)
    if not os.path.isdir(pub) or not os.path.isdir(pri):
        sys.exit("Erro: esperava '%s' e '%s' como pastas vizinhas de '%s'."
                 % (PUBLICO, PRIVADO, mae))
    return pub, pri


def resumo(caminho):
    if not os.path.exists(caminho):
        return None
    with open(caminho, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()[:12]


def main():
    aplicar = "--aplicar" in sys.argv
    pub, pri = raizes()

    divergentes, ausentes = [], []
    for rel_pub, rel_pri in PARES:
        a, b = os.path.join(pub, rel_pub), os.path.join(pri, rel_pri)
        ra, rb = resumo(a), resumo(b)

        if ra is None and rb is None:
            continue                      # o par ainda nao existe; nada a fazer
        if ra is None:
            ausentes.append((rel_pub, "falta no publico"))
            continue
        if rb is None or not filecmp.cmp(a, b, shallow=False):
            if aplicar:
                os.makedirs(os.path.dirname(b) or ".", exist_ok=True)
                shutil.copyfile(a, b)
                print("copiado   %s  ->  %s/%s" % (rel_pub, PRIVADO, rel_pri))
            else:
                divergentes.append((rel_pub, rel_pri, ra, rb or "ausente"))
        else:
            if not aplicar:
                print("igual     %s  (%s)" % (rel_pub, ra))

    if ausentes:
        for rel, motivo in ausentes:
            print("ERRO      %s: %s" % (rel, motivo))
        return 1

    if divergentes:
        print()
        print("DIVERGENCIA em %d ficheiro(s):" % len(divergentes))
        for rel_pub, rel_pri, ra, rb in divergentes:
            print("  %-28s publico %s  !=  privado %s" % (rel_pub, ra, rb))
        print()
        print("Rode 'python sincronizar-comum.py --aplicar' para copiar do publico")
        print("para o privado. Se a alteracao boa estiver no privado, mova-a para o")
        print("publico primeiro -- ele e o canonico.")
        return 1

    if aplicar:
        print("sincronizado.")
    else:
        print()
        print("os %d ficheiro(s) comuns estao identicos nos dois repositorios." % len(PARES))
    return 0


if __name__ == "__main__":
    sys.exit(main())
