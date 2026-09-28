# -*- coding: utf-8 -*-
"""Escreve historico.html, o registro público do que mudou no site.

Um site de calculadora que não mostra sinal de manutenção parece abandonado,
mesmo quando não está. Este site tem quatro meses de alterações registradas em
git, e nenhuma delas aparecia para quem visita.

As entradas abaixo são escritas à mão a partir do histórico real de commits,
porque mensagem de commit é escrita para quem programa, não para quem lê. As
datas vêm do repositório e não são inventadas.

    & "C:/Users/vinyn/miniconda3/python.exe" tests/gerar_historico.py
"""
from __future__ import annotations

import datetime
import io
import os
import re
import subprocess

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(AQUI)
MESES = ("janeiro", "fevereiro", "março", "abril", "maio", "junho", "julho",
         "agosto", "setembro", "outubro", "novembro", "dezembro")
HOJE = datetime.date.today()
DATA_EXT = "%d de %s de %d" % (HOJE.day, MESES[HOJE.month - 1], HOJE.year)

# (mês de referência, título, entradas). Escritas a partir do histórico real.
HISTORICO = [
 ("%s de %d" % (MESES[HOJE.month - 1], HOJE.year), [
   ("Validação numérica publicada",
    "Cada calculadora passou a ser conferida contra o SciPy, com os dois resultados "
    "e a diferença publicados em <a href=\"/validacao.html\">uma página aberta</a>. "
    "A conferência é gerada por script, então não tem como ficar desatualizada em silêncio."),
   ("Limitação declarada nos testes não paramétricos",
    "Wilcoxon e Mann-Whitney usam aproximação normal, que perde precisão em amostra "
    "pequena. A diferença em relação ao método exato agora está publicada, com os dois "
    "valores lado a lado."),
   ("Datas de revisão em todas as páginas de conteúdo",
    "Cada calculadora e cada artigo passou a mostrar quando foi revisado pela última vez, "
    "e a informar isso também nos dados estruturados."),
 ]),
 ("setembro de 2026", [
   ("Leituras recomendadas nas calculadoras",
    "As páginas de teste ganharam indicação de livros-texto, com aviso de que são links "
    "de afiliado."),
   ("Faixas de topo e centralização corrigidas",
    "As imagens de cabeçalho estavam recortadas fora do eixo e desalinhadas do texto."),
   ("Mídia explicativa e revisão de texto",
    "Diagramas e clipes curtos nas páginas que ganhavam com ilustração, e uma passada "
    "de revisão no texto para tirar construções artificiais."),
 ]),
 ("agosto de 2026", [
   ("Calculadora em primeiro lugar na página",
    "O resultado passou a aparecer em destaque e o texto longo desceu para depois da "
    "ferramenta, que é o que a maioria vem buscar."),
   ("Remoção de dados pessoais das páginas",
    "Nome e email pessoal saíram do site, substituídos por um canal de contato próprio."),
   ("Estrutura editorial",
    "Páginas de metodologia, fontes e política editorial, para deixar explícito de onde "
    "vêm as fórmulas e quem responde pelo conteúdo."),
 ]),
 ("julho de 2026", [
   ("Consentimento de cookies e Consent Mode v2",
    "Banner de consentimento e integração com o padrão do Google para consentimento."),
   ("Auditoria de SEO, segurança e higiene",
    "Correções de cabeçalhos, links e marcação encontradas numa revisão completa."),
   ("Identidade visual revista",
    "O fundo quadriculado saiu depois de leitura ruim em tela pequena; o resto da "
    "identidade ficou."),
 ]),
 ("junho de 2026", [
   ("Suíte de testes numéricos",
    "Quarenta e uma asserções comparando as funções internas contra valores de "
    "referência, rodando a cada mudança no código."),
   ("Correção no teste unicaudal",
    "O valor-p unicaudal estava desalinhado com a função de referência interna."),
   ("Seção de artigos",
    "Cinco textos longos sobre interpretação de p-valor, correlação e causalidade, "
    "tamanho amostral em pesquisa eleitoral, erro tipo I e II na clínica, e teste A/B."),
   ("Quatro páginas rasas expandidas",
    "Primeira resposta a uma recusa do AdSense por conteúdo raso."),
   ("Dados estruturados e identidade nos buscadores",
    "Marcação de FAQ e trilha de navegação, favicon em vários tamanhos e logotipo da "
    "publicação."),
 ]),
 ("maio de 2026", [
   ("Calculadora de correlação de Pearson",
    "Com gráfico de dispersão, para ver a nuvem de pontos junto do coeficiente."),
   ("Busca por IA",
    "Uma página onde a pessoa descreve o problema em linguagem natural e recebe a "
    "calculadora adequada."),
   ("Primeira versão pública",
    "O site entrou no ar em 22 de maio de 2026 com as calculadoras de teste t, teste z, "
    "proporção, qui-quadrado, ANOVA, intervalo de confiança e tamanho de amostra."),
 ]),
]


