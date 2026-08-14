# A pasta `css/`

## `site.css` — gerada. **Não editar à mão.**

Tailwind CSS v3.4.17 compilado apenas com as classes que as páginas deste site
realmente usam (17 KB, contra ~110 KB de JavaScript que o `cdn.tailwindcss.com`
carregava para compilar tudo no navegador do visitante).

**O procedimento de regeração está em [`../TAILWIND.md`](../TAILWIND.md)**, que é
comum aos dois repositórios. Antes ele estava escrito aqui e outra vez no
cabeçalho de `assets/tailwind.css` do repositório privado, com palavras
diferentes — que é como uma das duas versões fica desatualizada sem ninguém ver.

Para saber se falta alguma classe nesta folha, de dentro da raiz do repositório:

```bash
python conferir-classes.py
```

## Os outros três — escritos à mão

- **`tokens.css`** — paleta nomeada, tipografia, escala base. **Comum ao
  repositório privado**: depois de mexer, corra `python sincronizar-comum.py`.
  Ver [`../COMUM.md`](../COMUM.md).
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
vem no fim e ganha do `<style>` da página. A tabela está em `../COMUM.md`.
