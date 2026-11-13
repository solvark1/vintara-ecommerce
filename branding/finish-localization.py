from pathlib import Path
base=Path('source/CE-PhoenixCart-PhoenixCart-1c2161d')
out=Path('branding/overlay')
extra={
'includes/languages/english/system/versioned/1.0.7.other/1.0.7.12/product.php':{'In Stock':'Disponible','Out Of Stock':'Agotado'},
'includes/languages/english/modules/content/shopping_cart/cm_sc_title.php':{"What\\'s In My Cart?":'Tu carrito'},
'includes/languages/english/modules/content/shopping_cart/cm_sc_product_listing.php':{"= 'Product';":"= 'Producto';","= 'Stock';":"= 'Disponibilidad';","= 'Qty';":"= 'Cant.';","= 'Price';":"= 'Precio';",'title="Update"':'title="Actualizar"','title="Remove"':'title="Quitar"'},
'includes/languages/english/modules/content/shopping_cart/cm_sc_order_subtotal.php':{'Sub-Total':'Subtotal'},
'includes/languages/english/modules/content/shopping_cart/cm_sc_checkout.php':{"= 'Checkout';":"= 'Continuar compra';"},
}
for relative,replacements in extra.items():
    text=(base/relative).read_text(encoding='utf-8-sig')
    for old,new in replacements.items(): text=text.replace(old,new)
    target=out/relative;target.parent.mkdir(parents=True,exist_ok=True);target.write_text(text,encoding='utf-8')
relative='templates/override/includes/modules/content/header/tpl_cm_header_menu.php'
text=(base/'includes/modules/content/header/templates/tpl_cm_header_menu.php').read_text(encoding='utf-8')
prefix='''<?php
// Hide empty original sample categories while retaining their records in the database.
$activeRootQuery=$GLOBALS['db']->query("WITH RECURSIVE active_categories AS (SELECT DISTINCT c.categories_id,c.parent_id FROM categories c JOIN products_to_categories pc ON pc.categories_id=c.categories_id JOIN products p ON p.products_id=pc.products_id WHERE p.products_status=1 UNION DISTINCT SELECT c.categories_id,c.parent_id FROM categories c JOIN active_categories a ON a.parent_id=c.categories_id) SELECT categories_id FROM active_categories WHERE parent_id=0");
$activeRoots=array_fill_keys(array_column($activeRootQuery->fetch_all(MYSQLI_ASSOC),'categories_id'),true);
?>
'''
text=text.replace('foreach ($category_tree->get_children($category_tree->get_root_id()) as $e) {','foreach ($category_tree->get_children($category_tree->get_root_id()) as $e) {\n            if (!isset($activeRoots[(int)$e])) continue;')
target=out/relative;target.parent.mkdir(parents=True,exist_ok=True);target.write_text(prefix+text,encoding='utf-8')
print('Navigation and cart translations prepared.')
