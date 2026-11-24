<?php

class hook_shop_siteWide_tawkChat {

  public function listen_injectBodyEnd() {
    if (basename(Request::get_page()) !== 'index.php'
        || !empty($_GET['cPath'])
        || !empty($_GET['manufacturers_id'])) {
      return;
    }

    return <<<'HTML'
<script type="text/javascript">
var Tawk_API = Tawk_API || {}, Tawk_LoadStart = new Date();
(function(){
var s1 = document.createElement("script"), s0 = document.getElementsByTagName("script")[0];
s1.async = true;
s1.src = 'https://embed.tawk.to/6af12cbf6e09e53c4278181d/1k6v1diof';
s1.charset = 'UTF-8';
s1.setAttribute('crossorigin', '*');
s0.parentNode.insertBefore(s1, s0);
})();
</script>
HTML;
  }

}
