from pathlib import Path
base=Path('source/CE-PhoenixCart-PhoenixCart-1c2161d')
out=Path('branding/overlay')
changes={
'includes/languages/english/modules/content/index/cm_i_card_products.php':{'Our Latest Products':'Una selección para tu mesa','View All':'Ver todo'},
'includes/languages/english/modules/navbar/nb_search.php':{'Product Search':'Buscar productos','Try our Advanced Search':'Búsqueda avanzada'},
'includes/languages/english/modules/navbar/nb_special_offers.php':{'Specials':'Ofertas'},
'includes/languages/english/modules/navbar/nb_account.php':{'Account':'Mi cuenta','Sign In':'Iniciar sesión','Sign Out':'Cerrar sesión','Settings':'Mi cuenta','Orders':'Mis pedidos','Details':'Mis datos','Addresses':'Direcciones','Password':'Contraseña','Register':'Crear cuenta','you are signed in':'sesión iniciada'},
'includes/languages/english/modules/navbar/nb_shopping_cart.php':{'View Full Cart':'Ver carrito','Checkout':'Continuar compra','item(s)':'artículo(s)'},
'includes/languages/english/modules/content/footer/cm_footer_information_links.php':{'Privacy &amp; Cookie Policy':'Privacidad y cookies','Terms &amp; Conditions':'Términos de uso','Delivery &amp; Returns':'Envíos y devoluciones','Contact Us':'Contacto',"= 'Information';":"= 'Información';"},
'includes/languages/english/modules/content/footer/cm_footer_account.php':{'Customer Services':'Tu cuenta','Settings':'Mi cuenta','Addresses':'Direcciones','Orders':'Mis pedidos','Secure Sign Out':'Cerrar sesión','New? Start Here':'¿Primera visita? Crea tu cuenta','Sign In':'Iniciar sesión'},
'includes/languages/english/modules/content/footer/cm_footer_contact_us.php':{'How To Contact Us':'Encuéntranos','Contact Us':'Contacto'},
'includes/languages/english/modules/pi/product_info/pi_buy_button.php':{'Add To Cart':'Agregar al carrito'},
'includes/languages/english/modules/pi/product_info/pi_stock.php':{'In Stock':'Disponible','Out Of Stock':'Agotado'},
'includes/languages/english/modules/content/header/cm_header_breadcrumb.php':{'Catalog':'Mercado','Home':'Inicio'},
'includes/languages/english/products_new.php':{'New Products':'Nuestro mercado'},
'includes/languages/english/index.php':{'Welcome to Our Online Store':'Lo bueno nace de la tierra','New Products For':'Novedades de'},
'includes/languages/english.php':{" lang=\"en\"":" lang=\"es\"","= 'In Stock';":"= 'Disponible';","= 'Out Of Stock';":"= 'Agotado';","= 'Search';":"= 'Buscar';","= 'Close';":"= 'Cerrar';","= 'Contact Us';":"= 'Contacto';","= 'Home';":"= 'Inicio';","= 'Catalog';":"= 'Mercado';",'Shopping Cart':'Carrito','Your Shopping Cart':'Tu carrito'},
}
for relative,replacements in changes.items():
    p=base/relative
    if not p.exists():
        # The specials module name differs between Phoenix versions.
        if 'nb_special_offers' in relative:
            p=base/relative.replace('nb_special_offers','nb_specials')
            if not p.exists(): continue
            relative=str(p.relative_to(base))
        else: raise FileNotFoundError(p)
    text=p.read_text(encoding='utf-8-sig')
    for old,new in replacements.items(): text=text.replace(old,new)
    target=out/relative; target.parent.mkdir(parents=True,exist_ok=True); target.write_text(text,encoding='utf-8')
print('Generated Spanish storefront overrides.')
