#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Teste de fumaça dos dez sites: percorre, clica e CONFERE o que sai.

Por que existe
--------------
O defeito da vírgula decimal ficou meses no ar nas três calculadoras de lista,
invertendo a conclusão estatística de quem digitava número do jeito brasileiro.
Nenhum teste pegou, porque a suíte de regressão testa as funções de `stats.js`
e não a página montada. Este robô cobre o buraco: ele abre a página publicada,
preenche os campos como uma pessoa preencheria e compara o número que aparece
na tela com um valor de referência produzido pelo SciPy.

O que ele NÃO é
---------------
Não é gerador de tráfego. O AdSense e os scripts de medição são bloqueados na
camada de rede, o User-Agent se identifica como robô, e o volume é de umas
poucas dezenas de páginas por dia. Tráfego automatizado para página com AdSense
é "invalid traffic" na política do programa e leva a banimento permanente da
conta, então o robô é feito para não contar como visita nem como impressão.

Uso
---
    python tools/smoke_sites.py                      # tudo, páginas aleatórias
    python tools/smoke_sites.py --sites calculadoraestatistica.com.br
    python tools/smoke_sites.py --paginas 3 --seed 42
    python tools/smoke_sites.py --so-golden           # só as contas conferidas

A semente é impressa no começo. Para repetir exatamente a execução que falhou,
rode de novo com `--seed <aquele número>`.

