# O rodapé das folhas exportadas

Toda folha que vira PDF — nos dois repositórios — termina com o mesmo rodapé.
Este documento diz qual é, onde está, e por que tem a forma que tem.

## O rodapé

```
[tel] (22) 99940 8603   [insta] @barbaraamorimestetica   [mail] barbaraamorimesteticaa@gmail.com      Página X/Y
Bárbara Amorim · Enfermeira Esteta · COREN-RJ 543.324
```

Duas linhas, a 9px, com a credencial em `tinta-suave`. O bloco começa com o
comentário `<!-- Rodape unico das folhas exportadas -- ver RODAPE.md -->`, que
é o que permite contá-los por máquina.

## Onde está

| Repositório | Ficheiro | Folhas |
|---|---|---|
| público | `catalogo-impressao.html` | 4 |
| privado | `termos-consentimento.html` | 4 (três documentos) |
| privado | `ficha-anamnese.html` | 2 |
| privado | `planner-anual.html` | 2 |
| privado | `tabela-precos.html` | 2 |
| privado | `pos-procedimento.html` | 1 |

São **15 folhas**. As quatro do termo são três documentos distintos, então a
numeração reinicia: `1/2`, `2/2` para o TCLE, e depois `1/1` para o de imagem
e `1/1` para o promocional.

## Por que estas escolhas

**9px, e não 8 nem 12.** As folhas dos documentos usavam 8px e as do catálogo
12px — para a mesma folha física de 210×296mm. Não era escala diferente, era
divergência. O 9px fica no meio e cabe nas folhas mais apertadas.

**Duas linhas, e não uma.** A linha de contactos já estava no limite. Ao
acrescentar o marcador de versão a essa linha, o telefone partiu em duas e o
e-mail colou no número da página — **e só no PDF**, porque na tela sobrava
largura. A credencial vai por baixo justamente para não repetir isso.

**`Página X/Y`, e não `Página X de Y`.** As duas formas conviviam. Escolheu-se
a curta porque disputa menos espaço com os contactos.

**Os `<svg>` levam `width` e `height`.** Sem dimensão intrínseca o
html2canvas não desenha o ícone no PDF, sem erro nenhum. O motivo completo
está no `componentes.css`, ao lado da regra `.icon`.

## O que não entra

**A versão do documento.** Chegou a sair impressa e foi retirada: espremia a
linha de contactos. O registo de versões vive no `CONSULTA-JURIDICA.md` (no
privado) e no histórico do git, que é onde ele é fiável. Para saber qual texto
foi assinado, cruza-se a data da assinatura com a tabela de versões.

**Conteúdo da própria folha.** A folha 1 do planner tem uma instrução de
preenchimento — *marque com um "X" no mês planejado*. Isso é conteúdo, não
rodapé: ficou numa linha acima, e o rodapé padrão entra por baixo.

## Como conferir

```bash
python conferir-rodape.py
```

Confere as 15 folhas: se todas têm o rodapé, se a numeração está certa, e se
sobrou algum rodapé antigo. Roda de dentro de qualquer um dos dois
repositórios e olha os dois, como os outros verificadores.
