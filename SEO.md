# O sitemap e o Google Search Console

## O estado, em duas linhas

O sitemap local está correto e consistente. **O publicado não existe** — a URL
devolve 404, porque o `sitemap.xml` nasceu num commit que nunca foi enviado.

```bash
python conferir-sitemap.py --ar
```

Confere o local contra as páginas e diz o que está no ar. Roda sem rede no modo
sem `--ar`.

## Por que o envio tem de ser à mão

O site é um **project page** do GitHub Pages, servido em
`barbaraamorimestetica.github.io/baestetica/`. Os robôs só procuram o
`robots.txt` na raiz do host — `barbaraamorimestetica.github.io/robots.txt` —
que sairia de outro repositório. O `robots.txt` deste repositório responde em
`/baestetica/robots.txt` e é simplesmente ignorado, então a linha `Sitemap:`
dele não declara nada. Ver o comentário no topo daquele ficheiro.

Medido: a raiz do host devolve **404**, tanto em `/` como em `/robots.txt`. Isso
tem um lado bom — sem `robots.txt` na raiz, não há restrição de rastreio
nenhuma no host, e o `/baestetica/` fica livre por omissão.

## A ordem importa

O envio ao Search Console atua no **site publicado**, não no que está aqui.
Enviar enquanto a URL devolve 404 falha, e a falha fica registrada na conta.

1. Publicar o repositório.
2. Confirmar que `https://barbaraamorimestetica.github.io/baestetica/sitemap.xml`
   devolve 200 — o `--ar` acima diz isso.
3. Só então enviar.

## O envio

### A propriedade tem de ser de prefixo de URL, com o caminho

No Search Console, ao criar a propriedade, há duas opções. **Domínio** não serve:
ela verifica por DNS, e o domínio `github.io` não é seu.

Use **prefixo de URL** e escreva o endereço **com o caminho**:

```
https://barbaraamorimestetica.github.io/baestetica/
```

Sem o `/baestetica/`, a propriedade passa a ser do host inteiro — e aí a
verificação por ficheiro pediria um ficheiro na raiz do host, que vem de um
repositório que não existe (é o 404 medido acima).

### A verificação

Com a propriedade escopada no caminho, as opções que funcionam são:

- **Google Analytics** — as páginas já carregam o `gtag.js` com o
  `G-QWMWZ5SYWP`. Se a conta do Search Console for a mesma que administra essa
  propriedade do Analytics, esta é a via mais curta e não precisa de mexer no
  repositório.
- **Etiqueta HTML** — um `<meta name="google-site-verification" content="...">`
  no `<head>` do `index.html`. Precisa de commit e de publicação.
- **Ficheiro HTML** — um `google‹token›.html` na raiz do repositório, que
  responde em `/baestetica/google‹token›.html`. Também precisa de publicação.

Se escolher etiqueta ou ficheiro, cuidado com a **CSP**: o `index.html` tem
`Content-Security-Policy` restritiva. Uma `<meta>` de verificação não carrega
nada e passa sem alteração; um ficheiro de verificação é servido isolado e
também passa.

### O sitemap

Em **Sitemaps**, no menu lateral, o campo já vem preenchido com o prefixo da
propriedade. Escreva apenas:

```
sitemap.xml
```

O sitemap tem de estar **dentro** do caminho da propriedade, e está:
`/baestetica/sitemap.xml`.

## O que o sitemap declara, e o que fica de fora

Três URLs, e o `conferir-sitemap.py` verifica que cada uma existe, não tem
`noindex`, tem `canonical` idêntico ao caractere, e tem `lastmod` igual à última
alteração no git.

| Fora do sitemap | Por quê |
|---|---|
| `catalogo-impressao.html` | `noindex` — é a fonte do PDF, não uma página de destino |
| `Catálogo de Procedimentos.html` | `noindex` — redireciona um endereço antigo |
| `404.html` | página de erro |

As três são verificadas, não presumidas: se alguma perder o `noindex`, o
`conferir-sitemap.py` passa a acusá-la como indexável e fora do sitemap.

## Depois de enviar

O Search Console leva de horas a dias para processar. O que olhar:

- **Sitemaps** → estado `Com êxito` e o número de URLs descobertas (3).
- **Páginas** → o motivo de cada URL não indexada. Num site novo, `Descoberta —
  atualmente não indexada` é normal e resolve-se com o tempo.
- Não é preciso reenviar o sitemap a cada alteração. O Google volta a buscá-lo
  sozinho. Reenviar só faz sentido se o ficheiro mudar de nome ou de lugar.

## Quando o site ganhar domínio próprio

Com um `CNAME` no repositório, ele passa a ser servido na raiz do domínio. Aí:

- o `robots.txt` deste repositório passa a ser lido, e a linha `Sitemap:` dele
  passa a valer sozinha — é por isso que o ficheiro ficou;
- as URLs absolutas mudam **em todo lugar**: no `sitemap.xml`, nos `canonical`
  de cada página, nas `og:url` e nos caminhos absolutos do `404.html`. O
  `conferir-sitemap.py` acusa a divergência entre `canonical` e sitemap, mas o
  `BASE` no topo dele também precisa de ser trocado;
- vale criar uma propriedade nova no Search Console e manter a antiga, para não
  perder o histórico.
