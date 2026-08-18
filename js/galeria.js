// A galeria de resultados e montada a partir de uma folha do Google Sheets,
// para a Barbara poder acrescentar um post sem mexer no site. Sao duas abas:
//
//   Links          ID, Link, Procedimento     -- um post por linha
//   Procedimentos  Procedimento, Ordem, Descricao  -- uma seccao por linha
//
// O elo entre elas e o nome do procedimento escrito igual nas duas.
//
// ---------------------------------------------------------------------------
// O QUE ESTA PAGINA TEM DE SOBREVIVER
//
// 1. A folha nao responder. A pagina ja traz duas seccoes escritas no HTML --
//    as marcadas [data-piso]. Elas so sao removidas depois de a folha chegar
//    e ser dada como valida. Se algo falhar, ficam la: a paciente ve alguma
//    coisa, e o Google tem texto para indexar.
//
// 2. Pedir uma aba que nao existe. O endereco do Sheets aceita ?sheet=<nome>
//    e, quando o nome nao existe, devolve HTTP 200 com a PRIMEIRA aba. Medido:
//    pedi "NaoExiste" e vieram os links. Por isso cada aba e conferida pelo
//    cabecalho antes de ser usada -- sem isso o site desenharia os links no
//    lugar das descricoes, sem erro nenhum.
//
// 3. Um embed morrer. Quem trata disso e o window.baEmbeds, que ja existia.
//    As caixas criadas aqui sao registadas nele pelo baEmbeds.acompanhar().
// ---------------------------------------------------------------------------
(function () {
    'use strict';

    var FOLHA = '1aO-AGvUPBe8y71UP7hlnF3a4dH24Jxq3dUv9f2QE6VI';
    var ABAS = {
        // Sao estas tres que identificam a aba, e por isso sao obrigatorias.
        // As colunas Resultados e Destaque sao OPCIONAIS de proposito: sem
        // isso, o dia em que o codigo entra e a planilha ainda nao tem as
        // colunas as duas paginas ficam sem galeria ao mesmo tempo. Ausentes,
        // vale o comportamento de antes delas -- tudo na Resultados, nada em
        // destaque.
        links: { nome: 'Links', cabecalho: ['ID', 'Link', 'Procedimento'] },
        procs: { nome: 'Procedimentos', cabecalho: ['Procedimento', 'Ordem', 'Descricao'] }
    };
    // Posts que mostram mais de um procedimento vao todos para esta seccao,
    // em vez de se repetirem numa seccao por procedimento.
    //
    // Este nome tem de existir, escrito igual, na aba Procedimentos: e o elo
    // entre as duas abas. Se nao existir, o agrupar() nao deixa os posts cair
    // no vazio -- devolve-os as seccoes de cada procedimento, que e o
    // comportamento de antes desta regra. Perder quatro resultados por causa
    // de um acento seria pior do que os repetir.
    var COMBINADOS = 'Harmonização facial (mais de 1 procedimento)';

    function endereco(aba) {
        return 'https://docs.google.com/spreadsheets/d/' + FOLHA
             + '/gviz/tq?tqx=out:csv&sheet=' + encodeURIComponent(aba);
    }

    // ---- CSV -------------------------------------------------------------
    // O Google devolve virgula como separador e aspas a volta de tudo o que
    // contenha virgula ou quebra de linha -- e as descricoes contem as duas.
    // Por isso nao da para partir por linha e depois por virgula.
    function lerCsv(texto) {
        var linhas = [], campo = '', linha = [], aspas = false, i;
        texto = texto.replace(/^﻿/, '');
        for (i = 0; i < texto.length; i++) {
            var c = texto[i];
            if (aspas) {
                if (c === '"') {
                    if (texto[i + 1] === '"') { campo += '"'; i++; }
                    else { aspas = false; }
                } else { campo += c; }
            } else if (c === '"') {
                aspas = true;
            } else if (c === ',') {
                linha.push(campo); campo = '';
            } else if (c === '\n' || c === '\r') {
                if (c === '\r' && texto[i + 1] === '\n') { i++; }
                linha.push(campo); campo = '';
                linhas.push(linha); linha = [];
            } else {
                campo += c;
            }
        }
        if (campo !== '' || linha.length) { linha.push(campo); linhas.push(linha); }
        return linhas.filter(function (l) {
            return l.some(function (c) { return c.trim() !== ''; });
        });
    }

    function buscarAba(cfg) {
        return fetch(endereco(cfg.nome), { credentials: 'omit' })
            .then(function (r) {
                if (!r.ok) { throw new Error('HTTP ' + r.status + ' na aba ' + cfg.nome); }
                return r.text();
            })
            .then(function (txt) {
                var linhas = lerCsv(txt);
                if (!linhas.length) { throw new Error('aba ' + cfg.nome + ' vazia'); }
                var cab = linhas[0].map(function (c) { return c.trim(); });
                // e aqui que se apanha o nome de aba errado
                for (var i = 0; i < cfg.cabecalho.length; i++) {
                    if (cab[i] !== cfg.cabecalho[i]) {
                        throw new Error('aba ' + cfg.nome + ': esperava a coluna '
                            + cfg.cabecalho[i] + ' e veio ' + (cab[i] || '(nada)')
                            + ' -- o nome da aba mudou?');
                    }
                }
                return linhas.slice(1).map(function (l) {
                    var o = {};
                    cab.forEach(function (nome, j) { o[nome] = (l[j] || '').trim(); });
                    return o;
                });
            });
    }

    // ---- montagem --------------------------------------------------------
    // Uma celula marcada -- qualquer coisa escrita nela -- faz o post aparecer
    // naquele lugar. Vazia, nao aparece. A regra e a mesma nas duas colunas, e
    // e a coisa mais simples de explicar a quem edita a planilha.
    function marcado(l, coluna) {
        return String(l[coluna] || '').trim() !== '';
    }

    function temColuna(links, coluna) {
        return links.length > 0
            && Object.prototype.hasOwnProperty.call(links[0], coluna);
    }

    function procedimentosDe(celula) {
        return celula.split(';').map(function (p) { return p.trim(); })
                     .filter(function (p) { return p; });
    }

    function agrupar(links, temSeccao) {
        var mapa = {};
        if (temColuna(links, 'Resultados')) {
            links = links.filter(function (l) { return marcado(l, 'Resultados'); });
        }
        var juntar = temSeccao[COMBINADOS];
        if (!juntar) {
            console.warn('galeria: nao ha linha "' + COMBINADOS + '" na aba '
                + 'Procedimentos. Os posts com mais de um procedimento voltam a '
                + 'aparecer em cada seccao, para nao se perderem.');
        }
        links.forEach(function (l) {
            if (!l.Link) { return; }
            var ps = procedimentosDe(l.Procedimento);
            if (!ps.length) { return; }
            if (ps.length > 1 && juntar) {
                (mapa[COMBINADOS] = mapa[COMBINADOS] || []).push(l);
            } else {
                ps.forEach(function (p) { (mapa[p] = mapa[p] || []).push(l); });
            }
        });
        return mapa;
    }

    function paragrafos(texto) {
        return texto.split(/\n\s*\n/).map(function (p) {
            return p.split('\n').map(function (l) { return l.trim(); }).join(' ').trim();
        }).filter(function (p) { return p; });
    }

    function caixaDeEmbed(link) {
        var caixa = document.createElement('div');
        caixa.className = 'carrossel-slide';
        caixa.setAttribute('data-embed-instagram', '');
        caixa.setAttribute('data-permalink', link);
        return caixa;
    }

    // O blockquote so nasce quando a seccao entra no ecra. Com 19 embeds numa
    // pagina, cria-los todos de uma vez sao 19 iframes com script proprio a
    // arrancar juntos -- no telefone isso trava e gasta dados da paciente.
    function encherCaixa(caixa) {
        if (caixa.getAttribute('data-cheia')) { return; }
        caixa.setAttribute('data-cheia', '1');
        var bq = document.createElement('blockquote');
        bq.className = 'instagram-media';
        bq.setAttribute('data-instgrm-captioned', '');
        bq.setAttribute('data-instgrm-permalink', caixa.getAttribute('data-permalink'));
        bq.setAttribute('data-instgrm-version', '14');
        bq.setAttribute('style', 'background:#FFF; border:0; border-radius:12px;'
            + ' box-shadow:0 0 1px 0 rgba(0,0,0,0.5),0 1px 10px 0 rgba(0,0,0,0.15);'
            + ' margin:1px; max-width:540px; min-width:326px; padding:0; width:99.375%;');
        caixa.appendChild(bq);
        if (window.baEmbeds && window.baEmbeds.acompanhar) {
            window.baEmbeds.acompanhar([caixa]);
        }
        if (window.instgrm && window.instgrm.Embeds) { window.instgrm.Embeds.process(); }
    }

    function observarCaixas(raiz) {
        var caixas = Array.prototype.slice.call(
            raiz.querySelectorAll('[data-embed-instagram]'));
        if (!('IntersectionObserver' in window)) {
            caixas.forEach(encherCaixa);
            return;
        }
        var obs = new IntersectionObserver(function (entradas) {
            entradas.forEach(function (e) {
                if (e.isIntersecting) { encherCaixa(e.target); obs.unobserve(e.target); }
            });
        }, { rootMargin: '400px 0px' });
        caixas.forEach(function (c) { obs.observe(c); });
    }

    // ---- carrossel -------------------------------------------------------
    // Empilhar os 19 embeds punha a pagina em 26.000px. Aqui cada procedimento
    // ocupa a altura de um post so, e navega-se de lado.
    //
    // Que HA mais para ver e dito de tres maneiras, porque uma so nao chega:
    // a borda do post seguinte fica a espreita (o unico sinal que sobra no
    // telefone, onde as setas saem), as bolinhas dizem quantos sao e em qual
    // se esta, e as setas dao o gesto a quem usa rato. Para quem usa leitor
    // de ecra ha um texto que se atualiza sozinho.
    function seta(rotulo, caminho) {
        var b = document.createElement('button');
        b.type = 'button';
        b.className = 'carrossel-seta';
        b.setAttribute('aria-label', rotulo);
        b.innerHTML = '<svg class="icon" width="320" height="512" viewBox="0 0 320 512"'
            + ' xmlns="http://www.w3.org/2000/svg" aria-hidden="true"><path d="' + caminho
            + '"/></svg>';
        return b;
    }

    function carrossel(nome, posts) {
        var raiz = document.createElement('div');
        var unico = posts.length < 2;

        var caixa = document.createElement('div');
        caixa.className = 'carrossel';
        // o marcador vai no proprio .carrossel: o seletor do CSS e
        // .carrossel[data-unico], e no elemento de fora nao casava
        if (unico) { caixa.setAttribute('data-unico', ''); }

        var anterior = seta('Resultado anterior de ' + nome,
            'M9.4 233.4c-12.5 12.5-12.5 32.8 0 45.3l192 192c12.5 12.5 32.8 12.5 45.3 0s12.5-32.8 0-45.3L77.3 256 246.6 86.6c12.5-12.5 12.5-32.8 0-45.3s-32.8-12.5-45.3 0l-192 192z');
        var proximo = seta('Próximo resultado de ' + nome,
            'M310.6 233.4c12.5 12.5 12.5 32.8 0 45.3l-192 192c-12.5 12.5-32.8 12.5-45.3 0s-12.5-32.8 0-45.3L242.7 256 73.4 86.6c-12.5-12.5-12.5-32.8 0-45.3s32.8-12.5 45.3 0l192 192z');

        var trilho = document.createElement('div');
        trilho.className = 'carrossel-trilho';
        trilho.tabIndex = 0;
        trilho.setAttribute('role', 'group');
        trilho.setAttribute('aria-label', posts.length + ' resultados de ' + nome
            + (unico ? '' : ' — arraste para o lado para ver os outros'));
        posts.forEach(function (l) { trilho.appendChild(caixaDeEmbed(l.Link)); });

        caixa.appendChild(anterior);
        caixa.appendChild(trilho);
        caixa.appendChild(proximo);
        raiz.appendChild(caixa);

        var pontos = document.createElement('div');
        pontos.className = 'carrossel-pontos';
        var aviso = document.createElement('p');
        aviso.className = 'so-leitor';
        aviso.setAttribute('aria-live', 'polite');
        if (!unico) {
            posts.forEach(function (l, i) {
                var p = document.createElement('button');
                p.type = 'button';
                p.className = 'carrossel-ponto';
                p.setAttribute('aria-label', 'Ir para o resultado ' + (i + 1)
                    + ' de ' + posts.length);
                p.addEventListener('click', function () { irPara(i); });
                pontos.appendChild(p);
            });
            raiz.appendChild(pontos);
            raiz.appendChild(aviso);
        }

        var suave = !window.matchMedia
            || !window.matchMedia('(prefers-reduced-motion: reduce)').matches;

        function largura() {
            var s = trilho.firstElementChild;
            return s ? s.getBoundingClientRect().width + 20 : trilho.clientWidth;
        }
        function atual() {
            return Math.round(trilho.scrollLeft / largura());
        }
        function irPara(i) {
            trilho.scrollTo({ left: i * largura(), behavior: suave ? 'smooth' : 'auto' });
        }
        function pintar() {
            var i = Math.min(atual(), posts.length - 1);
            anterior.disabled = trilho.scrollLeft <= 1;
            proximo.disabled = trilho.scrollLeft
                >= trilho.scrollWidth - trilho.clientWidth - 1;
            Array.prototype.forEach.call(pontos.children, function (p, j) {
                p.setAttribute('aria-current', j === i ? 'true' : 'false');
            });
            aviso.textContent = 'Resultado ' + (i + 1) + ' de ' + posts.length;
        }

        anterior.addEventListener('click', function () { irPara(atual() - 1); });
        proximo.addEventListener('click', function () { irPara(atual() + 1); });
        var pendente = null;
        trilho.addEventListener('scroll', function () {
            if (pendente) { return; }
            pendente = requestAnimationFrame(function () { pendente = null; pintar(); });
        });
        // o estado inicial das setas depende de larguras que so existem depois
        // do primeiro desenho
        requestAnimationFrame(pintar);
        return raiz;
    }

    function secao(indice, nome, descricao, posts) {
        var sec = document.createElement('section');
        // sem o p-8 do Tailwind: o recuo do telefone vive no .secao-resultado,
        // e uma classe de utilidade ganharia dele por especificidade
        sec.className = 'secao-resultado bg-white rounded-3xl gold-border-glow mb-10';

        var topo = document.createElement('div');
        topo.className = 'text-left mb-6';
        var etiqueta = document.createElement('span');
        etiqueta.className = 'tinta-forte font-bold text-xs uppercase tracking-widest';
        etiqueta.textContent = 'Procedimento ' + (indice < 10 ? '0' : '') + indice;
        var titulo = document.createElement('h3');
        titulo.className = 'font-serif text-2xl font-bold tinta-texto';
        titulo.textContent = nome;
        topo.appendChild(etiqueta);
        topo.appendChild(titulo);
        sec.appendChild(topo);

        var texto = document.createElement('div');
        texto.className = 'mb-8 text-left';
        paragrafos(descricao).forEach(function (p) {
            var el = document.createElement('p');
            el.className = 'text-sm tinta-texto leading-relaxed text-justify medida-leitura mb-4 last:mb-0';
            el.textContent = p;          // textContent, nao innerHTML: o texto vem de fora
            texto.appendChild(el);
        });
        sec.appendChild(texto);

        if (posts.length) {
            sec.appendChild(carrossel(nome, posts));
        } else {
            var aviso = document.createElement('p');
            aviso.className = 'text-center text-sm tinta-suave italic border borda-marca rounded-xl py-6';
            aviso.textContent = 'Resultados em breve.';
            sec.appendChild(aviso);
        }
        return sec;
    }

    function desenhar(links, procs) {
        var ordenados = procs.slice().sort(function (a, b) {
            return (parseInt(a.Ordem, 10) || 0) - (parseInt(b.Ordem, 10) || 0);
        });

        // um procedimento usado nos links sem linha em Procedimentos nao tem
        // titulo nem texto -- e melhor dizer no console do que perder o post
        var definidos = {};
        ordenados.forEach(function (p) { definidos[p.Procedimento] = true; });
        var porProc = agrupar(links, definidos);
        Object.keys(porProc).forEach(function (nome) {
            if (!definidos[nome]) {
                console.warn('galeria: "' + nome + '" aparece nos links mas nao tem '
                    + 'linha na aba Procedimentos -- os ' + porProc[nome].length
                    + ' post(s) ficam de fora.');
            }
        });

        var main = document.querySelector('[data-galeria]');
        if (!main) { throw new Error('nao achei [data-galeria]'); }
        var novo = document.createDocumentFragment();
        ordenados.forEach(function (p, i) {
            novo.appendChild(secao(i + 1, p.Procedimento, p.Descricao,
                                   porProc[p.Procedimento] || []));
        });

        // so agora o piso sai -- se algo acima falhar, ele fica
        Array.prototype.slice.call(main.querySelectorAll('[data-piso]'))
             .forEach(function (el) { el.remove(); });
        main.insertBefore(novo, main.firstChild);
        observarCaixas(main);
    }


    // ---- destaques da pagina inicial -------------------------------------
    // A seccao "Acompanhe meu trabalho" tinha um reel escrito a mao no HTML.
    // Uma seccao com esse nome a mostrar sempre o mesmo post e a promessa
    // oposta ao que entrega: envelhece sozinha e ninguem da por isso. Agora
    // sai da mesma planilha, pela coluna Destaque.
    function desenharDestaques(links, alvo) {
        if (!temColuna(links, 'Destaque')) {
            console.warn('galeria: a aba Links nao tem a coluna Destaque; '
                + 'fica o que esta escrito no HTML.');
            return;
        }
        var posts = links.filter(function (l) {
            return l.Link && marcado(l, 'Destaque');
        });
        if (!posts.length) {
            console.warn('galeria: nenhuma linha marcada na coluna Destaque; '
                + 'fica o que esta escrito no HTML.');
            return;
        }
        var novo = carrossel('destaque', posts);
        Array.prototype.slice.call(alvo.querySelectorAll('[data-piso]'))
             .forEach(function (el) { el.remove(); });
        alvo.appendChild(novo);
        observarCaixas(alvo);
    }

    function iniciar() {
        if (!window.fetch || !window.Promise) { return; }   // fica o piso
        var galeria = document.querySelector('[data-galeria]');
        var destaques = document.querySelector('[data-destaques]');
        if (!galeria && !destaques) { return; }
        // a pagina inicial nao precisa da aba Procedimentos
        var pedidos = [buscarAba(ABAS.links)];
        if (galeria) { pedidos.push(buscarAba(ABAS.procs)); }
        Promise.all(pedidos)
            .then(function (r) {
                if (galeria) { desenhar(r[0], r[1]); }
                if (destaques) { desenharDestaques(r[0], destaques); }
            })
            .catch(function (e) {
                console.error('galeria: a folha nao pode ser usada, fica o que '
                    + 'esta escrito no HTML. Motivo:', e && e.message ? e.message : e);
            });
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', iniciar);
    } else {
        iniciar();
    }
})();
