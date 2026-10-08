# -*- coding: utf-8 -*-
"""Escreve validacao.html a partir de tests/_validacao.json.

A página existe porque um site de calculadora pede que o leitor confie em
números que ele não tem como conferir. Publicar a conferência resolve isso: os
mesmos dados entram nas duas implementações e os dois resultados ficam à vista.

    & "C:/Users/vinyn/miniconda3/python.exe" tests/gerar_validacao.py
    & "C:/Users/vinyn/miniconda3/python.exe" tests/gerar_pagina_validacao.py

Usa metodologia.html como molde, para a página nascer com o mesmo cabeçalho,
rodapé e folha de estilo do resto do site.
"""
from __future__ import annotations

import datetime
import io
import json
import os
import re
import subprocess

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(AQUI)
HOJE = datetime.date.today()
MESES = ("janeiro", "fevereiro", "março", "abril", "maio", "junho", "julho",
         "agosto", "setembro", "outubro", "novembro", "dezembro")
DATA_EXT = "%d de %s de %d" % (HOJE.day, MESES[HOJE.month - 1], HOJE.year)

D = json.load(io.open(os.path.join(AQUI, "_validacao.json"), encoding="utf-8"))
CASOS, RESSALVAS = D["casos"], D["ressalvas"]

try:
    NODE = subprocess.run(["node", "--version"], capture_output=True, text=True).stdout.strip()
except OSError:
    NODE = "Node.js"


def contar_assercoes() -> int:
    """Quantas asserções a suíte roda de verdade.

    Estava escrito à mão como 41 aqui dentro, então a página continuou
    publicando 41 depois de a suíte crescer. O número agora sai da saída do
    próprio teste, do mesmo jeito que a versão do Node sai de `node --version`.
    """
    try:
        saida = subprocess.run(
            ["node", os.path.join(AQUI, "test_calculadoras.js")],
            capture_output=True, text=True, encoding="utf-8", timeout=120).stdout
        m = re.search(r"(\d+)\s*/\s*(\d+)\s+asserções", saida)
        if m:
            return int(m.group(2))
    except (OSError, subprocess.SubprocessError):
        pass
    return 0


def num(v: float) -> str:
    """Número com casas suficientes para o leitor conferir, em português."""
    if v is None:
        return "&mdash;"
    if v == int(v) and abs(v) < 1e6:
        return str(int(v))
    s = "%.10g" % v if abs(v) >= 1e-4 else "%.3e" % v
    return s.replace(".", ",")


def dif(v: float) -> str:
    if v is None:
        return "&mdash;"
    if v == 0:
        return "0 (idêntico)"
    return ("%.0e" % v).replace("e-0", "e&minus;").replace("e-", "e&minus;")


# ── Tabela principal ───────────────────────────────────────────────────────
linhas = []
for c in CASOS:
    primeiro = True
    for l in c["linhas"]:
        nome = ('<th scope="row" rowspan="%d"><a href="/%s">%s</a><span class="val__in">%s</span></th>'
                % (len(c["linhas"]), c["pagina"], c["nome"], c["entrada"])) if primeiro else ""
        linhas.append(
            "<tr>%s<td>%s</td><td>%s</td><td>%s</td><td class=\"val__dif\">%s</td></tr>"
            % (nome, l["grandeza"], num(l["site"]), num(l["ref"]), dif(l["dif"])))
        primeiro = False

total = sum(len(c["linhas"]) for c in CASOS)
divergentes = sum(1 for c in CASOS for l in c["linhas"]
                  if l["dif"] is None or l["dif"] > 1e-6)

tabela = (
  '<div class="table-wrap"><table class="data val">'
  '<caption>Cada grandeza calculada duas vezes, com a mesma entrada, por dois programas independentes.</caption>'
  '<thead><tr><th scope="col">Calculadora e entrada</th><th scope="col">Grandeza</th>'
  '<th scope="col">Este site</th><th scope="col">SciPy</th>'
  '<th scope="col">Diferença</th></tr></thead><tbody>'
  + "".join(linhas) + "</tbody></table></div>")

# ── Ressalvas ──────────────────────────────────────────────────────────────
res_linhas = "".join(
  "<tr><th scope=\"row\"><a href=\"/%s\">%s</a></th><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>"
  % (r["pagina"], r["nome"], r["n"], num(r["p_usado"]), num(r["p_alternativo"]),
     r["alternativo"])
  for r in RESSALVAS)

