# A galeria de resultados

A página `Resultados.html` não tem os posts escritos dentro dela. Ela lê uma
folha do Google Sheets e monta as seções sozinha, para a Bárbara acrescentar
um resultado sem mexer no site.

## A folha

```
https://docs.google.com/spreadsheets/d/1aO-AGvUPBe8y71UP7hlnF3a4dH24Jxq3dUv9f2QE6VI
```

Duas abas, ligadas pelo **nome do procedimento escrito igual nas duas**:

| aba | colunas | uma linha é |
|---|---|---|
| `Links` | `ID, Link, Procedimento` | um post do Instagram |
| `Procedimentos` | `Procedimento, Ordem, Descricao` | uma seção da página |

A `Ordem` manda na sequência das seções — 10, 20, 30… deixa espaço para
encaixar uma nova no meio sem renumerar as outras.

## Como acrescentar

**Um resultado novo:** uma linha em `Links`. Se o procedimento já existe, ele
aparece na seção certa no próximo carregamento da página.

**Um procedimento novo:** uma linha em `Procedimentos` com nome, ordem e
descrição, e depois os posts em `Links`. A seção aparece mesmo sem nenhum
post — mostra o texto e a nota *Resultados em breve*. É de propósito: anuncia
o serviço enquanto a primeira foto não chega.

**Um post que mostra vários procedimentos:** separe-os com `;` na mesma
célula. Ele não se repete numa seção por procedimento — vai inteiro para a
seção **Harmonização facial (mais de 1 procedimento)**, que existe para isso.

Esse nome está escrito nos dois lados: numa linha da aba `Procedimentos` e na
constante `COMBINADOS` do `js/galeria.js`. **Renomear um sem o outro** deixaria
quatro resultados sem seção — por isso, quando o nome não bate, o site devolve
esses posts às seções de cada procedimento e avisa no console. Repetir um post
é menos grave do que escondê-lo.

## O que o site faz quando algo corre mal

**A folha não responde.** A página traz duas seções escritas no HTML,
marcadas `data-piso`. Elas só são removidas depois de a folha chegar e passar
na conferência. Se falhar, ficam: a paciente vê alguma coisa, e o Google tem
texto para indexar. O motivo aparece no console.

**O nome de uma aba muda.** O endereço do Sheets aceita `?sheet=<nome>` e,
quando o nome não existe, devolve **HTTP 200 com a primeira aba**. Foi medido:
pedimos `NaoExiste` e vieram os links. Por isso cada aba é conferida pelo
cabeçalho antes de ser usada — sem isso o site desenharia os links no lugar
das descrições, sem erro nenhum.

**Um procedimento em `Links` sem linha em `Procedimentos`.** Os posts ficam de
fora e o console diz quais e quantos. Não há seção sem título.

**Um embed morre** (post apagado, bloqueador de anúncios, Instagram fora do
ar). Quem trata é o `baEmbeds`, que já existia na página: troca o embed por um
cartão que leva ao Instagram. Cada caixa tem o seu próprio prazo de 15s — as
da galeria nascem quando entram no ecrã, e não podiam herdar o relógio de uma
que nasceu um minuto antes.

## O carrossel

Cada procedimento mostra um post de cada vez, e navega-se de lado. Empilhados,
os 19 embeds punham a página em 26.000px — só o Preenchimento Labial ocupava
8.400. Com o carrossel a página tem 8.600.

Que **há mais para ver** é dito de três maneiras, porque uma só não chega:

| | |
|---|---|
| a espreita | a borda do post seguinte fica à vista — o único sinal que sobra no telefone, onde as setas saem |
| as bolinhas | dizem quantos são e em qual se está, e levam a qualquer um |
| as setas | 44×44, desativam-se nas pontas |

Para leitor de ecrã há um texto que se atualiza: *"Resultado 3 de 7"*. Uma
seção com um post só não ganha nada disso.

A rolagem é nativa, com `scroll-snap`. No telefone o dedo já sabe fazer isto
sem código nenhum.

## Por que os embeds nascem tarde

São 19 posts. Criar 19 embeds de uma vez são 19 iframes com script próprio a
arrancar juntos — no telefone isso trava e gasta dados da paciente. Cada caixa
só vira embed quando a seção se aproxima do ecrã (`IntersectionObserver`, com
400px de antecedência).

## O que o Google lê

O conteúdo chega por JavaScript, **depois** do HTML — e o Googlebot executa
JavaScript, mas não sempre e não depressa. A `Resultados.html` é uma das três
páginas do sitemap, e o texto das dez seções é o maior do site.

Por isso o HTML traz uma **cópia escrita** de tudo, entre os marcadores
`<!-- galeria:inicio -->` e `<!-- galeria:fim -->`. São 6.000 caracteres de
texto indexável que não dependem de script nenhum. A mesma cópia é o que a
paciente vê se a folha não responder, e é o que o `js/galeria.js` substitui
quando ela responde.

```bash
python gerar-galeria.py            # mostra o que mudaria
python gerar-galeria.py --aplicar  # escreve no Resultados.html
```

**Correr antes de publicar, sempre que a folha mudar.** Sem isso o site
continua certo para quem tem JavaScript, e o Google fica a ver a versão
anterior.

A cópia **não** traz os `<blockquote>` do Instagram, e sim um link por post.
Se trouxesse, o `embed.js` podia processá-los antes de o `galeria.js` os
trocar, e os 18 embeds carregariam de uma vez — exatamente o que o
carregamento tardio existe para evitar. O link serve ao Google, a quem não tem
JavaScript e a quem usa leitor de ecrã.

## Ficheiros

| | |
|---|---|
| `js/galeria.js` | busca, confere, agrupa e desenha |
| `Resultados.html` | o piso, o `baEmbeds` e a CSP |

A CSP precisou de `connect-src https://docs.google.com` — um host, não `*`.

## Conferir

```bash
python conferir-classes.py
```

```bash
python conferir-largura.py     # o servidor tem de estar na pasta MÃE
```

O primeiro lê os `.js` que cada página carrega, e não só o HTML. Isso não era verdade
antes desta galeria: as classes criadas em JavaScript ficavam fora da
conferência **e** fora da folha do Tailwind — não pintavam e não davam erro.
Foi assim que o `flex-wrap` e o `last:mb-0` apareceram em falta.

```bash
python conferir-embeds.py      # quais posts do Instagram nao embutem
```

O `conferir-embeds.py` existe porque um post apagado, arquivado ou restrito
continua a responder **HTTP 200** — o Instagram devolve 200 até no muro de
login. O que denuncia é o iframe: quando o post não embute, ele nasce e
colapsa para uns poucos pixels, contra os 800–1000 de um post bom. Foi assim
que se descobriu o do Zigomático, e por acaso.

O `conferir-largura.py` mede transbordo lateral de 320 a 414px, por iframe —
o Chrome headless não aceita janela abaixo de 500px, então um screenshot de
375px é renderizado a 500 e recortado, o que parece corte de texto e não é.
Perdi três medições a perseguir esse fantasma.
