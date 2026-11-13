"""Reproducible, fictional wine catalogue and original vector artwork."""
from pathlib import Path
import json, html

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / 'branding/assets/vintara'
ASSETS.mkdir(parents=True, exist_ok=True)
rows = [
 ('Reserva del Valle','Tintos','Cabernet Sauvignon','2022','Valle del Maipo','Chile','Bodega Valle Sereno',14500,'Cassis, ciruela y un final de especias.','Carnes a la parrilla y quesos maduros','16–18 °C',13.5),
 ('Altura Andina','Tintos','Malbec','2023','Mendoza','Argentina','Bodega Cumbre Alta',12500,'Fruta negra, violetas y taninos envolventes.','Asados y hongos a la parrilla','16–18 °C',14),
 ('Sendero de Roble','Tintos','Tempranillo','2021','Rioja','España','Bodega Camino Viejo',18500,'Cereza madura, vainilla y notas de roble.','Cordero y quesos curados','16–18 °C',13.5),
 ('Brisa Austral','Tintos','Pinot Noir','2024','Valle de Casablanca','Chile','Bodega Costa Clara',16500,'Frambuesa, cereza y un perfil delicado.','Salmón al horno y risotto de hongos','14–16 °C',12.5),
 ('Luna de Toscana','Tintos','Sangiovese','2022','Toscana','Italia','Bodega Colina Dorada',21000,'Cereza ácida, hierbas y un final persistente.','Pasta con tomate y pizza artesanal','16–18 °C',13),
 ('Noche del Ródano','Tintos','Syrah','2023','Valle del Ródano','Francia','Bodega Riberas del Sol',22500,'Moras, pimienta negra y cuerpo intenso.','Estofados y vegetales asados','16–18 °C',14),
 ('Costa de Luz','Blancos','Sauvignon Blanc','2025','Valle de Casablanca','Chile','Bodega Costa Clara',11500,'Cítricos, hierbas frescas y acidez vibrante.','Ceviche y ensaladas frescas','8–10 °C',12.5),
 ('Sol de los Andes','Blancos','Chardonnay','2024','Mendoza','Argentina','Bodega Cumbre Alta',13500,'Manzana, pera y una textura redonda.','Pollo al horno y pastas cremosas','10–12 °C',13),
 ('Jardín del Rin','Blancos','Riesling','2024','Mosela','Alemania','Bodega Jardín del Norte',17500,'Flores blancas, durazno y un final fresco.','Cocina asiática y platos especiados','8–10 °C',11),
 ('Orilla Atlántica','Blancos','Albariño','2025','Galicia','España','Bodega Mar Abierto',19000,'Lima, fruta de hueso y notas salinas.','Mariscos y pescado a la plancha','8–10 °C',12.5),
 ('Amanecer Veneto','Blancos','Pinot Grigio','2025','Véneto','Italia','Bodega Colina Dorada',12000,'Pera fresca, limón y un cuerpo ligero.','Antipasti y ensaladas mediterráneas','8–10 °C',12),
 ('Atardecer Mediterráneo','Rosados','Garnacha','2025','Navarra','España','Bodega Camino Viejo',11000,'Fresa, sandía y una frescura delicada.','Tapas y verduras a la parrilla','8–10 °C',12.5),
 ('Pétalo de Provence','Rosados','Cinsault / Garnacha','2025','Provenza','Francia','Bodega Riberas del Sol',17500,'Frutos rojos sutiles y un final floral.','Ensaladas, sushi y pescado','8–10 °C',12),
 ('Rosa de los Andes','Rosados','Malbec','2025','Mendoza','Argentina','Bodega Cumbre Alta',10500,'Frambuesa fresca y un perfil frutal.','Empanadas y tablas de quesos suaves','8–10 °C',12.5),
 ('Brillo de Veneto','Espumantes','Glera','Sin añada','Véneto','Italia','Bodega Colina Dorada',16000,'Manzana verde y burbujas ligeras.','Aperitivos y bocados salados','6–8 °C',11),
 ('Celebración Brut','Espumantes','Macabeo / Xarel·lo / Parellada','Sin añada','Cataluña','España','Bodega Camino Viejo',18000,'Cítricos, pan tostado y burbuja fina.','Mariscos y croquetas','6–8 °C',11.5),
 ('Estrella Rosé','Espumantes','Pinot Noir / Chardonnay','Sin añada','Mendoza','Argentina','Bodega Cumbre Alta',15500,'Fresa, flores y un final vivaz.','Sushi y frutos rojos','6–8 °C',12),
 ('Éclat Reserva','Espumantes','Chardonnay / Pinot Noir','2022','Borgoña','Francia','Bodega Riberas del Sol',26500,'Brioche, manzana y una burbuja elegante.','Vieiras y quesos de pasta blanda','6–8 °C',12),
]
catalog=[]
colors={'Tintos':('#26332a','#682c40'),'Blancos':('#9f9d55','#92804f'),'Rosados':('#c88574','#bb7370'),'Espumantes':('#35473a','#aa8b49')}
for n,row in enumerate(rows,1):
    wine=dict(zip(['name','category','grape','vintage','region','country','winery','price','notes','pairing','serving','abv'],row))
    wine.update(sku=f'VIN-{n:03}',quantity=36+n*3,volume_ml=750,storage='Conservar en un lugar fresco y oscuro, sin cambios bruscos de temperatura.',image=f'vintara/vin-{n:03}.png')
    catalog.append(wine)
    glass,accent=colors[wine['category']]
    label=html.escape(wine['name']); grape=html.escape(wine['grape']); region=html.escape(wine['region'])
    svg=f'''<svg xmlns="http://www.w3.org/2000/svg" width="600" height="720" viewBox="0 0 600 720" role="img" aria-label="{label}, ilustración de botella">
<defs><linearGradient id="g"><stop stop-color="#101b16"/><stop offset=".28" stop-color="{glass}"/><stop offset=".5" stop-color="{glass}"/><stop offset="1" stop-color="#17251e"/></linearGradient><radialGradient id="bg"><stop stop-color="#fffdf8"/><stop offset="1" stop-color="#eee8dd"/></radialGradient></defs>
<rect width="600" height="720" fill="url(#bg)"/><ellipse cx="300" cy="653" rx="108" ry="14" fill="#3d2820" opacity=".14"/>
<path d="M266 81h68v125c0 35 53 48 53 95v327q0 24-24 24H237q-24 0-24-24V301c0-47 53-60 53-95z" fill="url(#g)"/>
<path d="M232 320v294" stroke="#fff" stroke-width="8" opacity=".13"/><rect x="263" y="77" width="74" height="94" rx="5" fill="{accent}"/><path d="M266 146h68" stroke="#d8bc80" stroke-width="2"/>
<rect x="225" y="342" width="150" height="202" rx="2" fill="#f5efdf"/><rect x="234" y="351" width="132" height="184" fill="none" stroke="{accent}" opacity=".5"/>
<text x="300" y="382" text-anchor="middle" font-family="Georgia,serif" font-size="19" letter-spacing="3" fill="{accent}">VINTARA</text>
<path d="M259 416l20-18 21 23 19-27 24 22M258 424h85" fill="none" stroke="{accent}" stroke-width="1.5"/>
<text x="300" y="451" text-anchor="middle" font-family="Georgia,serif" font-size="{12 if len(wine['name'])>20 else 14}" fill="#392c2a">{label}</text>
<text x="300" y="474" text-anchor="middle" font-family="Arial,sans-serif" font-size="8" fill="#6e6158">{grape}</text>
<text x="300" y="500" text-anchor="middle" font-family="Georgia,serif" font-size="15" fill="{accent}">{wine['vintage']}</text>
<text x="300" y="522" text-anchor="middle" font-family="Arial,sans-serif" font-size="8" fill="#6e6158">750 ml · {html.escape(wine['country'])}</text></svg>'''
    (ASSETS/f'vin-{n:03}.svg').write_text(svg,encoding='utf-8')
