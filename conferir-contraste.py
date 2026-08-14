#!/usr/bin/env python
"""Mede o contraste de todo texto das paginas dos dois repositorios.

    python conferir-contraste.py            mede tudo
    python conferir-contraste.py --detalhe  mostra tambem o que passa raspando

POR QUE ISTO EXISTE COMO SCRIPT, e nao como harness escrito a mao de cada vez:

  1. A lista de paginas sai do os.listdir, nao de uma lista escrita a mao. As
     medicoes anteriores deste projeto usavam listas fixas, e uma pagina ficou
     de fora de TODAS elas -- o "Catalogo de Procedimentos.html", que redireciona
     um endereco antigo. Escondia um link a 3,72:1, a mesma reprova que foi
     fechada 61 vezes noutras paginas.

  2. Mede tambem os ESTADOS. O medidor anterior lia o estilo computado em
     repouso, entao :hover e :focus passavam invisiveis -- e havia dois hovers
     defeituosos, achados a ler markup por sorte. Aqui as regras de :hover e
     :focus sao lidas das folhas e conferidas contra o fundo efetivo do elemento
     que casa com elas.

  3. Confere o anel de foco contra o fundo (WCAG 1.4.11, 3:1).

O servidor sobe na pasta MAE dos dois repositorios, e nao dentro de um deles.
E o que faz o 404.html funcionar: ele usa caminhos absolutos /baestetica/..., que
so resolvem se a raiz estiver acima da pasta do repositorio.

COMUM AOS DOIS REPOSITORIOS -- ver COMUM.md. Depois de mexer, sincronize.
"""
import functools
import http.server
import json
import os
import re
import socketserver
import subprocess
import sys
import tempfile
import threading

PORTA = 8899
CHROME = [
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    "google-chrome", "chromium",
]
REPOS = ["baestetica", "baestetica_private"]