Saída
-----
Código 0 quando não há falha. Qualquer falha devolve código 1, o que faz o
workflow do GitHub falhar e manda o e-mail de aviso. Avisos (console.warn,
título vazio, lentidão) são relatados mas não derrubam a execução: alerta que
dispara por nada vira alerta que ninguém lê.
"""
from __future__ import annotations

import argparse
import os
import random
import re
import sys
import time
import urllib.request
import xml.etree.ElementTree as ET

try:
    from playwright.sync_api import Error as PwError
    from playwright.sync_api import sync_playwright
except ImportError:  # pragma: no cover
    print("Falta o Playwright. Instale com:  pip install playwright && playwright install chromium",
          file=sys.stderr)
    raise SystemExit(2)


UA = ("Mozilla/5.0 (compatible; CalcEstatSmokeBot/1.0; teste de fumaca, nao conta "
      "como visita; +https://calculadoraestatistica.com.br/sobre.html)")

# Nada de anúncio nem de medição. O robô não deve aparecer em relatório de
# audiência nem gerar impressão de anúncio.
HOSTS_BLOQUEADOS = (
    "pagead2.googlesyndication.com", "googlesyndication.com", "doubleclick.net",
    "googletagmanager.com", "google-analytics.com", "analytics.google.com",
    "adservice.google.com", "adservice.google.dk", "adservice.google.com.br",
    "fundingchoicesmessages.google.com", "ep1.adtrafficquality.google",
    "ep2.adtrafficquality.google", "tpc.googlesyndication.com",
)

# domínio -> chave do consentimento no localStorage (js/cookie-consent.js)
SITES = {
    "calculadoraestatistica.com.br": "ce-consent",
    "agrododia.com.br": "ad-consent",
    "statistikberegner.dk": "sb-consent",
    "landbrugstal.dk": "lt-consent",
    "hverdagstal.dk": "hv-consent",
    "lonberegning.dk": "lb-consent",
    "kitclinico.com.br": "kc-consent",
    "datafolia.com.br": "df-consent",
    "calendariobrasileiro.com.br": "cb-consent",
    "danskedage.dk": "dd-consent",
}

# Contas com resposta conhecida. Os valores de referência vêm do SciPy 1.17.1 e
# estão anotados ao lado de cada um, para a conferência não depender de
# lembrança de ninguém.
#
# Cada entrada: campos a preencher por índice de <textarea>, e o que precisa
# aparecer no resultado.
GOLDEN = [
    {
        "nome": "ANOVA com vírgula decimal",
        "url": "https://calculadoraestatistica.com.br/k-amostras.html",
        "textareas": ["5,1 5,4 4,9 5,3 5,2", "6,2 6,5 6,0 6,4 6,3", "7,1 7,4 6,9 7,3 7,2"],
        # scipy.stats.f_oneway -> F=135.5855856, p=5.791529e-09, gl 2/12
        "numeros": [(r"F\s*=\s*([\d.,]+)", 135.5856, 0.05)],
        "contem": ["2/12"],
        "nao_contem": ["não significativa", "nao significativa"],
    },
    {
        "nome": "ANOVA med decimalkomma",
        "url": "https://statistikberegner.dk/anova.html",
        "textareas": ["5,1 5,4 4,9 5,3 5,2", "6,2 6,5 6,0 6,4 6,3", "7,1 7,4 6,9 7,3 7,2"],
        "numeros": [(r"F\s*=\s*([\d.,]+)", 135.5856, 0.05)],
        "contem": ["2/12"],
        "nao_contem": ["ikke signifikant"],
    },
    {
        "nome": "Mann-Whitney com vírgula decimal",
        "url": "https://calculadoraestatistica.com.br/wilcoxon.html",
        "textareas": ["12,5 15,5 11,5 18,5 14,5 16,5", "20,5 22,5 19,5 25,5 21,5 23,5"],
        # scipy.stats.mannwhitneyu(..., 'two-sided') -> U=0
        "numeros": [(r"U\s*=\s*([\d.,]+)", 0.0, 0.01)],
        "nao_contem": ["não significativa", "nao significativa"],
    },
    {
        "nome": "Mann-Whitney med decimalkomma",
        "url": "https://statistikberegner.dk/wilcoxon.html",
        "textareas": ["12,5 15,5 11,5 18,5 14,5 16,5", "20,5 22,5 19,5 25,5 21,5 23,5"],
        "numeros": [(r"U\s*=\s*([\d.,]+)", 0.0, 0.01)],
        "nao_contem": ["ikke signifikant"],
    },
    {
        "nome": "correlação lê os próprios exemplos do campo",
        "url": "https://calculadoraestatistica.com.br/correlacao.html",
        "placeholders": ["#varX", "#varY"],
        # scipy.stats.pearsonr([1,2,3,4,5],[2.1,3.9,6.2,7.8,9.5]) -> r=0.9981322
        "numeros": [(r"r\s*=\s*([\d.,]+)", 0.9981, 0.001)],
        "contem": ["n = 5"],
    },
    {
        "nome": "korrelation laeser sine egne eksempler",
        "url": "https://statistikberegner.dk/korrelation.html",
        "placeholders": ["#varX", "#varY"],
        "numeros": [(r"r\s*=\s*([\d.,]+)", 0.9981, 0.001)],
        "contem": ["n = 5"],
    },
    {
        "nome": "correlação: milhar separado por espaço não dobra a série",
        "url": "https://calculadoraestatistica.com.br/correlacao.html",
        "campos": {"#varX": "1 234\n5 678\n9 012\n3 456\n7 890",
                   "#varY": "2 345\n6 789\n1 023\n4 567\n8 901"},
        # scipy.stats.pearsonr -> r=0.191872, p=0.757207
        "numeros": [(r"r\s*=\s*(-?[\d.,]+)", 0.1919, 0.002)],
        "contem": ["n = 5"],
    },
    {
        "nome": "tamanho de amostra, exemplo embutido",
        "url": "https://calculadoraestatistica.com.br/tamanho-amostra.html",
        "exemplo": True,
        "numeros": [],
        "contem": [],
    },
]

SEL_RESULTADO = ('[id$="-result"], #result, #calc-result, [id$="-resultat"], '
                 '[id$="-resultado"]')
SEL_EXEMPLO = ('a[id$="-example"], button[id$="-example"], a#calc-example, '
               'button#calc-example, a[id$="-eksempel"], button[id$="-eksempel"]')
# Widgets que mudam estado sem sair da página.
SEL_WIDGET = ('summary, [role="tab"], button[aria-expanded], '
              'button[data-tab], .segmented button, .tabs button')


def pt_float(txt: str | None) -> float | None:
    """Número escrito em pt-BR ou da-DK para float."""
    if not txt:
        return None
    s = txt.strip()
    if "," in s:
        s = s.replace(".", "").replace(",", ".")
    try:
        return float(s)
    except ValueError:
        return None


def urls_do_sitemap(dominio: str, tempo: int = 25) -> list[str]:
    """URLs publicadas, lidas do sitemap do próprio site.

    Ler do sitemap em vez de cravar caminhos no script: página nova entra na
    rodada sozinha, e página removida sai.
    """
    alvo = "https://%s/sitemap.xml" % dominio
    req = urllib.request.Request(alvo, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=tempo) as r:
        bruto = r.read()
    raiz = ET.fromstring(bruto)
    ns = {"s": "http://www.sitemaps.org/schemas/sitemap/0.9"}
    locs = [e.text.strip() for e in raiz.findall(".//s:loc", ns) if e.text]
    if not locs:  # sitemap sem namespace
        locs = [e.text.strip() for e in raiz.iter() if e.tag.endswith("loc") and e.text]
    return [u for u in locs if u.startswith("http")]


class Relatorio:
    def __init__(self) -> None:
        self.falhas: list[str] = []
        self.avisos: list[str] = []
        self.paginas = 0
        self.cliques = 0
        self.golden_ok = 0

    def falha(self, onde: str, msg: str) -> None:
        self.falhas.append("%s — %s" % (onde, msg))
        print("      FALHA: %s" % msg)

    def aviso(self, onde: str, msg: str) -> None:
        self.avisos.append("%s — %s" % (onde, msg))
        print("      aviso: %s" % msg)


def preparar(ctx, chaves: list[str]) -> None:
    """Consentimento negado e banner escondido, antes de qualquer página.

    Negar por localStorage em vez de clicar em "aceitar": o robô não deve
    conceder consentimento de medição, e o banner não deve ficar na frente dos
    cliques. O CSS cobre o caso de um site com chave diferente das conhecidas.
    """
    js = ";".join("try{localStorage.setItem('%s','denied')}catch(e){}" % k for k in chaves)
    ctx.add_init_script(js)
    ctx.add_init_script(
        "document.addEventListener('DOMContentLoaded',function(){"
        "var s=document.createElement('style');"
        "s.textContent='.cookie-banner{display:none!important}';"
        "document.head.appendChild(s);});")


def bloquear_anuncios(pagina) -> None:
    """Responde 204 vazio no lugar de anúncio e medição.

    Com route.abort() o navegador registra "Failed to load resource:
    net::ERR_FAILED" no console, e o próprio robô contava isso como defeito do
    site: dezesseis falhas inventadas na primeira execução. Responder 204 vazio
    bloqueia igual e não deixa rastro de erro.
    """
    def rota(route):
        if any(h in route.request.url for h in HOSTS_BLOQUEADOS):
            return route.fulfill(status=204, body="", headers={"content-type": "text/plain"})
        return route.continue_()
    pagina.route("**/*", rota)


# Mensagens de console que não dizem nada sobre a saúde do site.
RUIDO_CONSOLE = (
    "failed to load resource",        # coberto por requestfailed, com a URL
    "err_blocked_by_client",
    "preloaded using link preload",   # dica de performance do Chrome
)


def ligar_escutas(pagina, erros: list[str], dominios: set[str]) -> None:
    """Captura o que de fato indica defeito, e só isso.

    * pageerror: exceção de JS não tratada, sempre é defeito;
    * console.error: defeito, menos o ruído conhecido;
    * requestfailed: só quando o recurso é do próprio site. Terceiro que cai
      não é problema nosso, e o que o robô bloqueou de propósito, menos ainda.
    """
    pagina.on("pageerror", lambda e: erros.append("exceção de JS: %s" % e))

    def no_console(m):
        if m.type != "error":
            return
        t = m.text.strip()
        if any(r in t.lower() for r in RUIDO_CONSOLE):
            return
        erros.append("console.error: %s" % t)
    pagina.on("console", no_console)

    def no_falho(req):
        url = req.url
        if any(h in url for h in HOSTS_BLOQUEADOS):
            return
        if not any(("//%s/" % d) in url or ("//www.%s/" % d) in url for d in dominios):
            return
        erros.append("recurso do site não carregou: %s" % url[:120])
    pagina.on("requestfailed", no_falho)


def conferir_pagina(pagina, url: str, rel: Relatorio, erros: list[str]) -> bool:
    """Abre a URL e confere o básico. Devolve False se nem abriu."""
    erros.clear()
    try:
        resp = pagina.goto(url, wait_until="domcontentloaded", timeout=45000)
    except PwError as e:
        rel.falha(url, "não abriu: %s" % str(e).split("\n")[0][:110])
        return False
    if resp is None:
        rel.falha(url, "sem resposta HTTP")
        return False
    if resp.status >= 400:
        rel.falha(url, "HTTP %d" % resp.status)
        return False
    rel.paginas += 1

    titulo = (pagina.title() or "").strip()
    if not titulo:
        rel.aviso(url, "<title> vazio")

    pagina.wait_for_timeout(400)
    for e in list(erros):
        rel.falha(url, "erro de JS na página: %s" % e[:110])
    return True


def clicar_widgets(pagina, url: str, rel: Relatorio, erros: list[str],
                   rnd: random.Random, quantos: int) -> None:
    """Clica em alguns widgets ao acaso e confere que nada estoura."""
    try:
        alvos = pagina.locator(SEL_WIDGET)
        n = alvos.count()
    except PwError:
        return
    if not n:
        return
    indices = list(range(n))
    rnd.shuffle(indices)
    for i in indices[:quantos]:
        el = alvos.nth(i)
        try:
            if not el.is_visible():
                continue
            el.click(timeout=4000)
            rel.cliques += 1
            pagina.wait_for_timeout(180)
        except PwError:
            continue  # elemento coberto ou que saiu do DOM não é defeito
        for e in list(erros):
            rel.falha(url, "erro de JS depois de um clique: %s" % e[:110])
            erros.clear()


def texto_resultado(pagina, espera_ms: int = 1200) -> str:
    """Texto do painel de resultado, se ele aparecer."""
    try:
        alvo = pagina.locator(SEL_RESULTADO).first
        alvo.wait_for(state="visible", timeout=espera_ms)
        return alvo.inner_text(timeout=4000)
    except PwError:
        return ""


def exercitar_calculadora(pagina, url: str, rel: Relatorio, erros: list[str]) -> None:
    """Clica em "Ver exemplo", envia o formulário e confere que sai número.

    Não sabe o valor certo de cada calculadora, mas sabe que uma calculadora
    que não devolve nenhum número depois do exemplo pré-montado está quebrada.
    """
    try:
        botao = pagina.locator(SEL_EXEMPLO).first
        if botao.count() == 0 or not botao.is_visible():
            return
        botao.click(timeout=5000)
        rel.cliques += 1
        pagina.wait_for_timeout(300)
    except PwError:
        return

    try:
        enviar = pagina.locator("form button[type=submit]").first
        if enviar.count() == 0:
            return
        enviar.click(timeout=5000)
        rel.cliques += 1
    except PwError:
        return

    txt = texto_resultado(pagina)
    if not txt:
        rel.falha(url, "o exemplo pré-montado não produziu resultado")
        return
    if not re.search(r"\d", txt):
        rel.falha(url, "resultado sem nenhum número: %r" % txt[:80])
    for e in list(erros):
        rel.falha(url, "erro de JS ao calcular: %s" % e[:110])
        erros.clear()


def rodar_golden(pagina, caso: dict, rel: Relatorio, erros: list[str]) -> None:
    url, nome = caso["url"], caso["nome"]
    print("   %s" % nome)
    if not conferir_pagina(pagina, url, rel, erros):
        return

    try:
        if caso.get("exemplo"):
            exercitar_calculadora(pagina, url, rel, erros)
            rel.golden_ok += 1
            return

        if "textareas" in caso:
            tas = pagina.locator("textarea")
            if tas.count() < len(caso["textareas"]):
                rel.falha(url, "esperava %d textarea, achei %d"
                          % (len(caso["textareas"]), tas.count()))
                return
            for i, v in enumerate(caso["textareas"]):
                tas.nth(i).fill(v)

        if "placeholders" in caso:
            for sel in caso["placeholders"]:
                ph = pagina.locator(sel).get_attribute("placeholder") or ""
                if not ph.strip():
                    rel.falha(url, "%s está sem placeholder para conferir" % sel)
                    return
                pagina.locator(sel).fill(ph)

        for sel, v in (caso.get("campos") or {}).items():
            pagina.locator(sel).fill(v)

        pagina.locator("form button[type=submit]").first.click(timeout=6000)
    except PwError as e:
        rel.falha(url, "não deu para preencher/enviar: %s" % str(e).split("\n")[0][:100])
        return

    txt = texto_resultado(pagina, 3000)
    if not txt:
        rel.falha(url, "nenhum resultado apareceu")
        return

    plano = re.sub(r"\s+", " ", txt)
    for padrao, esperado, tol in caso.get("numeros", []):
        m = re.search(padrao, plano)
        if not m:
            rel.falha(url, "não achei %s no resultado: %r" % (padrao, plano[:90]))
            continue
        obtido = pt_float(m.group(1))
        if obtido is None or abs(obtido - esperado) > tol:
            rel.falha(url, "%s: esperava %s, veio %s" % (nome, esperado, obtido))
    for s in caso.get("contem", []):
        if s.lower() not in plano.lower():
            rel.falha(url, "o resultado não traz %r: %r" % (s, plano[:90]))
    for s in caso.get("nao_contem", []):
        if s.lower() in plano.lower():
            rel.falha(url, "o resultado traz %r, que indica conclusão invertida" % s)
    for e in list(erros):
        rel.falha(url, "erro de JS: %s" % e[:110])
        erros.clear()
    rel.golden_ok += 1


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--sites", nargs="*", default=None,
                    help="domínios a visitar (padrão: todos)")
    ap.add_argument("--paginas", type=int, default=5,
                    help="páginas por site, sorteadas do sitemap (padrão: 5)")
    ap.add_argument("--cliques", type=int, default=3,
                    help="widgets clicados por página (padrão: 3)")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--so-golden", action="store_true",
                    help="só as contas de valor conhecido")
    ap.add_argument("--pausa", type=float, default=1.0,
                    help="segundos entre páginas, para não pesar no site")
    args = ap.parse_args()

    semente = args.seed if args.seed is not None else random.randrange(1, 10 ** 9)
    rnd = random.Random(semente)
    print("=" * 72)
    print("Teste de fumaça dos sites · semente %d" % semente)
    print("Para repetir esta execução: --seed %d" % semente)
    print("=" * 72)

    dominios = list(SITES) if args.sites is None else args.sites
    desconhecidos = [d for d in dominios if d not in SITES]
    if desconhecidos:
        print("domínio desconhecido: %s" % ", ".join(desconhecidos), file=sys.stderr)
        return 2

    rel = Relatorio()
    erros: list[str] = []

    with sync_playwright() as pw:
        navegador = pw.chromium.launch()
        ctx = navegador.new_context(
            user_agent=UA, viewport={"width": 1280, "height": 900},
            locale="pt-BR")
        preparar(ctx, sorted(set(SITES.values())))
        pagina = ctx.new_page()
        bloquear_anuncios(pagina)
        ligar_escutas(pagina, erros, set(SITES))

        # 1) as contas de valor conhecido, que são o coração do teste
        print("\n--- contas conferidas contra o SciPy")
        for caso in GOLDEN:
            if args.sites is not None:
                if not any(d in caso["url"] for d in dominios):
                    continue
            rodar_golden(pagina, caso, rel, erros)
            time.sleep(args.pausa)

        # 2) a caminhada aleatória
        if not args.so_golden:
            for dom in dominios:
                print("\n--- %s" % dom)
                try:
                    urls = urls_do_sitemap(dom)
                except Exception as e:  # noqa: BLE001
                    rel.falha(dom, "sitemap.xml não pôde ser lido: %s"
                              % str(e).split("\n")[0][:100])
                    continue
                if not urls:
                    rel.falha(dom, "sitemap.xml sem nenhuma URL")
                    continue
                escolhidas = rnd.sample(urls, min(args.paginas, len(urls)))
                for u in escolhidas:
                    print("   %s" % u.replace("https://" + dom, "") or "/")
                    if not conferir_pagina(pagina, u, rel, erros):
                        continue
                    clicar_widgets(pagina, u, rel, erros, rnd, args.cliques)
                    exercitar_calculadora(pagina, u, rel, erros)
                    time.sleep(args.pausa)

        navegador.close()

    print("\n" + "=" * 72)
    print("%d páginas, %d cliques, %d/%d contas conferidas"
          % (rel.paginas, rel.cliques, rel.golden_ok, len(GOLDEN)))
    print("%d falha(s), %d aviso(s)" % (len(rel.falhas), len(rel.avisos)))
    if rel.avisos:
        print("\nAvisos (não derrubam a execução):")
        for a in rel.avisos[:20]:
            print("  · %s" % a)
    if rel.falhas:
        print("\nFALHAS:")
        for f in rel.falhas:
            print("  · %s" % f)

    resumo = os.environ.get("GITHUB_STEP_SUMMARY")
    if resumo:
        with open(resumo, "a", encoding="utf-8") as fh:
            fh.write("## Teste de fumaça dos sites\n\n")
            fh.write("Semente `%d` · %d páginas · %d cliques · "
                     "%d/%d contas conferidas\n\n"
                     % (semente, rel.paginas, rel.cliques, rel.golden_ok, len(GOLDEN)))
            if rel.falhas:
                fh.write("### %d falha(s)\n\n" % len(rel.falhas))
                for f in rel.falhas:
                    fh.write("- %s\n" % f)
                fh.write("\nPara repetir: `python tools/smoke_sites.py --seed %d`\n"
                         % semente)
            else:
                fh.write("Nenhuma falha.\n")
            if rel.avisos:
                fh.write("\n### %d aviso(s)\n\n" % len(rel.avisos))
                for a in rel.avisos[:30]:
                    fh.write("- %s\n" % a)

    return 1 if rel.falhas else 0


if __name__ == "__main__":
    sys.exit(main())
