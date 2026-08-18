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
// Vive num ficheiro proprio porque as duas paginas que embutem Instagram
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

    var pendentes = [];
    var inicio = 0;
    var timer = null;
    var iniciado = false;
    var falhou = false;

    function temEmbedVivo(caixa) {
var frame = caixa.querySelector('iframe.instagram-media');
return !!frame && frame.getBoundingClientRect().height > ALTURA_MINIMA;
    }

    function parar() {
if (timer) { clearInterval(timer); timer = null; }
    }

    function mostrarCartao(caixa) {
caixa.classList.remove('min-h-[500px]');
caixa.innerHTML = '<a href="https://instagram.com/barbaraamorimestetica" target="_blank" rel="noopener"'
        + ' class="w-full max-w-[540px] border borda-marca rounded-xl p-8 flex flex-col items-center justify-center tinta-suave borda-realce transition-colors">'
        + '<svg class="icon tinta-marca text-3xl mb-3" width="448" height="512" viewBox="0 0 448 512" xmlns="http://www.w3.org/2000/svg" aria-hidden="true"><path d="M224.1 141c-63.6 0-114.9 51.3-114.9 114.9s51.3 114.9 114.9 114.9S339 319.5 339 255.9 287.7 141 224.1 141zm0 189.6c-41.1 0-74.7-33.5-74.7-74.7s33.5-74.7 74.7-74.7 74.7 33.5 74.7 74.7-33.6 74.7-74.7 74.7zm146.4-194.3c0 14.9-12 26.8-26.8 26.8-14.9 0-26.8-12-26.8-26.8s12-26.8 26.8-26.8 26.8 12 26.8 26.8zm76.1 27.2c-1.7-35.9-9.9-67.7-36.2-93.9-26.2-26.2-58-34.4-93.9-36.2-37-2.1-147.9-2.1-184.9 0-35.8 1.7-67.6 9.9-93.9 36.1s-34.4 58-36.2 93.9c-2.1 37-2.1 147.9 0 184.9 1.7 35.9 9.9 67.7 36.2 93.9s58 34.4 93.9 36.2c37 2.1 147.9 2.1 184.9 0 35.9-1.7 67.7-9.9 93.9-36.2 26.2-26.2 34.4-58 36.2-93.9 2.1-37 2.1-147.8 0-184.8zM398.8 388c-7.8 19.6-22.9 34.7-42.6 42.6-29.5 11.7-99.5 9-132.1 9s-102.7 2.6-132.1-9c-19.6-7.8-34.7-22.9-42.6-42.6-11.7-29.5-9-99.5-9-132.1s-2.6-102.7 9-132.1c7.8-19.6 22.9-34.7 42.6-42.6 29.5-11.7 99.5-9 132.1-9s102.7-2.6 132.1 9c19.6 7.8 34.7 22.9 42.6 42.6 11.7 29.5 9 99.5 9 132.1s2.7 102.7-9 132.1z"/></svg>'
        + '<span class="text-sm">Ver este resultado no Instagram</span></a>';
    }

    function desistirDeTodas() {
parar();
pendentes.forEach(mostrarCartao);
pendentes = [];
    }

    // O prazo e de cada caixa, e nao da pagina: com a galeria vinda
    // da folha (js/galeria.js) as caixas nascem quando a seccao entra
    // no ecra, e uma caixa criada agora nao pode herdar o relogio de
    // uma que nasceu ha um minuto.
    function rodada() {
var agora = Date.now();
pendentes = pendentes.filter(function (caixa) {
    if (!caixa.isConnected) { return false; }   // seccao trocada
    if (temEmbedVivo(caixa)) { return false; }
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
    return { aoFalharScript: aoFalharScript, acompanhar: vigiar };
})();
