# O Tailwind nos dois repositórios

Os dois lados usam Tailwind CSS v3.4.17 **compilado à mão**, não o
`cdn.tailwindcss.com`. O CDN é um compilador em runtime: baixava ~110 KB de
JavaScript a cada abertura da página, e sem rede não sobrava layout nenhum.

Este documento é o procedimento **único**. Antes havia dois — um em
`css/README.md`, outro no cabeçalho de `assets/tailwind.css` — que diziam a
mesma coisa com palavras diferentes, o que é como uma delas fica desatualizada.

## O que muda de um lado para o outro

| | público (`baestetica`) | privado (`baestetica_private`) |
|---|---|---|
| Folha gerada | `css/site.css` (17 KB) | `assets/tailwind.css` (23 KB) |
| Onde entra no `<head>` | **primeiro**, antes de tudo | **último**, depois de tudo |
| Cores do tema | `roseGold` #C28E86, `roseAccent` #AA746B, `borderRose` #EACDCA, `bgBeige` #F6ECEB, `softGray` #F5F2F1, `darkText` #3D2D2B | `roseAccent` #AA746B, `roseDeep` #8F5C54, `borderRose` #EACDCA, `bgBeige` #F6ECEB |

As duas folhas **não** são comuns e não devem ser: cada uma contém só as classes
que as páginas daquele lado usam. Juntá-las faria cada repositório carregar o
que não usa. A ordem no `<head>` de cada lado está em [`COMUM.md`](COMUM.md).

O `roseDeep` (#8F5C54) existe só no tema privado. Foi por isso que a fase 1
precisou de o trazer ao site pelo `tokens.css`, como `.tinta-forte`: o tema
público não tinha nenhum tom de rosa que passasse a WCAG em texto pequeno.

## O modo de falhar

**Uma classe que não está na folha não tem efeito e não dá erro.** Não aparece
no console, não quebra nada, só não pinta. Vale também para classe que nem
existe no Tailwind: `text-md` parece plausível e não faz parte da escala (que
vai de `text-sm` para `text-base` e `text-lg`), e falha exatamente do mesmo
jeito. Esse `text-md` esteve numa página deste site sem que ninguém notasse.

Por isso existe a conferência mecânica:

```bash
python conferir-classes.py
```

Para cada página, junta as folhas que ela **realmente carrega** mais o `<style>`
dela, extrai todo seletor de classe definido, e compara com toda classe usada.
O que sobrar não pinta. Roda nos dois repositórios de uma vez, de dentro de
qualquer um dos dois, e não precisa de rede.

Ela sabe procurar nos lugares onde uma varredura simples do HTML não chega:

- strings de `innerHTML` e template literal
- **interpolação**: em `class="... ${x === 'A' ? 'text-green-700' : 'text-red-600'}"`
  as classes são as duas últimas, e `'A'` é dado. Sem separar isso, as duas
  classes de verdade passavam sem ser conferidas
- `classList.add()` / `.remove()` / `.toggle()` — no `toggle`, só o primeiro
  argumento é classe; o segundo é a força

Classes que existem só para o JavaScript agarrar não precisam de regra, e estão
numa lista no topo do script, **cada uma com o motivo escrito**. Sem o motivo, a
lista viraria tapete para esconder defeito.

## Quando é preciso regerar

Sempre que uma classe **nova** do Tailwind for usada em qualquer página. A
conferência acima diz quando. Não é preciso regerar quando uma classe deixa de
ser usada: a regra órfã fica na folha como bytes mortos, e isso é inofensivo.

## Como regerar

```bash
python regerar-tailwind.py            # mostra o que mudaria
python regerar-tailwind.py --aplicar  # escreve as duas folhas
```

**Não escreve por omissão**, de propósito: esta é a operação mais frágil do
projeto e o erro dela é silencioso. O modo de conferência lista os seletores que
entrariam e os que sairiam, para se poder olhar antes de aplicar.

O script faz o que o Tailwind CLI faria se houvesse Node: monta um HTML
temporário com o CDN pinado na versão, o tema, e uma `<div>` cujo `class` contém
todos os tokens usados; abre no Chrome headless; recolhe o `<style>` injetado; e
grava mantendo o cabeçalho de comentário. O caminho do HTML temporário é
impresso no fim, para se poder abrir e ver o que o CDN recebeu.

Os tokens saem do **mesmo extractor** que o `conferir-classes.py` usa — ele é
carregado pelo caminho, porque o nome tem hífen. Isso é deliberado: se os dois
lessem o HTML de maneira diferente, o gerador poderia deixar de fora uma classe
que a conferência procura, e a folha passaria a conferência com um buraco.

Com Node disponível, o caminho normal seria o CLI:

```bash
npx tailwindcss@3.4.17 -i entrada.css -o css/site.css --minify
```

...com um `tailwind.config.js` que replique o tema e `content` a apontar para
`*.html`.

### O tema encolheu

Depois de a cor sair dos nomes de classe, **nenhum** nome de cor do tema antigo
(`roseGold`, `roseAccent`, `roseDeep`, `borderRose`, `bgBeige`, `softGray`,
`darkText`) é usado em página nenhuma. O `tailwind.config` do script tem só as
duas famílias de fonte — que precisam de ficar, porque o *preflight* do Tailwind
põe a `fontFamily.sans` no `<html>` e o `.font-serif` é usado 83 vezes.

### Depois de regerar, prove que não quebrou

Regerar é a operação mais frágil deste projeto, e o erro é silencioso. Vale
comparar os estilos computados antes e depois:

1. `git archive HEAD | tar -x -C antes/` e sirva `antes/` e a árvore de trabalho
   **da mesma origem** (um `python -m http.server` com as duas como subpastas —
   origens diferentes barram o acesso ao `contentWindow` do iframe).
2. Num iframe por versão, percorra `querySelectorAll('*')` e compare
   `getComputedStyle` propriedade a propriedade.
3. O iframe tem de ser **mais largo que a folha mais larga** (o planner em
   paisagem tem 297mm = 1122px). Num iframe estreito o conteúdo reflui e a
   comparação inventa diferenças que não existem — foi o que aconteceu ao medir
   a 1100px.

Uma animação em curso (`.animate-spin`) aparece como diferença na matriz de
transformação. É a única diferença legítima.

## O `.font-serif` e o `.font-sans` do lado privado

Apontam para Playfair Display e Montserrat de propósito. Com as pilhas padrão do
Tailwind (Georgia, system-ui) eles sobrepunham as regras próprias das páginas,
porque lá a folha é carregada **depois** delas — era por isso que os títulos
nunca saíam em Playfair.

---

*Comum aos dois repositórios. Depois de mexer, rode `python sincronizar-comum.py`
— ver [`COMUM.md`](COMUM.md).*