HARNESS = r"""<!DOCTYPE html><meta charset="utf-8"><title>contraste</title>
<body style="font:12px monospace"><pre id="saida">a medir...</pre>
<script>
const PAGINAS = __PAGINAS__;
const LARGURA = 1400;   // mais largo que a folha em paisagem (297mm = 1122px)

function rgb(s){const m=String(s).match(/-?[\d.]+/g);return m?m.slice(0,3).map(Number):null;}
function lum(c){const f=c.map(v=>{v/=255;return v<=0.03928?v/12.92:Math.pow((v+0.055)/1.055,2.4);});
  return 0.2126*f[0]+0.7152*f[1]+0.0722*f[2];}
function razao(a,b){const L=lum(a),M=lum(b);return (Math.max(L,M)+0.05)/(Math.min(L,M)+0.05);}
function hex(c){return "#"+c.map(v=>Math.round(v).toString(16).padStart(2,"0")).join("").toUpperCase();}

// fundo efetivo: sobe a arvore ate achar quem pinta de facto
function fundo(el,win){
  let n=el;
  while(n && n!==win.document.documentElement){
    const bg=win.getComputedStyle(n).backgroundColor, c=rgb(bg);
    const alpha=String(bg).match(/rgba?\([^)]*,\s*([\d.]+)\)/);
    if(c && (!alpha || parseFloat(alpha[1])>0.5)) return c;
    n=n.parentElement;
  }
  const c=rgb(win.getComputedStyle(win.document.body).backgroundColor);
  return (c && c.join()!=="0,0,0") ? c : [255,255,255];
}

function textoProprio(el){
  let t=""; for(const n of el.childNodes) if(n.nodeType===3) t+=n.textContent;
  return t.trim();
}

function grande(px,peso){ return px>=24 || (px>=18.66 && peso>=700); }

// --- 1. repouso -----------------------------------------------------------
function repouso(win){
  const out=[];
  for(const el of win.document.querySelectorAll("*")){
    if(/^(SCRIPT|STYLE|SVG|PATH|HEAD|META|LINK|TITLE|BR|HR|IMG|NOSCRIPT)$/.test(el.tagName)) continue;
    const txt=textoProprio(el); if(!txt) continue;
    const cs=win.getComputedStyle(el);
    if(cs.visibility==="hidden"||cs.display==="none"||parseFloat(cs.opacity)<0.1) continue;
    const fg=rgb(cs.color); if(!fg) continue;
    const bg=fundo(el,win), px=parseFloat(cs.fontSize), peso=parseInt(cs.fontWeight)||400;
    const r=razao(fg,bg), exig=grande(px,peso)?3.0:4.5;
    if(r<exig) out.push({tipo:"repouso",tag:el.tagName,px:+px.toFixed(1),peso,
      fg:hex(fg),bg:hex(bg),r:+r.toFixed(2),exig,txt:txt.slice(0,40),
      cls:(el.className||"").toString().slice(0,44)});
  }
  return out;
}

// --- 2. estados: le as regras de :hover / :focus das folhas ---------------
function estados(win){
  const out=[], vistos=new Set();
  let lidas=0;
  const folhas=[...win.document.styleSheets];
  for(const f of folhas){
    let regras; try{ regras=[...f.cssRules]; }catch(e){ continue; }  // folha de outra origem
    const pilha=[...regras];
    while(pilha.length){
      const r=pilha.pop();
      // A ordem importa, e a ordem errada custou caro: o Chrome suporta CSS
      // aninhado, entao CSSStyleRule.cssRules EXISTE e e truthy mesmo vazio. Com
      // "if(r.cssRules) continue" primeiro, toda regra de estilo era saltada e
      // este medidor devolvia zero achados -- que parece aprovacao e nao e.
      if(!r.selectorText){                        // @media, @supports, @layer
        if(r.cssRules) pilha.push(...r.cssRules);
        continue;
      }
      if(!/:(hover|focus|focus-visible|focus-within)\b/.test(r.selectorText)) continue;
      // do cssText, e nao de r.style.color: um valor com var() dentro pode
      // serializar vazio no CSSOM
      const corpoEstado=(r.cssText.match(/\{([^}]*)\}/)||[,""])[1];
      if(!/(^|;|\s)color\s*:/.test(corpoEstado)) continue;
      lidas++;
      const cor=corpoEstado;
      for(const sel of r.selectorText.split(",")){
        const limpo=sel.trim().replace(/:(hover|focus-visible|focus-within|focus)\b/g,"");
        if(!limpo) continue;
        let alvos; try{ alvos=win.document.querySelectorAll(limpo); }catch(e){ continue; }
        for(const el of alvos){
          const txt=textoProprio(el); if(!txt) continue;
          const chave=sel.trim()+"|"+txt.slice(0,20);
          if(vistos.has(chave)) continue; vistos.add(chave);
          // resolve a cor declarada (pode ser var()) medindo num elemento clone
          const sonda=win.document.createElement("span");
          sonda.style.cssText="position:absolute;visibility:hidden;"+cor;
          el.appendChild(sonda);
          const fg=rgb(win.getComputedStyle(sonda).color);
          sonda.remove();
          if(!fg) continue;
          const cs=win.getComputedStyle(el);
          const bg=fundo(el,win), px=parseFloat(cs.fontSize), peso=parseInt(cs.fontWeight)||400;
          const razaoEstado=razao(fg,bg), exig=grande(px,peso)?3.0:4.5;
          if(razaoEstado<exig) out.push({tipo:"estado",seletor:sel.trim().slice(0,44),
            tag:el.tagName,px:+px.toFixed(1),peso,fg:hex(fg),bg:hex(bg),
            r:+razaoEstado.toFixed(2),exig,txt:txt.slice(0,40)});
        }
      }
    }
  }
  out.regrasLidas=lidas;
  return out;
}

// --- 3. anel de foco contra o fundo (WCAG 1.4.11, 3:1) -------------------
//
// Lido das REGRAS, e nao dando foco ao elemento. Duas razoes, as duas apanhadas
// a medir de verdade, com a primeira versao deste script:
//
//   - :focus-visible nao casa com foco programatico num <button>, e nem sempre
//     num <a>: o Chrome decide pelo que veio antes, teclado ou rato. Medindo
//     assim, botoes que TEM anel apareciam como "sem anel".
//   - o anel tem outline-offset positivo, entao fica FORA do elemento, sobre o
//     fundo do pai. Medir contra o fundo do proprio elemento acusava 2,38:1 num
//     botao escuro e 2,77:1 no botao verde do WhatsApp -- quando o anel esta
//     desenhado sobre o cartao claro em volta, onde da 5,49:1.
function anel(win){
  const out=[], vistos=new Set();
  const focaveis="a[href],button,input,select,textarea,summary,[tabindex]";

  const regras=[];
  for(const f of [...win.document.styleSheets]){
    let rs; try{ rs=[...f.cssRules]; }catch(e){ continue; }
    const pilha=[...rs];
    while(pilha.length){
      const r=pilha.pop();
      if(!r.selectorText){                        // ver a nota em estados()
        if(r.cssRules) pilha.push(...r.cssRules);
        continue;
      }
      if(!/:focus(-visible)?\b/.test(r.selectorText)) continue;
      // Le do cssText, e nao de r.style.outline. Um shorthand com var() dentro --
      // "outline: 2px solid var(--marca-forte)" -- serializa VAZIO no CSSOM, tanto
      // no shorthand como nos longhands. A primeira versao disto descartava a
      // propria regra de foco do projeto e acusava 58 elementos sem anel.
      const corpo=(r.cssText.match(/\{([^}]*)\}/)||[,""])[1];
      if(!/\boutline\b/.test(corpo)) continue;
      regras.push({sel:r.selectorText, corpo:corpo});
    }
  }

  for(const el of win.document.querySelectorAll(focaveis)){
    const cs=win.getComputedStyle(el);
    if(cs.display==="none"||cs.visibility==="hidden") continue;
    const cx=el.getBoundingClientRect();
    if(!cx.width && !cx.height) continue;          // nao renderizado (pai oculto)
    const chave=el.tagName+"|"+(el.className||"").toString().slice(0,24);
    if(vistos.has(chave)) continue; vistos.add(chave);

    let achou=null;
    for(const r of regras){
      for(const sel of r.sel.split(",")){
        const limpo=sel.trim().replace(/:focus(-visible)?\b/g,"");
        if(!limpo) continue;
        try{ if(el.matches(limpo)){ achou=r; break; } }catch(e){}
      }
      if(achou) break;
    }
    if(!achou){
      out.push({tipo:"anel",falta:"nenhuma regra de foco alcanca",tag:el.tagName,
        cls:(el.className||"").toString().slice(0,40)});
      continue;
    }
    // A sonda recebe o CORPO INTEIRO da regra, e nao um valor reconstruido: e o
    // que resolve o var() sem depender de como o CSSOM serializa o shorthand.
    const sonda=win.document.createElement("span");
    sonda.style.cssText="position:absolute;visibility:hidden;"+achou.corpo;
    el.appendChild(sonda);
    const c=rgb(win.getComputedStyle(sonda).outlineColor);
    sonda.remove();
    if(!c) continue;
    const bg=fundo(el.parentElement||el, win);     // o anel fica fora do elemento
    const r=razao(c,bg);
    if(r<3.0) out.push({tipo:"anel",falta:"anel fraco",tag:el.tagName,
      fg:hex(c),bg:hex(bg),r:+r.toFixed(2),exig:3.0,
      cls:(el.className||"").toString().slice(0,40)});
  }
  return out;
}

function carregar(url){
  return new Promise(res=>{
    const f=document.createElement("iframe");
    f.style.cssText="width:"+LARGURA+"px;height:1200px;border:0;position:absolute;left:-9999px";
    f.src=url; document.body.appendChild(f);
    f.onload=()=>setTimeout(()=>res(f),1800);
    setTimeout(()=>res(f),12000);
  });
}

(async()=>{
  const rel=[];
  for(const p of PAGINAS){
    const f=await carregar(p);
    try{
      const w=f.contentWindow;
      const n=w.document.querySelectorAll("*").length;
      const est=estados(w);
      const achados=[...repouso(w), ...est, ...anel(w)];
      rel.push({pag:p, elementos:n, achados, regrasEstado:est.regrasLidas||0});
    }catch(e){ rel.push({pag:p, erro:String(e)}); }
    f.remove();
    document.title=p;
  }
  document.getElementById("saida").textContent=JSON.stringify(rel);
  document.title="PRONTO";
})();
</script>
"""


