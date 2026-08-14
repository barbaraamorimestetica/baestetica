# O que é comum aos dois repositórios

O site (`baestetica`) e a ferramenta interna (`baestetica_private`) nasceram do
mesmo desenho e são repositórios separados — um público, um privado. Alguns
ficheiros precisam ser idênticos nos dois. Este documento diz quais, por que a
duplicação foi a escolha, e como ela é garantida.

## Os ficheiros comuns

| No público | No privado |
|---|---|
| `css/tokens.css` | `assets/tokens.css` |
| `css/componentes.css` | `assets/componentes.css` |
| `sincronizar-comum.py` | `sincronizar-comum.py` |
| `COMUM.md` | `COMUM.md` |

O lado **canônico é o público**. Não por hierarquia: só é preciso que um dos
dois seja, e o público é o que define a identidade visual da marca.

## Por que duplicar, e não compartilhar

As alternativas foram consideradas e descartadas:

- **Pacote publicado** — exigiria etapa de build. Não há Node na máquina, e as
  duas folhas de Tailwind já são geradas à mão justamente por isso.
- **Submódulo git** — funciona, inclusive no GitHub Pages. Mas traz um terceiro
  repositório para manter, e cada mudança de token passa a ser dois commits mais
  um `git submodule update` em cada lado.
- **Duplicação controlada** — o ficheiro existe nos dois, idêntico, e a cópia é
  verificada por máquina em vez de por memória. Zero infraestrutura nova.

A escolha só é defensável porque a verificação é mecânica. Duplicação sem
verificação é exatamente o que produziu a deriva que este trabalho corrigiu:
oito tons de marrom onde bastavam quatro, e a classe `.icon` copiada em doze
páginas.

## Como sincronizar

De dentro de qualquer um dos dois repositórios:

```bash
python sincronizar-comum.py
```

Confere e lista o que divergiu, sem tocar em nada. Para aplicar:

```bash
python sincronizar-comum.py --aplicar
```

Copia do público para o privado. **Se a alteração boa estiver no privado, mova-a
para o público primeiro** — o `--aplicar` sobrescreve o privado.

## A garantia

Cada repositório tem um hook de `pre-commit` que roda a conferência e **recusa o
commit se as cópias divergirem**. Não é possível commitar metade da alteração.

Hooks não viajam pelo `git clone`. Numa máquina nova, instale com:

```bash
python instalar-hooks.py
```

Se o hook não estiver instalado, a sincronização volta a depender de memória —
que é a situação que este arranjo existe para evitar.

## O que **não** é comum

As folhas compiladas do Tailwind: `css/site.css` (17 KB) no público e
`assets/tailwind.css` (23 KB) no privado. São conjuntos de classes diferentes,
ambas geradas a partir das páginas de cada lado. Juntá-las faria cada repositório
carregar o que não usa. O procedimento de regeração, esse sim, é o mesmo — está
descrito em `css/README.md`.
