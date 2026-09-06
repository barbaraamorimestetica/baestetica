// O que fazer quando um embed do Instagram nao vem.
//
// Cada caixa [data-embed-instagram] reserva 500px de altura a espera do embed.
// Se ele nao vier, esse espaco fica em branco -- e ha tres formas de ele nao
// vir:
//
//   1. o post foi removido, ficou privado ou nao e embutivel: o embed.js
//      carrega, cria o iframe, e o iframe colapsa para uns poucos pixels;
//   2. o embed.js nao carrega (bloqueador de anuncios, rede da operadora,
//      Instagram fora do ar): nao chega a existir iframe nenhum;
//   3. a rede esta lenta e o embed ainda vem -- so que depois.
//
// Por isso nao basta varrer os iframes uma vez, num prazo fixo: no caso 2 nao
// ha iframe para varrer, e no caso 3 varrer cedo demais troca por um cartao um
// embed que ia funcionar.
//
// Vive num arquivo proprio porque as duas paginas que embutem Instagram
// precisam dele: a Resultados e a inicial.
window.baEmbeds = (function () {
    // Cada caixa [data-embed-instagram] reserva 500px de altura à espera
    // do embed. Se ele não vier, esse espaço fica em branco na página --
    // e há três formas de ele não vir:
    //
    //   1. o post foi removido ou ficou privado: o embed.js carrega, cria
    //      o iframe, e o iframe colapsa para uns poucos pixels;
    //   2. o embed.js não carrega (bloqueador de anúncios, rede da
    //      operadora, Instagram fora do ar): não chega a existir iframe
    //      nenhum, e o blockquote vazio fica lá;
    //   3. a rede está lenta e o embed ainda vem -- só que depois.
    //
    // Por isso não basta varrer os iframes uma vez, num prazo fixo: no
    // caso 2 não há iframe para varrer, e no caso 3 varrer cedo demais
    // troca por um cartão um embed que ia funcionar. Aqui reavaliamos as
    // caixas de meio em meio segundo e só desistimos no fim do prazo --
    // ou na hora, se o próprio script falhar ao carregar.
    var PRAZO = 15000;
    var INTERVALO = 500;
    var ALTURA_MINIMA = 120;   // abaixo disto o iframe colapsou

    // QUANTO SE ESPERA DEPOIS DE O IFRAME TERMINAR DE CARREGAR.
    //
    // O PRAZO de 15s existe para o caso em que nao ha iframe nenhum -- e ai
    // nao ha o que medir, so o relogio. Mas quando o iframe existe e ja
    // disparou o `load`, a resposta do Instagram CHEGOU: se ele continua com
    // dois pixels de altura, nao vai crescer mais.
    //
    // Esperar os 15s nesse caso e fazer a paciente olhar um retangulo branco
    // vazio por quinze segundos -- foi exatamente o que o Gabriel viu na
    // seccao do Bioestimulador, e com razao: ele parece defeito.
    //
    // Os 2s de folga sao para o redimensionamento: o embed.js mede o conteudo
    // e manda a altura por postMessage DEPOIS do load, e medir no instante do
    // load pegaria todo embed ainda pequeno.
    var FOLGA_APOS_CARREGAR = 2000;

    var pendentes = [];
    var inicio = 0;
    var timer = null;
    var iniciado = false;
    var falhou = false;

    function temEmbedVivo(caixa) {
var frame = caixa.querySelector('iframe.instagram-media');
return !!frame && frame.getBoundingClientRect().height > ALTURA_MINIMA;
    }

    // O iframe nao existe quando a caixa entra na lista: quem o cria e o
    // embed.js, e so depois de adotar o blockquote. Por isso a escuta e posta
    // na primeira rodada em que ele aparecer, e uma vez so.
    //
    // O `load` de um iframe de outro dominio CHEGA ao pai -- o que nao chega e
    // o conteudo. Aqui basta saber que terminou.
    function escutarCarregamento(caixa) {
var frame = caixa.querySelector('iframe.instagram-media');
if (!frame || frame.__baEscutado) { return; }
frame.__baEscutado = true;
frame.addEventListener('load', function () {
    caixa.__baCarregou = Date.now();
});
    }

    function parar() {
if (timer) { clearInterval(timer); timer = null; }
    }

    function mostrarCartao(caixa) {
// A ALTURA RESERVADA TEM DE SAIR JUNTO.
//
// Cada caixa reserva 500px a espera do embed, e a reserva vive no CSS --
// `.carrossel-slide { min-height: 500px }`. Antes esta linha removia uma
// classe do Tailwind, `min-h-[500px]`, que nao esta em HTML nenhum: sobrou
// de uma marcacao anterior. O cartao aparecia dentro de uma moldura de meio
// metro de vazio, e a seccao parecia quebrada -- que e o oposto do que ele
// existe para fazer.
caixa.classList.add('sem-embed');

// O DESTINO E O POST, e nao o perfil.
//
// Quem chega ate aqui quer ver AQUELE resultado. Mandar para a conta obriga
// a procurar entre cem publicacoes -- e o post abre normalmente para quem
// esta com sessao iniciada, que e o caso comum de quem usa o Instagram no
// telefone.
var destino = caixa.getAttribute('data-permalink')
    || 'https://instagram.com/barbaraamorimestetica';

var endereco = caixa.getAttribute('data-foto');
caixa.innerHTML = '';

// SEM FOTO: o cartao de sempre -- uma frase, um botao e o endereco escrito.
if (!endereco) {
    var cartao = document.createElement('div');
    cartao.className = 'cartao-sem-embed';
    // So o desenho vai por innerHTML: e texto fixo deste arquivo. O que vem
    // da planilha entra pelo DOM, onde nao ha como uma aspa solta fechar um
    // atributo e o resto virar marcacao.
    cartao.innerHTML = '<span class="cartao-sem-embed-icone" aria-hidden="true">'
        + '<svg class="icon tinta-marca text-3xl mb-3" width="448" height="512" viewBox="0 0 448 512" xmlns="http://www.w3.org/2000/svg" aria-hidden="true"><path d="M224.1 141c-63.6 0-114.9 51.3-114.9 114.9s51.3 114.9 114.9 114.9S339 319.5 339 255.9 287.7 141 224.1 141zm0 189.6c-41.1 0-74.7-33.5-74.7-74.7s33.5-74.7 74.7-74.7 74.7 33.5 74.7 74.7-33.6 74.7-74.7 74.7zm146.4-194.3c0 14.9-12 26.8-26.8 26.8-14.9 0-26.8-12-26.8-26.8s12-26.8 26.8-26.8 26.8 12 26.8 26.8zm76.1 27.2c-1.7-35.9-9.9-67.7-36.2-93.9-26.2-26.2-58-34.4-93.9-36.2-37-2.1-147.9-2.1-184.9 0-35.8 1.7-67.6 9.9-93.9 36.1s-34.4 58-36.2 93.9c-2.1 37-2.1 147.9 0 184.9 1.7 35.9 9.9 67.7 36.2 93.9s58 34.4 93.9 36.2c37 2.1 147.9 2.1 184.9 0 35.9-1.7 67.7-9.9 93.9-36.2 26.2-26.2 34.4-58 36.2-93.9 2.1-37 2.1-147.8 0-184.8zM398.8 388c-7.8 19.6-22.9 34.7-42.6 42.6-29.5 11.7-99.5 9-132.1 9s-102.7 2.6-132.1-9c-19.6-7.8-34.7-22.9-42.6-42.6-11.7-29.5-9-99.5-9-132.1s-2.6-102.7 9-132.1c7.8-19.6 22.9-34.7 42.6-42.6 29.5-11.7 99.5-9 132.1-9s102.7-2.6 132.1 9c19.6 7.8 34.7 22.9 42.6 42.6 11.7 29.5 9 99.5 9 132.1s2.7 102.7-9 132.1z"/></svg>' + '</span>';
    var frase = document.createElement('p');
    frase.className = 'cartao-sem-embed-frase';
    frase.textContent = 'Este resultado abre no Instagram.';
    cartao.appendChild(frase);
    var botao = document.createElement('a');
    botao.href = destino;
    botao.target = '_blank';
    botao.rel = 'noopener';
    botao.className = 'botao-marca cartao-sem-embed-botao';
    botao.textContent = 'Ver a publicação';
    cartao.appendChild(botao);
    caixa.appendChild(cartao);
    return;
}

// COM FOTO: A MOLDURA DE POST.
//
// A foto sozinha, com uma frase embaixo, nao se lia como resultado do
// Instagram -- lia-se como uma imagem qualquer com um aviso. Aqui ela vem
// na forma que a paciente reconhece: conta em cima, imagem no meio, link
// para o post embaixo. E a mesma arrumacao do embed que nao pode carregar.
//
// O QUE NAO ENTRA: a fila de coracao, comentario, compartilhar e salvar.
// Ali eles seriam desenho -- botao que nao faz nada e pior do que botao que
// nao existe, e o clique perdido ensina a nao clicar no resto.
//
// AS CORES SAO AS DA CASA, e nao o azul do Instagram. A arrumacao e o que
// faz a caixa ser reconhecida; a cor faria dela a unica coisa azul da
// pagina.
// Escrito uma vez: o avatar, o nome e o botao levam todos ao mesmo lugar, e
// tres copias do endereco divergiriam no dia em que a conta mudasse de nome.
var PERFIL = 'https://instagram.com/barbaraamorimestetica';

var moldura = document.createElement('figure');
moldura.className = 'cartao-instagram';

var topo = document.createElement('header');
topo.className = 'cartao-instagram-topo';
// O AVATAR E O NOME, DENTRO DE UM LINK SO.
//
// Os dois levam ao perfil, e num link so -- e nao um cada. Dois links lado a
// lado para o mesmo lugar sao dois anuncios do mesmo destino para quem navega
// por leitor de tela ou por tabulacao, e a segunda parada nao leva a nada
// novo. Aqui o alvo clicavel e a fila inteira: retrato e nome.
var quem = document.createElement('a');
quem.className = 'cartao-instagram-quem';
quem.href = PERFIL;
quem.target = '_blank';
quem.rel = 'noopener';

// O ANEL COLORIDO precisa de um elemento proprio: ele e o degrade por tras, e
// o avatar por cima com um vao branco entre os dois. Numa borda so nao da --
// `border` nao aceita degrade.
var anel = document.createElement('span');
anel.className = 'cartao-instagram-anel';
var avatar = document.createElement('img');
avatar.className = 'cartao-instagram-avatar';
// O logotipo do proprio site. As paginas todas vivem na raiz, entao o
// caminho relativo vale nas duas que embutem Instagram.
avatar.src = 'img/logo-barbara-amorim.webp';
// alt vazio de proposito: o nome ao lado, dentro do mesmo link, ja e o texto
// do link. Um alt aqui faria o link ser anunciado duas vezes.
avatar.alt = '';
anel.appendChild(avatar);
quem.appendChild(anel);

var conta = document.createElement('span');
conta.className = 'cartao-instagram-conta';
conta.textContent = 'barbaraamorimestetica';
quem.appendChild(conta);
topo.appendChild(quem);
var perfil = document.createElement('a');
perfil.className = 'cartao-instagram-perfil';
perfil.href = PERFIL;
perfil.target = '_blank';
perfil.rel = 'noopener';
perfil.textContent = 'Ver perfil';
topo.appendChild(perfil);
moldura.appendChild(topo);

var foto = document.createElement('img');
foto.className = 'resultado-foto';
foto.src = endereco;
foto.alt = caixa.getAttribute('data-foto-alt') || '';
foto.loading = 'lazy';
// O Drive olha o referenciador em alguns caminhos; sem ele mandado, ha uma
// variavel a menos entre o teste local e o site no ar.
foto.referrerPolicy = 'no-referrer';
// Se a imagem nao vier -- acesso revogado, endereco trocado, Drive a
// estrangular -- a moldura sai inteira e fica o cartao de sempre. Nunca um
// icone de imagem quebrada, que e pior do que nao ter foto.
foto.onerror = function () {
    caixa.removeAttribute('data-foto');
    mostrarCartao(caixa);
};
moldura.appendChild(foto);

// SEM O ENDERECO ESCRITO.
//
// Ele entrou quando o cartao era so uma frase solta, para dizer que havia um
// destino ali. Com a moldura, o "Ver mais no Instagram" ja e o destino, e
// escrever `instagram.com/p/Dc5GkZ8xZwo` embaixo dele repete a mesma coisa em
// linguagem de maquina -- e um codigo de onze letras nao diz nada a quem le.
// O PE, EM DOIS BLOCOS SEPARADOS, como o do Instagram.
//
// Primeiro o "Ver mais no Instagram", sozinho e com filete embaixo. Depois a
// conta e a legenda. E a ordem do embed de verdade, e a que a paciente
// reconhece: o link e a saida, e a legenda e a leitura.
var pe = document.createElement('figcaption');
pe.className = 'cartao-instagram-pe';

var linhaDoLink = document.createElement('div');
linhaDoLink.className = 'cartao-instagram-saida';
var maisNo = document.createElement('a');
maisNo.href = destino;
maisNo.target = '_blank';
maisNo.rel = 'noopener';
maisNo.className = 'cartao-instagram-link';
maisNo.textContent = 'Ver mais no Instagram';
linhaDoLink.appendChild(maisNo);
pe.appendChild(linhaDoLink);

// A LEGENDA, quando a planilha tem uma.
//
// O `\n` que se escreve na celula chega aqui como duas letras, barra e n -- o
// CSV nao carrega quebra de linha dentro de campo sem ela vir citada. Cada
// trecho vira um paragrafo proprio, que e o que a barra e o n queriam dizer.
//
// textContent em cada paragrafo, e nao innerHTML no conjunto: o texto vem da
// planilha, e um `<` perdido no meio de uma legenda nao pode virar marcacao.
var legenda = caixa.getAttribute('data-legenda');
if (legenda) {
    var corpo = document.createElement('div');
    corpo.className = 'cartao-instagram-corpo';

    // A conta OUTRA VEZ, em negrito, antes da legenda. E assim no embed de
    // verdade: em cima ela identifica o autor do post, aqui ela abre a fala.
    var quem = document.createElement('span');
    quem.className = 'cartao-instagram-autor';
    quem.textContent = 'barbaraamorimestetica';
    corpo.appendChild(quem);

    var texto = document.createElement('div');
    texto.className = 'cartao-instagram-legenda';
    legenda.split(/\\n|\r?\n/).forEach(function (trecho) {
        var t = trecho.trim();
        if (!t) { return; }
        var p = document.createElement('p');
        p.textContent = t;
        texto.appendChild(p);
    });
    if (texto.childNodes.length) {
        corpo.appendChild(texto);
        pe.appendChild(corpo);
    }
}

moldura.appendChild(pe);

caixa.appendChild(moldura);
    }

    function desistirDeTodas() {
parar();
pendentes.forEach(mostrarCartao);
pendentes = [];
    }

    // O prazo e de cada caixa, e nao da pagina: com a galeria vinda
    // da folha (js/galeria.js) as caixas nascem quando a seccao entra
    // na tela, e uma caixa criada agora nao pode herdar o relogio de
    // uma que nasceu ha um minuto.
    function rodada() {
var agora = Date.now();
pendentes = pendentes.filter(function (caixa) {
    if (!caixa.isConnected) { return false; }   // seccao trocada
    if (temEmbedVivo(caixa)) { return false; }
    escutarCarregamento(caixa);
    // O IFRAME JA CARREGOU E CONTINUA PEQUENO: a resposta chegou, e e nao.
    // Nao ha por que esperar o resto do prazo.
    if (caixa.__baCarregou
        && agora - caixa.__baCarregou >= FOLGA_APOS_CARREGAR) {
        mostrarCartao(caixa);
        return false;
    }
    if (agora - (caixa.__baInicio || agora) >= PRAZO) {
        mostrarCartao(caixa);
        return false;
    }
    return true;
});
if (!pendentes.length) { parar(); }
    }

    function vigiar(caixas) {
var agora = Date.now();
caixas.forEach(function (caixa) {
    if (pendentes.indexOf(caixa) === -1) {
        caixa.__baInicio = agora;
        pendentes.push(caixa);
    }
});
if (!pendentes.length) { return; }
if (falhou) { desistirDeTodas(); return; }
if (!timer) { timer = setInterval(rodada, INTERVALO); }
    }

    function iniciar() {
iniciado = true;
vigiar(Array.prototype.slice.call(
    document.querySelectorAll('[data-embed-instagram]')));
    }

    // Chamado pelo onerror do embed.js. Pode chegar antes de iniciar(),
    // e nesse caso só deixa a marca: quem trata é o próprio iniciar().
    function aoFalharScript() {
falhou = true;
if (iniciado) { desistirDeTodas(); }
    }

    if (document.readyState === 'loading') {
document.addEventListener('DOMContentLoaded', iniciar);
    } else {
iniciar();
    }

    // acompanhar() e o que a galeria dinamica chama para as caixas
    // que cria depois do arranque
    // cartao() e para quem JA SABE que o post nao embute -- a galeria, quando
    // o post esta no js/sem-embed.js. Sem ele, a unica forma de chegar ao
    // cartao era esperar a medicao falhar, que e o que aquela lista existe
    // para poupar.
    return { aoFalharScript: aoFalharScript, acompanhar: vigiar,
             cartao: mostrarCartao };
})();