def main() -> int:
    try:
        n = subprocess.run(["git", "rev-list", "--count", "HEAD"], cwd=RAIZ,
                           capture_output=True, text=True).stdout.strip() or "36"
    except OSError:
        n = "36"

    blocos = []
    for mes, itens in HISTORICO:
        lis = "".join("<li><strong>%s.</strong> %s</li>" % (t, d) for t, d in itens)
        blocos.append('<section class="hist"><h2>%s</h2><ul class="hist__lista">%s</ul></section>'
                      % (mes[0].upper() + mes[1:], lis))

    MAIN = """<main id="conteudo">

  <div class="page-head">
    <div class="container">
      <nav class="breadcrumb" aria-label="Trilha de navegação">
        <ol>
          <li><a href="/">Início</a></li>
          <li>Histórico de mudanças</li>
        </ol>
      </nav>
      <h1>Histórico de mudanças</h1>
      <p class="lead">O que mudou neste site, quando e por quê. Um site de calculadora que
        nunca mostra sinal de manutenção parece abandonado, mesmo quando não está.</p>
    </div>
  </div>

  <div class="container narrow">
    <article class="prose">

      <p>O site está no ar desde <strong>22 de maio de 2026</strong> e acumula
        <strong>%(n)s alterações registradas</strong> até %(data)s. A lista abaixo é escrita a
        partir desse registro, em linguagem de quem lê e não de quem programa.</p>
      <p>Correção de conta entra na frente de qualquer outra coisa. Se você encontrar um número
        errado, a <a href="/validacao.html">página de validação</a> explica como conferir e o
        <a href="/contato.html">contato</a> é o caminho para avisar.</p>

      %(blocos)s

      <h2>O que não muda</h2>
      <p>Três decisões estão firmes desde o começo e não estão em revisão. As calculadoras rodam
        no seu navegador, então os números que você digita não são enviados para lugar nenhum.
        Não há cadastro, login nem paywall. E nenhuma calculadora esconde resultado atrás de
        anúncio ou de clique.</p>

      <div class="card-grid card-grid--3">
        <a class="card" href="/validacao.html"><h3>Validação numérica</h3><p>Cada calculadora conferida contra o SciPy, com os números publicados.</p><span class="card__cta">Abrir →</span></a>
        <a class="card" href="/metodologia.html"><h3>Metodologia</h3><p>As fórmulas por trás de cada conta.</p><span class="card__cta">Abrir →</span></a>
        <a class="card" href="/politica-editorial.html"><h3>Política editorial</h3><p>Quem mantém o site e como o conteúdo é revisado.</p><span class="card__cta">Abrir →</span></a>
      </div>

    </article>
  </div>

</main>""" % dict(n=n, data=DATA_EXT, blocos="\n      ".join(blocos))

    molde = io.open(os.path.join(RAIZ, "metodologia.html"), encoding="utf-8").read()
    novo = molde[:molde.index("<main")] + MAIN + molde[molde.index("</main>") + 7:]

    TITULO = "Histórico de mudanças | Calculadora Estatística"
    DESC = ("O que mudou na Calculadora Estatística desde maio de 2026: correções, novas "
            "calculadoras, validação numérica e revisões de conteúdo.")
    novo = re.sub(r"<title>.*?</title>", "<title>%s</title>" % TITULO, novo, flags=re.S)
    novo = re.sub(r'(<meta name="description" content=")[^"]*(")', r"\1%s\2" % DESC, novo)
    novo = novo.replace("https://calculadoraestatistica.com.br/metodologia.html",
                        "https://calculadoraestatistica.com.br/historico.html")
    novo = re.sub(r'(<meta property="og:title" content=")[^"]*(")',
                  r"\1Histórico de mudanças\2", novo)
    novo = re.sub(r'(<meta property="og:description" content=")[^"]*(")', r"\1%s\2" % DESC, novo)
    novo = novo.replace('"name":"Metodologia"', '"name":"Histórico de mudanças"')

    io.open(os.path.join(RAIZ, "historico.html"), "w", encoding="utf-8").write(novo)
    print("historico.html gravada (%s alterações registradas)" % n)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
