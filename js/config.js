/* ==========================================================================
   config.js — Configuração do site
   --------------------------------------------------------------------------
   MONETIZAÇÃO (Google AdSense)
   Enquanto "adsenseClient" estiver vazio, os espaços de anúncio ficam ocultos
   e o site funciona normalmente, sem nenhum anúncio.

   Quando a sua conta do Google AdSense for aprovada:
     1. Copie o seu ID de publisher (algo como "ca-pub-1234567890123456").
     2. Cole-o no campo "adsenseClient" abaixo e salve.
     3. Pronto: a biblioteca do AdSense é carregada e os anúncios aparecem
        nos espaços já posicionados (após o resultado e no meio dos artigos).
        Com os "Anúncios automáticos" ligados no painel do AdSense, o Google
        cuida do posicionamento sozinho.

   Para controle manual, crie unidades de anúncio no painel do AdSense e
   preencha o atributo data-ad-slot de cada <div class="ad-slot"> nas páginas.
   ========================================================================== */
window.SITE_CONFIG = {
  // Cole aqui o seu ID do AdSense quando tiver. Ex.: "ca-pub-1234567890123456"
  adsenseClient: "",

  // Endereço público do site (usado em metadados).
  baseUrl: "https://calculadoraestatistica.com.br"
};
