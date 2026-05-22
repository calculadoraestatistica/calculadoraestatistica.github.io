# Calculadora Estatística

Site estático de **calculadoras estatísticas online, gratuitas e em português**,
com explicação didática de cada teste. Publicado via **GitHub Pages** com
domínio próprio: <https://calculadoraestatistica.com.br>

## O que tem no site

**Calculadoras** (cálculo 100% no navegador, sem servidor):

| Página | Teste |
|---|---|
| `teste-ab.html` | Teste A/B — significância de duas proporções |
| `tamanho-amostra-ab.html` | Tamanho de amostra e duração de um teste A/B |
| `teste-t.html` | Teste t de Student (uma amostra, duas amostras, pareado) |
| `teste-z.html` | Teste z para uma média |
| `teste-proporcao.html` | Teste de proporção (uma e duas proporções) |
| `qui-quadrado.html` | Qui-quadrado de independência (tabela de contingência) |
| `k-amostras.html` | ANOVA de uma via e Kruskal-Wallis (3+ grupos) |
| `wilcoxon.html` | Wilcoxon e Mann-Whitney (não-paramétricos, 2 grupos) |
| `intervalo-confianca.html` | Intervalo de confiança (média e proporção) |
| `tamanho-amostra.html` | Tamanho de amostra para pesquisas |

**Guias** (`/guias/`): estatística para enfermagem, para psicologia, para
marketing/CRO e um guia de como escolher o teste estatístico certo.

**Institucional:** `index.html`, `sobre.html`, `privacidade.html`, `404.html`.

## Estrutura

```
/
├── index.html, teste-*.html, qui-quadrado.html, k-amostras.html, wilcoxon.html,
│   intervalo-confianca.html, tamanho-*.html, sobre/privacidade/404
├── guias/                  artigos e guia de escolha de teste
├── css/style.css           folha de estilo única (responsiva)
├── js/
│   ├── stats.js            núcleo estatístico (funções puras, testado)
│   ├── config.js           configuração (ID do AdSense)
│   └── app.js              menu, rodapé, anúncios, utilidades
├── favicon.svg, og-image.png, site.webmanifest
├── CNAME                   domínio próprio (GitHub Pages)
├── robots.txt, sitemap.xml, .nojekyll
```

Não há etapa de build: é HTML/CSS/JS puro.

## Rodar localmente

Como as páginas usam caminhos absolutos (`/css/...`), abra com um servidor HTTP
(não com `file://`):

```bash
python -m http.server 8000
# acesse http://localhost:8000
```

## Publicar (GitHub Pages + domínio próprio)

1. O conteúdo é servido da branch `main` do repositório no GitHub.
2. O arquivo `CNAME` (com `calculadoraestatistica.com.br`) faz o GitHub Pages
   usar o domínio próprio.
3. No painel do registrador do domínio, configure o DNS apontando para o
   GitHub Pages:
   - **Domínio raiz** (`calculadoraestatistica.com.br`) — 4 registros `A`:
     `185.199.108.153`, `185.199.109.153`, `185.199.110.153`, `185.199.111.153`
   - **www** — um registro `CNAME` para `calculadoraestatistica.github.io`
4. Em **Settings → Pages** do repositório, confirme o domínio próprio e ative
   **Enforce HTTPS** (após o certificado ser emitido).

Depois disso, cada `git push` para a `main` atualiza o site.

## Monetização — ativar o Google AdSense

Os espaços de anúncio (`<div class="ad-slot">`) já estão posicionados nas
páginas (após o resultado e no meio dos artigos). Enquanto o AdSense não estiver
configurado, eles ficam ocultos e o site funciona normalmente.

Para ativar, após a aprovação da conta:

1. Abra `js/config.js`.
2. Preencha `adsenseClient` com o seu ID de publisher (ex.: `"ca-pub-XXXXXXXXXXXXXXXX"`).
3. Salve e faça `git push`.

**Afiliados:** as caixas `class="recommend"` têm um comentário HTML indicando
onde inserir links de parceiros (cursos, livros) quando desejar.

## Núcleo estatístico

`js/stats.js` implementa, sem dependências externas:

- distribuição normal (CDF, inversa) — algoritmo de Acklam;
- distribuição t de Student, qui-quadrado e F — via funções beta e gama incompletas;
- testes: A/B, tamanho de amostra, teste t, teste z, proporção, intervalo de
  confiança (Wilson), qui-quadrado, ANOVA, Kruskal-Wallis, Mann-Whitney e Wilcoxon.

As funções foram verificadas contra valores de referência conhecidos
(z, t, χ² e F críticos tabelados, e exemplos resolvidos).

---

© Calculadora Estatística — finalidade educacional e informativa.
