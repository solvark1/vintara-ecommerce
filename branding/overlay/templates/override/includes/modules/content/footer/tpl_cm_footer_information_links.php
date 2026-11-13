<div class="<?= MODULE_CONTENT_FOOTER_INFORMATION_CONTENT_WIDTH ?> cm-footer-information-links tn-footer-col">
 <h2 class="tn-footer-heading">Información</h2><nav class="tn-footer-links" aria-label="Información">
 <?php foreach(MODULE_CONTENT_FOOTER_INFORMATION_DATA as $page=>$text){ ?><a href="<?= $GLOBALS['Linker']->build($page) ?>"><?= $text ?></a><?php } ?>
 </nav>
</div>