def chrome():
    for c in CHROME:
        if os.path.isfile(c):
            return c
    return CHROME[-2]


def _lum(c):
    f = []
    for v in c:
        v /= 255.0
        f.append(v / 12.92 if v <= 0.03928 else ((v + 0.055) / 1.055) ** 2.4)
    return 0.2126 * f[0] + 0.7152 * f[1] + 0.0722 * f[2]


def _razao(a, b):
    la, lb = _lum(a), _lum(b)
    return (max(la, lb) + 0.05) / (min(la, lb) + 0.05)


def _rgb(h):
    h = h.lstrip("#")
    return [int(h[i:i + 2], 16) for i in (0, 2, 4)]


def estatico(fonte):
    """Confere as cores de uma pagina que redireciona, por leitura do ficheiro.

    Grosseiro de proposito: nao ha layout aqui, nem tamanho de fonte fiavel. Toma
    todo 'color: #xxxxxx' e mede contra o fundo declarado no body, ou branco. Serve
    para uma pagina de redirecionamento, que e texto simples sobre fundo simples --
    e e a unica que precisa disto.
    """
    fundo = "#FFFFFF"
    m = re.search(r"<body[^>]*background(?:-color)?:\s*(#[0-9A-Fa-f]{6})", fonte)
    if m:
        fundo = m.group(1)
    fora = []
    for m in re.finditer(r"color:\s*(#[0-9A-Fa-f]{6})", fonte):
        cor = m.group(1)
        if cor.upper() == fundo.upper():
            continue
        r = _razao(_rgb(cor), _rgb(fundo))
        if r < 4.5:
            i = fonte.rfind("<", 0, m.start())
            fora.append({"fg": cor.upper(), "bg": fundo.upper(), "r": "%.2f" % r,
                         "exig": 4.5, "onde": fonte[i:i + 60].replace("\n", " ")})
    return fora


