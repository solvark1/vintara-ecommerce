<div class="<?= MODULE_CONTENT_FOOTER_ACCOUNT_CONTENT_WIDTH ?> cm-footer-account tn-footer-col">
 <h2 class="tn-footer-heading">Tu cuenta</h2>
 <nav class="tn-footer-links" aria-label="Tu cuenta">
 <?php if(isset($_SESSION['customer_id'])) { ?>
 <a href="<?= $GLOBALS['Linker']->build('account.php') ?>">Mi cuenta</a>
 <a href="<?= $GLOBALS['Linker']->build('account_history.php') ?>">Mis pedidos</a>
 <a href="<?= $GLOBALS['Linker']->build('address_book.php') ?>">Mis direcciones</a>
 <a href="<?= $GLOBALS['Linker']->build('logoff.php') ?>">Cerrar sesión</a>
 <?php } else { ?>
 <a href="<?= $GLOBALS['Linker']->build('login.php') ?>">Iniciar sesión</a>
 <a href="<?= $GLOBALS['Linker']->build('create_account.php') ?>">Crear una cuenta</a>
 <?php } ?>
 </nav>
</div>
