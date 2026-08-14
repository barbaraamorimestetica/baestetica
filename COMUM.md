# O que é comum aos dois repositórios

O site (`baestetica`) e a ferramenta interna (`baestetica_private`) nasceram do
mesmo desenho e são repositórios separados — um público, um privado. Alguns
ficheiros precisam ser idênticos nos dois. Este documento diz quais, por que a
duplicação foi a escolha, e como ela é garantida.

## Os ficheiros comuns

| No público | No privado | O que é |
|---|---|---|
| `css/tokens.css` | `assets/tokens.css` | paleta, tipografia, escala base |
| `css/componentes.css` | `assets/componentes.css` | as peças que os dois desenham igual |
| `css/fontes.css` | `assets/fontes.css` | as `@font-face` da Montserrat e da Playfair |
| `sincronizar-comum.py` | idem | confere e copia |
| `conferir-classes.py` | idem | classe usada sem regra |
| `conferir-contraste.py` | idem | contraste, estados e anel de foco |
| `regerar-tailwind.py` | idem | regera a folha compilada |
| `COMUM.md` | idem | este documento |
| `TAILWIND.md` | idem | o procedimento do Tailwind |

O `conferir-sitemap.py` e o `SEO.md` ficam **só no público**: a ferramenta interna
não é indexada e não tem sitemap.

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

## Os três verificadores

Rodam de dentro de qualquer um dos dois repositórios e olham os **dois**:

```bash
python sincronizar-comum.py     # os comuns divergiram?
python conferir-classes.py      # há classe usada sem regra em folha nenhuma?
python conferir-contraste.py    # há texto, estado ou anel de foco a reprovar?
```

Os três descobrem as páginas com `os.listdir`, e não por lista escrita à mão. Isso
não é detalhe: uma página do site — o `Catálogo de Procedimentos.html`, que
redireciona um endereço antigo — ficou fora de **todas** as medições feitas à mão
neste projeto, e escondia um link a 3,87:1.

O `conferir-contraste.py` mede três coisas, e as três por um motivo:

- **repouso**, a cor computada de todo texto contra o fundo efetivo;
- **estados**, lendo as regras de `:hover` e `:focus` das folhas — o medidor
  anterior lia só o repouso, e dois *hovers* defeituosos passaram invisíveis;
- **anel de foco** contra o fundo do elemento em volta (WCAG 1.4.11, 3:1).

Página que redireciona não dá para medir num iframe, porque ele segue o
redirecionamento e mede o destino. Essas são conferidas por leitura do ficheiro.

## O que está em cada ficheiro comum

`tokens.css` — a paleta nomeada, a tipografia e a **escala base** (`html {
font-size: 16px }`). Antes a base estava declarada página a página e não batia:
18px em quatro páginas, 16px nas outras oito.

`fontes.css` — as declarações `@font-face` da Montserrat e da Playfair Display,
servidas do próprio repositório. Os `url()` são relativos ao ficheiro, e por isso
o **mesmo texto** funciona nos dois lados: em `css/fontes.css` aponta para
`css/fontes/`, em `assets/fontes.css` aponta para `assets/fontes/`.

Os 10 ficheiros `.woff2` (388 KB, só o subset `latin`) acompanham a folha mas não
entram na conferência: são binários imutáveis, baixados do Google Fonts e nunca
editados à mão. Quem os atualizar segue o procedimento no cabeçalho do
`fontes.css` e substitui os dois lados de uma vez.

`componentes.css` — as peças que os dois lados desenham igual, e só essas:
`.botao-marca` (3 usos no site, 9 na ferramenta), `.icon` (12 páginas, era a
regra mais duplicada do projeto), `.serif`, o cabeçalho no telefone, e o
`@media print { .no-print }`.

## O que **não** é comum

**As folhas compiladas do Tailwind:** `css/site.css` (17 KB) no público e
`assets/tailwind.css` (23 KB) no privado. São conjuntos de classes diferentes,
ambas geradas a partir das páginas de cada lado. Juntá-las faria cada repositório
carregar o que não usa. O procedimento de regeração, esse sim, é o mesmo — está
descrito em `css/README.md`.

**As peças de um lado só**, pelo mesmo motivo:

| Ficheiro | Onde | O que tem |
|---|---|---|
| `css/paginas.css` | só público | `body`, o fundo em degradê, o rodapé de contacto |
| `assets/documento.css` | só privado | o andaime da folha A4: papel, campo de preencher à mão, caixa de seleção, impressão |

O `documento.css` está ligado **apenas** na `ficha-anamnese` e no
`termos-consentimento`. Foi uma decisão medida, não descuido: as outras três
páginas de documento usam os mesmos nomes de classe sem nunca terem tido as
regras, e carregar o ficheiro nelas mudava o que já desenham — no
`tabela-precos`, `.logo-circle { width: 60px !important }` encolhia um logótipo
que hoje é dimensionado pelo `assets/logo.js`. Seria regressão disfarçada de
arrumação. As três regras que essas páginas realmente partilhavam ficaram nelas,
com o motivo escrito ao lado.

## A ordem no `<head>`

Os dois lados carregam na mesma ordem lógica, mas o Tailwind fica em pontos
diferentes, e isso é de propósito:

| | público | privado |
|---|---|---|
| 1 | `site.css` (Tailwind) | `tokens.css` |
| 2 | `tokens.css` | `componentes.css` |
| 3 | `componentes.css` | `documento.css` |
| 4 | `paginas.css` | `<style>` da página |
| 5 | `<style>` da página | `tailwind.css` |

No público o `<style>` da página ganha do Tailwind; no privado é o Tailwind que
ganha. Em ambos, o `<style>` da página ganha dos ficheiros comuns — é o que
permite a uma página sobrepor-se sem editar o comum.