def paginas(mae):
    """Toda pagina HTML dos dois repositorios, descoberta na pasta."""
    fora = []
    for repo in REPOS:
        raiz = os.path.join(mae, repo)
        if not os.path.isdir(raiz):
            continue
        for a in sorted(os.listdir(raiz)):
            if a.endswith(".html"):
                # o iframe recebe o caminho ja escapado
                from urllib.parse import quote
                fora.append("/%s/%s" % (repo, quote(a)))
    return fora


def servir(mae):
    # Subclasse, e nao functools.partial com log_message por cima: o partial nao
    # e a classe, entao atribuir-lhe log_message nao silencia nada -- e o relatorio
    # sai afogado em linhas de GET.
    class Calado(http.server.SimpleHTTPRequestHandler):
        def log_message(self, *a, **k):
            pass

    manipulador = functools.partial(Calado, directory=mae)
    srv = socketserver.TCPServer(("127.0.0.1", PORTA), manipulador)
    srv.allow_reuse_address = True
    t = threading.Thread(target=srv.serve_forever, daemon=True)
    t.start()
    return srv


def main():
    detalhe = "--detalhe" in sys.argv
    aqui = os.path.dirname(os.path.abspath(__file__))
    mae = os.path.dirname(aqui)

    lista = paginas(mae)
    print("%d pagina(s) descoberta(s) na pasta -- nenhuma lista escrita a mao" % len(lista))

    # Paginas que redirecionam nao dao para medir num iframe: ele segue o
    # redirecionamento e mede o DESTINO. Foi o que aconteceu ao "Catalogo de
    # Procedimentos.html", que reportava 169 elementos -- os do catalogo.html --
    # e por isso passava com zero achados enquanto tinha um link a 3,72:1.
    # Estas sao conferidas por leitura do ficheiro.
    redirecionam = []
    for rel_p in lista:
        from urllib.parse import unquote
        caminho = os.path.join(mae, *unquote(rel_p.lstrip("/")).split("/"))
        try:
            fonte = open(caminho, encoding="utf-8").read()
        except OSError:
            continue
        if re.search(r'http-equiv=["\']refresh|location\.replace|location\.href\s*=', fonte):
            redirecionam.append((rel_p, fonte))
    if redirecionam:
        print()
        print("%d pagina(s) redirecionam -- conferidas por leitura, nao no iframe:" % len(redirecionam))
        for rel_p, fonte in redirecionam:
            achados = estatico(fonte)
            print("  %-46s %d achado(s)" % (rel_p, len(achados)))
            for a in achados:
                print("       ESTATICO %s sobre %s  %s:1 (pede %s)  %s" % (
                    a["fg"], a["bg"], a["r"], a["exig"], a["onde"]))
    print()

    srv = servir(mae)
    try:
        d = tempfile.mkdtemp(prefix="contraste-")
        h = os.path.join(mae, "_contraste_harness.html")
        with open(h, "w", encoding="utf-8") as f:
            f.write(HARNESS.replace("__PAGINAS__", json.dumps(lista)))
        saida = subprocess.run(
            [chrome(), "--headless=new", "--disable-gpu", "--virtual-time-budget=240000",
             "--dump-dom", "http://127.0.0.1:%d/_contraste_harness.html" % PORTA],
            capture_output=True, text=True, encoding="utf-8", errors="replace").stdout
    finally:
        srv.shutdown()
        try:
            os.remove(h)
        except OSError:
            pass

    m = re.search(r'<pre id="saida">(.*?)</pre>', saida, re.S)
    if not m:
        sys.exit("Erro: o harness nao devolveu resultado. Chrome disponivel?")
    import html as H
    rel = json.loads(H.unescape(m.group(1)))

    total = 0
    for r in rel:
        if "erro" in r:
            print("  %-46s ERRO %s" % (r["pag"], r["erro"][:60]))
            total += 1
            continue
        ach = r["achados"]
        marca = "" if not ach else "   <<<"
        print("  %-46s %4d elementos, %d regra(s) de estado, %d achado(s)%s" % (
            r["pag"], r["elementos"], r.get("regrasEstado", 0), len(ach), marca))
        for a in ach:
            if a["tipo"] == "anel":
                print("       ANEL     %-8s %-6s %s %s" % (
                    a["falta"], a["tag"], a.get("r", ""), a.get("cls", "")))
            elif a["tipo"] == "estado":
                print("       ESTADO   %-44s %s -> %s  %s:1 (pede %s)  \"%s\"" % (
                    a["seletor"], a["fg"], a["bg"], a["r"], a["exig"], a["txt"]))
            else:
                print("       REPOUSO  %-6s %5spx/%-3s %s / %s  %s:1 (pede %s)  \"%s\"" % (
                    a["tag"], a["px"], a["peso"], a["fg"], a["bg"], a["r"], a["exig"], a["txt"]))
        total += len(ach)

    print()
    if total:
        print("TOTAL: %d achado(s)." % total)
    else:
        print("TOTAL: nenhum. Todo texto passa em repouso e nos estados, e todo")
        print("       elemento focavel tem anel com 3:1 ou mais contra o fundo.")
    return 1 if total else 0


if __name__ == "__main__":
    sys.exit(main())