(ROOT/'docker/vintara-catalog.json').write_text(json.dumps(catalog,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
(ASSETS/'logo.svg').write_text('''<svg xmlns="http://www.w3.org/2000/svg" width="310" height="75" viewBox="0 0 310 75"><g fill="none" stroke="#682c40" stroke-width="1.6"><path d="M15 10h29c3 23-3 29-14 29S12 33 15 10zM30 39v23M18 62h24"/><path d="M17 24h25"/></g><text x="60" y="42" font-family="Georgia,serif" font-size="36" letter-spacing="5" fill="#4a2431">VINTARA</text><text x="63" y="62" font-family="Arial,sans-serif" font-size="8" letter-spacing="3.8" fill="#87704f">VINOS CON HISTORIA</text></svg>''',encoding='utf-8')
# An editorial still-life composed exclusively of our own vector illustrations.
hero='''<svg xmlns="http://www.w3.org/2000/svg" width="1000" height="1000" viewBox="0 0 1000 1000"><defs><linearGradient id="bg" x2="1" y2="1"><stop stop-color="#401f2c"/><stop offset="1" stop-color="#211a20"/></linearGradient><linearGradient id="b"><stop stop-color="#101c16"/><stop offset=".4" stop-color="#3e4a36"/><stop offset="1" stop-color="#111a15"/></linearGradient></defs><rect width="1000" height="1000" fill="url(#bg)"/><circle cx="670" cy="360" r="260" fill="#a97f58" opacity=".1"/><path d="M0 770Q450 670 1000 800v200H0" fill="#6e4c3c"/><path d="M0 833Q500 760 1000 853" fill="none" stroke="#a88667" opacity=".3"/><ellipse cx="510" cy="851" rx="270" ry="31" fill="#151215" opacity=".5"/><g transform="translate(70 80) rotate(-10 430 420)"><path d="M400 60h76v180c0 38 68 53 68 111v366q0 28-28 28H360q-28 0-28-28V351c0-58 68-73 68-111z" fill="url(#b)"/><rect x="397" y="54" width="82" height="116" rx="5" fill="#713247"/><path d="M401 143h74" stroke="#c6aa70" stroke-width="3"/><path d="M355 360v337" stroke="#fff" stroke-width="11" opacity=".1"/><rect x="346" y="401" width="184" height="222" fill="#eee3cc"/><rect x="357" y="412" width="162" height="200" fill="none" stroke="#a68a53"/><text x="438" y="454" text-anchor="middle" font-size="27" font-family="Georgia" fill="#60283b" letter-spacing="3">VINTARA</text><path d="M387 495l30-29 24 29 27-22 24 22M387 503h105" stroke="#9a794b" fill="none"/><text x="438" y="543" text-anchor="middle" font-size="18" font-family="Georgia" fill="#4a2932">Reserva del Valle</text><text x="438" y="575" text-anchor="middle" font-size="11" font-family="Arial" fill="#76624c">CABERNET SAUVIGNON</text><text x="438" y="598" text-anchor="middle" font-size="16" font-family="Georgia" fill="#60283b">2022</text></g><g fill="none" stroke="#e8d5c0" stroke-width="3" opacity=".7"><path d="M687 385h176c30 160-23 207-88 207s-117-47-88-207zM775 592v212M719 807h112"/><path d="M683 483q92 20 184 0"/></g><path d="M687 488h177c-9 70-42 98-89 98s-79-28-88-98" fill="#852c45" opacity=".65"/><text x="75" y="935" font-family="Arial" font-size="16" letter-spacing="6" fill="#e2cba8">ORIGEN · CARÁCTER · ENCUENTROS</text></svg>'''
(ASSETS/'hero.svg').write_text(hero,encoding='utf-8')
print(f'Created {len(catalog)} wines and original SVG assets.')
overlay=ROOT/'branding/overlay'
hero_template='''<?php $catalogUrl=$GLOBALS['Linker']->build('products_new.php'); ?>
<div class="col-12 mb-4 cm-i-slider tn-home">
 <div class="tn-intro"><span>VINOS CON HISTORIA</span><span>Una botella. Mil encuentros.</span></div>
 <section class="tn-hero" aria-labelledby="tn-hero-title">
  <div class="tn-hero-copy">
   <p class="tn-eyebrow">LA SELECCIÓN VINTARA</p>
   <h1 id="tn-hero-title">Del viñedo<br>a tu <em>copa.</em></h1>
   <p class="tn-hero-description">Cada origen tiene una historia. Descubrí tintos, blancos, rosados y espumantes para acompañar tus mejores momentos.</p>
   <a class="btn btn-success tn-cta" href="<?= $catalogUrl ?>">Explorar los vinos <span aria-hidden="true">↗</span></a>
   <div class="tn-hero-note">Con datos que transforman la experiencia.</div>
  </div>
  <div class="tn-hero-photo"><img src="images/vintara/hero.svg" alt="Ilustración de un vino Reserva del Valle de Vintara junto a una copa" fetchpriority="high"></div>
 </section>
 <div class="tn-values" aria-label="Nuestra propuesta">
  <div><span class="tn-value-number">01</span><span><strong>Conocé su origen</strong><small>Uva, añada, región y bodega</small></span></div>
  <div><span class="tn-value-number">02</span><span><strong>Encontrá tu estilo</strong><small>Cuatro formas de descubrir el vino</small></span></div>
  <div><span class="tn-value-number">03</span><span><strong>Elegí el maridaje</strong><small>Ideas para acompañar cada botella</small></span></div>
 </div>
</div>
'''
(overlay/'templates/override/includes/modules/content/index/tpl_cm_i_slider.php').write_text(hero_template,encoding='utf-8')
(overlay/'templates/override/includes/modules/content/footer/tpl_cm_footer_text.php').write_text('''<div class="<?= MODULE_CONTENT_FOOTER_TEXT_CONTENT_WIDTH ?> cm-footer-text tn-footer-col"><h2 class="tn-footer-heading">El mundo Vintara</h2><p>Conectamos orígenes, sabores y personas. Una selección de vinos para descubrir a tu manera.</p><span class="tn-footer-motto">Del viñedo a tu copa.</span><p class="v-demo">Catálogo académico · Sin cobros reales.<br>Solo para mayores de edad. Disfrutá con moderación.</p></div>
''',encoding='utf-8')
for path in overlay.rglob('*.php'):
    text=path.read_text(encoding='utf-8-sig')
    for a,b in [('Terra Nostra','Vintara S.A.'),('Lo bueno nace de la tierra','Del viñedo a tu copa | Vintara'),('Nuestro mercado','Nuestra colección de vinos'),("'Mercado'","'Vinos'"),('Una selección para tu mesa','Una selección con carácter'),('Discover a wide selection of products and enjoy easy online shopping with great customer service.','Descubrí vinos tintos, blancos, rosados y espumantes. Uvas, añadas, regiones y maridajes en Vintara.')]: text=text.replace(a,b)
    path.write_text(text,encoding='utf-8')
css_path=overlay/'templates/override/static/user.css'
css=css_path.read_text(encoding='utf-8-sig').split('/* VINTARA OVERRIDES */')[0]
css+='''
/* VINTARA OVERRIDES */
.cm-i-card-products>p{display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:12px}.cm-i-card-products>p .btn{float:none!important;white-space:nowrap}
:root{--tn-forest:#682c40;--tn-moss:#8a6b45;--tn-cream:#f4eee3;--tn-ink:#392831;--tn-line:#e4d9cc;--bs-success:#682c40;--bs-success-rgb:104,44,64;--bs-link-color:#682c40;--bs-link-hover-color:#873c54;--bs-body-color:#392831;--bs-body-bg:#fcfaf5}
body,.navbar.bg-body-tertiary,.navbar.bg-light{background:#fcfaf5!important;color:#392831}
a:hover{color:#873c54}.navbar-brand img{width:240px;height:62px}.nb-search input{background:#fcfaf5}
.tn-intro{color:#80694f}.tn-hero{border-radius:3px;min-height:490px}.tn-hero-copy{padding:58px 48px 40px}.tn-hero h1{font-size:clamp(3rem,5vw,5rem);color:#4a2431}.tn-hero h1 em{color:#8b4a58}.tn-hero-description{color:#74645c;max-width:365px}.tn-hero-note{color:#80694f;font-family:Georgia,serif;font-style:italic;font-size:.88rem}.tn-hero-photo{min-height:490px;background:#291d23}.tn-hero-photo img{object-position:center}.tn-value-number{color:#b39361}.tn-values small{color:#76685e}.tn-values{padding:27px 0}
.btn-success,.btn-primary{--bs-btn-bg:#682c40;--bs-btn-border-color:#682c40;--bs-btn-hover-bg:#4e2030;--bs-btn-hover-border-color:#4e2030;--bs-btn-active-bg:#4e2030;--bs-btn-active-border-color:#4e2030}
.card.is-product{background:#fcfaf5}.is-product>.card-img-top,.is-product>a>img{height:270px;object-fit:contain;background:#f2ece2;border-radius:2px!important}.is-product .card-title{font-family:Georgia,serif;font-size:1.06rem!important;line-height:1.4}.badge.bg-info{background:#8a6b45!important}.tn-footer-links a,.tn-footer-address,.tn-footer-col p{color:#74645c}.tn-footer-motto{color:#8a6b45}.v-demo{font-size:.68rem;margin-top:16px!important;line-height:1.8}.v-wine-kicker{text-transform:uppercase;font-size:.75rem;letter-spacing:1.6px;color:#8a6b45}.v-tasting{font-size:1.15rem;line-height:1.7}.v-wine-details h2{font-size:1.7rem;margin:26px 0 20px}.v-wine-details h3{font-size:1.25rem}.v-specs{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));border-top:1px solid #e4d9cc}.v-specs>div{padding:13px 10px 13px 0;border-bottom:1px solid #e4d9cc}.v-specs dt{font-weight:400;text-transform:uppercase;font-size:.65rem;letter-spacing:1px;color:#8a6b45}.v-specs dd{margin:5px 0 0;font-size:.92rem}.v-pairing{background:#f4eee3;padding:20px;margin:22px 0}.v-pairing p{margin:0}
@media(max-width:991px){.tn-hero-copy{padding:36px 28px}.tn-hero,.tn-hero-photo{min-height:450px}.navbar-brand img{width:195px}.is-product>a>img{height:230px}}
@media(max-width:575px){.tn-hero{border-radius:3px}.tn-hero-copy{padding:32px 26px}.tn-hero h1{font-size:3.4rem}.tn-hero-photo{min-height:330px}.tn-hero-photo img{object-position:center 48%}.tn-hero-note{font-size:.8rem}.is-product>a>img{height:220px}.navbar-brand img{width:175px}.v-specs{grid-template-columns:1fr}}
'''
css_path.write_text(css,encoding='utf-8')
