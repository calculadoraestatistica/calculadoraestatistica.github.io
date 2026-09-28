# -*- coding: utf-8 -*-
"""Acrescenta sinais de manutenção às páginas de conteúdo.

O AdSense recusou este site por "conteúdo de baixo valor" citando, entre outros
critérios, "curadoria e manutenção estruturais contínuas". O site tem quatro
meses de manutenção registrada em git e nada disso aparecia: nenhuma data
visível, nenhum dateModified, nenhum autor nos dados estruturados.

Este script preenche essa lacuna usando as datas REAIS do repositório. A data de
criação é a do primeiro commit que tocou o arquivo e a de revisão é a do último.
Nenhuma é inventada, e páginas fora do controle de versão são puladas.

    & "C:/Users/vinyn/miniconda3/python.exe" tests/marcar_revisao.py
"""
from __future__ import annotations

import datetime
import glob
import io
import os
import re
import subprocess

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(AQUI)
SITE = "https://calculadoraestatistica.com.br"
MESES = ("janeiro", "fevereiro", "março", "abril", "maio", "junho", "julho",
         "agosto", "setembro", "outubro", "novembro", "dezembro")

MARCA_SCHEMA = "<!-- revisao-schema -->"
MARCA_LINHA = "<!-- revisao-linha -->"


def datas_git(rel: str):
    def log(*args):
        p = subprocess.run(["git", "log"] + list(args) + ["--date=short", "--pretty=%ad", "--", rel],
                           cwd=RAIZ, capture_output=True, text=True)
        return [l for l in p.stdout.split("\n") if l.strip()]
    todas = log()
    if not todas:
        return None, None
    return todas[-1], todas[0]          # criação, última alteração


def extenso(iso: str) -> str:
    d = datetime.date.fromisoformat(iso)
    return "%d de %s de %d" % (d.day, MESES[d.month - 1], d.year)


def main() -> int:
    alvos = []
    for f in sorted(glob.glob(os.path.join(RAIZ, "*.html")) +
                    glob.glob(os.path.join(RAIZ, "artigos", "*.html")) +
                    glob.glob(os.path.join(RAIZ, "guias", "*.html"))):
        h = io.open(f, encoding="utf-8").read()
        # páginas de conteúdo são as que carregam anúncio; serviço e jurídico não
        if "adsbygoogle" in h and not f.endswith(("404.html", "_template.html")):
            alvos.append(f)

    feitos = pulados = 0
    for f in alvos:
        rel = os.path.relpath(f, RAIZ).replace("\\", "/")
        h = io.open(f, encoding="utf-8").read()
        if MARCA_SCHEMA in h:
            pulados += 1
            continue
        criada, alterada = datas_git(rel)
        if not criada:
            pulados += 1
            continue

        titulo = re.search(r"(?is)<h1[^>]*>(.*?)</h1>", h)
        titulo = re.sub(r"<[^>]+>", "", titulo.group(1)).strip() if titulo else rel

        schema = (
          '%s\n<script type="application/ld+json">{"@context":"https://schema.org",'
          '"@type":"WebPage","name":%s,"url":"%s/%s",'
          '"datePublished":"%s","dateModified":"%s","inLanguage":"pt-BR",'
          '"isPartOf":{"@type":"WebSite","name":"Calculadora Estatística","url":"%s/"},'
          '"author":{"@type":"Organization","name":"Calculadora Estatística","url":"%s/"},'
          '"publisher":{"@type":"Organization","name":"Calculadora Estatística","url":"%s/",'
          '"logo":{"@type":"ImageObject","url":"%s/favicon-512.png"}}}</script>\n'
          % (MARCA_SCHEMA, '"%s"' % titulo.replace('"', "'"), SITE,
             rel if rel != "index.html" else "", criada, alterada, SITE, SITE, SITE, SITE))
        h = h.replace("</head>", schema + "</head>", 1)

        linha = (
          '%s\n  <div class="container narrow"><p class="revisao">'
          'Publicada em %s e revisada pela última vez em %s. '
          'As contas desta página são conferidas contra o SciPy na '
          '<a href="/validacao.html">validação numérica</a>, e o que mudou no site está no '
          '<a href="/historico.html">histórico</a>.</p></div>\n'
          % (MARCA_LINHA, extenso(criada), extenso(alterada)))
        h = h.replace("</main>", linha + "</main>", 1)

        io.open(f, "w", encoding="utf-8").write(h)
        print("  %-44s %s -> %s" % (rel, criada, alterada))
        feitos += 1

    print()
    print("%d páginas marcadas, %d puladas" % (feitos, pulados))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
