# css/site.css

Folha de estilos gerada. **Não editar à mão.**

Contém o Tailwind CSS v3.4.17 compilado apenas com as classes que as páginas
deste site realmente usam (17 KB, contra ~110 KB de JavaScript que o
`cdn.tailwindcss.com` carregava para compilar tudo no navegador do visitante).

## Quando é preciso regerar

Sempre que uma classe **nova** do Tailwind for usada em qualquer página. Se a
classe não estiver nesta folha, ela não tem efeito nenhum — e falha em silêncio,
sem erro no console. O mesmo vale para uma classe que **não existe** no Tailwind:
`text-md`, por exemplo, parece plausível mas não faz parte da escala (que vai de
`text-sm` para `text-base` e `text-lg`), e por isso também não gera regra.

Atenção às classes que só existem dentro de JavaScript, e que uma varredura do
HTML não encontra:

- strings de `innerHTML` — hoje só o cartão alternativo do Instagram, em
  `Resultados.html`
- `classList.add()` / `classList.remove()` — hoje nenhuma; a única que havia
  saiu junto com o toast que existia em `catalogo.html`

Elas também precisam de entrar na regeração.

## Como regerar

Com Node disponível, o caminho normal é o Tailwind CLI:

```bash
npx tailwindcss@3.4.17 -i entrada.css -o css/site.css --minify
```

...com um `tailwind.config.js` que replique o tema (as cores estão no comentário
no topo de `site.css`) e `content` a apontar para `*.html`.

Sem Node — como foi o caso quando esta folha foi gerada — dá para extrair o CSS
que o próprio CDN produz em runtime:

1. Junte num único ficheiro HTML temporário o `<script src="https://cdn.tailwindcss.com">`,
   o bloco `tailwind.config` com o tema, e uma `<div>` cujo `class` contenha
   **todas** as classes usadas no site (incluindo as que só aparecem no JS).
2. Abra esse ficheiro num navegador. O CDN injeta um `<style>` com exactamente
   as utilidades correspondentes, mais o preflight.
3. Grave `document.querySelector('style').textContent` neste ficheiro e
   mantenha o comentário de cabeçalho.

## Os outros ficheiros desta pasta

`site.css` é o único gerado. Os outros três são escritos à mão:

- **`tokens.css`** — paleta nomeada, tipografia, escala base. **Comum ao
  repositório privado**: depois de mexer, corra `python sincronizar-comum.py`.
  Ver `COMUM.md`.
- **`componentes.css`** — peças que os dois repositórios desenham igual
  (`.botao-marca`, `.icon`, `.serif`, cabeçalho no telefone, `.no-print`).
  **Também comum.**
- **`paginas.css`** — peças só deste site: `body`, `.luxury-light-bg`,
  `.rodape`. Não é comum, e não deve ser: o privado não tem rodapé de contacto.

Cor não se escreve mais dentro de nome de classe. Em vez de `text-[#AA746B]`,
use `.tinta-forte`, `.tinta-marca`, `.tinta-texto` ou `.tinta-suave` — o nome
diz o papel, e a paleta muda num lugar só. Foi assim que 61 reprovas de
contraste apareceram sem ninguém notar: o hexadecimal estava espalhado por 66
elementos e trocá-lo queria dizer caçá-lo página por página.

## Ordem no `<head>`

```
site.css  →  tokens.css  →  componentes.css  →  paginas.css  →  <style> da página
```

`site.css` vem **primeiro**: o preflight do Tailwind faz reset de margens,
bordas e tipografia, e tudo o que vem depois conta com isso. O `<style>` de cada
página vem **último**, para poder sobrepor-se ao que é comum sem editar o comum.

No repositório privado a ordem é diferente de propósito — lá o `tailwind.css`
vem no fim e ganha do `<style>` da página. A tabela está em `COMUM.md`.
