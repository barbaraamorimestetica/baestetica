// O botao de voltar ao topo da galeria de resultados.
//
// POR QUE ELE FAZ FALTA AQUI, e nao nas outras paginas
//
// Sao dez seccoes, cada uma com descricao e uma fila de links. Quem desce ate a
// oitava para ler sobre um procedimento tem de subir tudo outra vez para
// escolher outro -- e o indice, que e o que serve para escolher, esta no topo.
//
// No computador o menu do site fica preso no alto e ja resolve metade disto. No
// telefone nao fica: abaixo de 640px ele sai com a rolagem, de proposito, para
// nao comer altura de tela. E justamente ali, onde a pagina e mais comprida em
// numero de telas, que nao havia como voltar.
//
// E UM LINK, E NAO UM BOTAO
//
// Ele leva a uma ancora. Sendo <a href="#topo">, funciona com o JavaScript
// desligado, aparece na navegacao por teclado no lugar certo, e o navegador
// trata do deslocamento sozinho. Um <button> exigiria script para fazer o que o
// HTML ja faz.
//
// O QUE ESTE ARQUIVO ACRESCENTA e so a APARICAO: sem ele o link fica escondido
// pela folha de estilo. Um botao de "voltar ao topo" visivel enquanto ainda se
// esta no topo e um botao que nao faz nada.
(function () {
    'use strict';

    // Quanto e preciso ter descido para o botao valer a pena. Uma tela e meia:
    // abaixo disso, subir e um gesto curto e o botao seria estorvo. Medido no
    // telefone, o indice sozinho tem 305px, entao 1,5 tela poe o limiar bem
    // depois dele.
    function limiar() {
        return window.innerHeight * 1.5;
    }

    function iniciar() {
        var alvo = document.querySelector('.ao-topo');
        if (!alvo) { return; }
        var raiz = document.documentElement;
        var estava = null;

        // SEM requestAnimationFrame, e vale dizer por que.
        //
        // A primeira versao agrupava a conta num rAF, para nao mexer na classe
        // dezenas de vezes entre desenhos. Duas razoes para o tirar:
        //
        //   - a conta nao precisa disso. Ler o pageYOffset dentro de um ouvinte
        //     de rolagem e barato, e a classe so muda DUAS vezes numa leitura
        //     inteira -- ao passar do limiar para baixo e para cima. O `estava`
        //     e o que garante isso: sem mudanca, nao se toca no DOM.
        //
        //   - o rAF nao corre sob tempo virtual no Chrome headless. Medido:
        //     rolar 1600px e disparar o evento nao acendia o botao, e a classe
        //     ficava vazia. Um atalho que so se pode conferir a mao acaba por
        //     nao ser conferido.
        function avaliar() {
            var desceu = (window.pageYOffset || raiz.scrollTop) > limiar();
            if (desceu === estava) { return; }
            estava = desceu;
            raiz.classList.toggle('mostra-ao-topo', desceu);
        }

        window.addEventListener('scroll', avaliar, { passive: true });
        window.addEventListener('resize', avaliar, { passive: true });
        avaliar();   // quem chega com a pagina ja rolada (voltar do navegador)
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', iniciar);
    } else {
        iniciar();
    }
}());