# ── Conteúdo da página ─────────────────────────────────────────────────────
MAIN = """<main id="conteudo">

  <div class="page-head">
    <div class="container">
      <nav class="breadcrumb" aria-label="Trilha de navegação">
        <ol>
          <li><a href="/">Início</a></li>
          <li>Validação numérica</li>
        </ol>
      </nav>
      <h1>Validação numérica</h1>
      <p class="lead">Todo site de calculadora pede que você confie num número que não tem como
        conferir. Esta página existe para você não precisar confiar: cada calculadora é rodada
        contra uma implementação independente e os dois resultados ficam publicados lado a lado.</p>
    </div>
  </div>

  <div class="container narrow">
    <article class="prose">

      <p class="val__selo"><strong>%(total)d grandezas conferidas, %(divergentes)d divergentes.</strong>
        Última execução em %(data)s.</p>

      <h2>Como a conferência é feita</h2>
      <p>As calculadoras deste site são escritas em JavaScript e rodam no seu navegador. Isso é bom
        para a sua privacidade, porque nenhum dado sai do seu computador, e ruim para a sua
        confiança, porque você não tem como saber se a conta está certa.</p>
      <p>A conferência resolve isso comparando com o <a href="https://scipy.org/" rel="noopener"
        target="_blank">SciPy</a>, a biblioteca estatística usada em pesquisa acadêmica e na
        indústria há mais de duas décadas. O mesmo conjunto de números entra nas duas
        implementações. Se as duas chegam ao mesmo resultado, o erro teria que estar nas duas ao
        mesmo tempo e do mesmo jeito.</p>
      <p>Nada aqui é escrito à mão. A tabela é gerada por um script que roda as duas
        implementações no momento da geração, então ela não tem como ficar desatualizada em
        relação ao código sem que alguém perceba.</p>

      <h2>O resultado</h2>
      %(tabela)s
      <p class="val__nota">As diferenças na ordem de 10⁻⁹ ou menores são ruído de ponto flutuante,
        não discordância: computador guarda número decimal com precisão finita, e duas rotinas
        diferentes chegam ao mesmo valor com o último dígito diferente. Para efeito prático, uma
        diferença dessa ordem não muda nenhuma decisão.</p>

      <h2>Onde este site é menos preciso, e por quê</h2>
      <p>Em dois testes não paramétricos a conta deste site usa a <strong>aproximação normal</strong>,
        que é o método dos livros-texto e o que a maioria dos programas mostra por padrão. Para
        amostra pequena existe alternativa melhor: a <strong>distribuição exata</strong>, que o
        SciPy e o R usam automaticamente quando o número de observações é baixo.</p>
      <p>Os dois valores estão abaixo. A diferença aparece a partir da terceira casa decimal, e é
        maior quanto menor a amostra.</p>
      <div class="table-wrap"><table class="data val">
        <caption>Diferença entre os dois métodos, nos mesmos dados.</caption>
        <thead><tr><th scope="col">Teste</th><th scope="col">Amostra</th>
          <th scope="col">Valor-p deste site</th><th scope="col">Valor-p exato</th>
          <th scope="col">Método alternativo</th></tr></thead>
        <tbody>%(ressalvas)s</tbody></table></div>
      <p>Na prática: se o seu valor-p ficar perto do limiar que você usa para decidir, e a sua
        amostra tiver menos de vinte observações, confira no R ou no Python antes de concluir.
        Quando a amostra é grande, os dois métodos convergem e a diferença some.</p>

      <h2>Além desta página</h2>
      <p>O site também tem uma suíte de regressão com %(assercoes)d asserções, que compara as
        funções internas contra valores de referência a cada mudança no código. Ela roda em
        %(node)s sem dependência nenhuma e falha se qualquer conta sair do lugar. A tabela acima
        é a parte que dá para publicar; a suíte é a rede de proteção de quem mexe no código.</p>

      <h2>Como refazer por conta própria</h2>
      <p>Você não precisa acreditar nesta página. As entradas de cada linha estão na primeira
        coluna, e dá para colar no programa da sua preferência. Em Python, por exemplo, um teste t
        de Welch com os mesmos números é uma linha:</p>
      <pre><code>from scipy import stats
stats.ttest_ind(grupo_a, grupo_b, equal_var=False)</code></pre>
      <p>Achou divergência que não seja ruído de ponto flutuante? Escreva para
        <a href="/contato.html">o contato do site</a> com os números que você usou. Erro de conta
        em calculadora é o pior tipo de erro que este site pode ter, e correção dessas entra na
        frente de qualquer outra coisa.</p>

      <div class="card-grid card-grid--3">
          <a class="card" href="/metodologia.html"><h3>Metodologia</h3><p>As fórmulas por trás de cada calculadora e o que elas não fazem.</p><span class="card__cta">Abrir →</span></a>
          <a class="card" href="/fontes.html"><h3>Fontes</h3><p>Os livros e referências em que as fórmulas se apoiam.</p><span class="card__cta">Abrir →</span></a>
          <a class="card" href="/historico.html"><h3>Histórico de mudanças</h3><p>O que mudou no site e quando.</p><span class="card__cta">Abrir →</span></a>
      </div>

    </article>
  </div>

</main>""" % dict(total=total, divergentes=divergentes, data=DATA_EXT, tabela=tabela,
                  ressalvas=res_linhas, assercoes=contar_assercoes(), node=NODE)

# ── Monta a página usando metodologia.html como molde ──────────────────────
molde = io.open(os.path.join(RAIZ, "metodologia.html"), encoding="utf-8").read()
novo = molde[:molde.index("<main")] + MAIN + molde[molde.index("</main>") + 7:]

TITULO = "Validação numérica das calculadoras | Calculadora Estatística"
DESC = ("Cada calculadora deste site conferida contra o SciPy, com os dois resultados publicados "
        "lado a lado e as diferenças de método declaradas.")

novo = re.sub(r"<title>.*?</title>", "<title>%s</title>" % TITULO, novo, flags=re.S)
novo = re.sub(r'(<meta name="description" content=")[^"]*(")', r"\1%s\2" % DESC, novo)
novo = novo.replace("https://calculadoraestatistica.com.br/metodologia.html",
                    "https://calculadoraestatistica.com.br/validacao.html")
novo = re.sub(r'(<meta property="og:title" content=")[^"]*(")',
              r"\1Validação numérica das calculadoras\2", novo)
novo = re.sub(r'(<meta property="og:description" content=")[^"]*(")', r"\1%s\2" % DESC, novo)
novo = novo.replace('"name":"Metodologia"', '"name":"Validação numérica"')

io.open(os.path.join(RAIZ, "validacao.html"), "w", encoding="utf-8").write(novo)
print("validacao.html gravada: %d grandezas, %d divergentes" % (total, divergentes))
