# Catalogo-Barbara-Amorim.pdf

O botão "Download do catálogo" serve um PDF **pré-gerado**, versionado aqui no
repositório. Antes ele era montado no navegador do visitante com o
`html2pdf.js`, o que trazia três problemas:

- **Travava em celular.** O `html2canvas` rodava com `scale: 3` sobre 4 páginas
  A4, o que dá um canvas de ~2380x13450 px — cerca de 128 MB só de bitmap, mais
  os clones internos. Em aparelhos de gama média a aba congelava ou abortava.
- **Qualidade pior.** A saída era uma imagem rasterizada da página: texto sem
  nitidez, não selecionável e não pesquisável.
- **900 KB de dependência.** O `html2pdf.bundle.min.js` era baixado por todo
  visitante do catálogo, mesmo quem nunca clicava no botão.

O PDF atual tem 4 páginas A4, texto vetorial (selecionável e pesquisável) e
540 KB. O download é instantâneo e não depende de JavaScript.

## Como regerar

A fonte é [`catalogo-impressao.html`](catalogo-impressao.html) — o mesmo layout
A4 que antes ficava escondido dentro de `catalogo.html`. Ele usa as imagens de
`img/print/`, que são variantes JPEG dimensionadas para impressão.

1. Sirva o site localmente (o `file://` também funciona, mas o servidor evita
   surpresas com caminhos):

   ```bash
   python -m http.server 8765 --directory . --bind 127.0.0.1
   ```

2. Gere o PDF com o Chrome em modo headless:

   ```bash
   chrome --headless=new --disable-gpu --no-pdf-header-footer --virtual-time-budget=12000 --print-to-pdf=Catalogo-Barbara-Amorim.pdf http://127.0.0.1:8765/catalogo-impressao.html
   ```

   No Windows o executável costuma estar em
   `C:\Program Files\Google\Chrome\Application\chrome.exe`.

3. Confira: 4 páginas, A4 (595x842 pt), e o texto deve dar para selecionar.

## Por que as imagens de `img/print/`

O Chrome embute imagens sem perdas no `--print-to-pdf`. Com os `.webp` do site,
o PDF saía com 3,9 MB. Apontando para JPEGs de ~560 px (`img/print/*.jpg`), o
Chrome repassa o JPEG direto para dentro do PDF e o arquivo cai para 540 KB,
sem diferença visível numa folha A4.

O logotipo é a exceção: é PNG, não JPEG. O original tem fundo `(254,254,254)`,
que contra o branco puro da folha aparecia como um quadrado acinzentado em volta
da marca. O `img/print/logo-barbara-amorim.png` tem esse quase-branco achatado
em branco puro, e fica em PNG para o JPEG não reintroduzir a variação.

## Se alterar o catálogo

Editar `catalogo.html` **não** atualiza o PDF. As duas páginas têm o conteúdo
duplicado: a grade responsiva do site e o layout A4 da versão impressa. Ao
mexer em textos ou procedimentos, atualize as duas e regere o PDF.
