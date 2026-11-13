<?php
// Additive catalogue migration: historical order lines and CRM are preserved.
if (PHP_SAPI !== 'cli') { http_response_code(403); exit; }
mysqli_report(MYSQLI_REPORT_ERROR | MYSQLI_REPORT_STRICT);
$db = new mysqli(getenv('DB_HOST'),getenv('DB_USER'),getenv('DB_PASSWORD'),getenv('DB_NAME'));
$db->set_charset('utf8mb4');
function vq(string $sql,array $args=[]): mysqli_stmt {
 global $db; $s=$db->prepare($sql);
 if($args) $s->bind_param(str_repeat('s',count($args)),...$args);
 $s->execute(); return $s;
}
function vi(string $table,array $data): int {
 global $db;
 vq('INSERT INTO `'.$table.'` (`'.implode('`,`',array_keys($data)).'`) VALUES ('.implode(',',array_fill(0,count($data),'?')).')',array_values($data));
 return (int)$db->insert_id;
}
function vc(string $key,string $value): void {
 vq("INSERT INTO configuration(configuration_title,configuration_key,configuration_value,configuration_description,configuration_group_id,sort_order,date_added) VALUES (?,?,?,'Vintara wine store',6,0,NOW()) ON DUPLICATE KEY UPDATE configuration_value=VALUES(configuration_value),last_modified=NOW()",[$key,$key,$value]);
}
function vh($value): string { return htmlspecialchars((string)$value,ENT_QUOTES,'UTF-8'); }
$assets='/var/www/html/images/vintara';
if(!is_dir($assets)&&!mkdir($assets,0755,true)) throw new RuntimeException('Cannot create asset directory');
foreach(glob('/opt/phoenix/brand-assets/vintara/*') as $source) {
 $target=$assets.'/'.basename($source);
 if(!copy($source,$target)) throw new RuntimeException('Cannot copy asset');
 chown($target,'www-data'); chgrp($target,'www-data');
}
if(!$db->query("SELECT GET_LOCK('vintara_catalog_migration',20) AS ok")->fetch_assoc()['ok']) throw new RuntimeException('Migration running');
try {
 if(vq("SELECT 1 FROM configuration WHERE configuration_key='VINTARA_CATALOG_V1'")->get_result()->num_rows) {
  echo "Vintara catalog already applied; edits and inventory preserved.\n"; exit;
 }
 $catalog=json_decode(file_get_contents('/opt/phoenix/vintara-catalog.json'),true,512,JSON_THROW_ON_ERROR);
 if(count($catalog)!==18||count(array_unique(array_column($catalog,'sku')))!==18) throw new RuntimeException('Invalid catalog');
 // DDL is outside the transaction: MySQL DDL implicitly commits.
 $db->query("CREATE TABLE IF NOT EXISTS vintara_wines (products_id int NOT NULL PRIMARY KEY, category varchar(32) NOT NULL, grape varchar(120) NOT NULL, vintage varchar(24) NOT NULL, region varchar(100) NOT NULL, country varchar(80) NOT NULL, winery varchar(120) NOT NULL, volume_ml int NOT NULL, abv decimal(4,1) NOT NULL, tasting_notes text NOT NULL, pairing text NOT NULL, serving_temperature varchar(32) NOT NULL, storage text NOT NULL, is_synthetic tinyint NOT NULL DEFAULT 1) ENGINE=InnoDB CHARACTER SET utf8mb4");
 $db->begin_transaction();
 $langs=array_column($db->query('SELECT languages_id FROM languages')->fetch_all(MYSQLI_ASSOC),'languages_id');
 $categories=[];
 foreach(['Tintos','Blancos','Rosados','Espumantes'] as $i=>$name) {
  $example=array_values(array_filter($catalog,fn($w)=>$w['category']===$name))[0];
  $id=vi('categories',['categories_image'=>$example['image'],'parent_id'=>0,'sort_order'=>10*$i,'date_added'=>date('Y-m-d H:i:s')]);
  foreach($langs as $lang) vi('categories_description',['categories_id'=>$id,'language_id'=>$lang,'categories_name'=>$name,'categories_description'=>'Descubrí nuestra selección: '.$name.'. Explorá sus uvas, regiones y maridajes.','categories_seo_title'=>$name.' | Vintara']);
  $categories[$name]=$id;
 }
 $wineries=[];
 foreach($catalog as $w) {
  if(vq('SELECT 1 FROM products WHERE products_model=?',[$w['sku']])->get_result()->num_rows) throw new RuntimeException('SKU conflict: '.$w['sku']);
  if(!isset($wineries[$w['winery']])) {
   $mid=vi('manufacturers',['manufacturers_name'=>$w['winery'],'date_added'=>date('Y-m-d H:i:s')]);
   foreach($langs as $lang) vi('manufacturers_info',['manufacturers_id'=>$mid,'languages_id'=>$lang,'manufacturers_url'=>'','manufacturers_description'=>'Bodega ficticia del catálogo académico de Vintara.']);
   $wineries[$w['winery']]=$mid;
  }
  $id=vi('products',['products_quantity'=>$w['quantity'],'products_model'=>$w['sku'],'products_image'=>$w['image'],'products_price'=>$w['price'],'products_date_added'=>date('Y-m-d H:i:s'),'products_weight'=>1.3,'products_status'=>1,'products_tax_class_id'=>0,'products_ordered'=>0,'manufacturers_id'=>$wineries[$w['winery']]]);
  $specs=['Tipo'=>$w['category'],'Uva'=>$w['grape'],'Añada'=>$w['vintage'],'Región'=>$w['region'],'País'=>$w['country'],'Bodega'=>$w['winery'],'Contenido'=>$w['volume_ml'].' ml','Alcohol'=>$w['abv'].' %','Temperatura de servicio'=>$w['serving']];
  $desc='<section class="v-wine-details"><p class="v-wine-kicker">'.vh($w['country']).' · '.vh($w['region']).'</p><p class="v-tasting">'.vh($w['notes']).'</p><h2>La historia en cada botella</h2><dl class="v-specs">';
  foreach($specs as $key=>$val) $desc.='<div><dt>'.vh($key).'</dt><dd>'.vh($val).'</dd></div>';
  $desc.='</dl><div class="v-pairing"><h3>En buena compañía</h3><p>'.vh($w['pairing']).'.</p></div><h3>Conservación</h3><p>'.vh($w['storage']).'</p><p class="small text-muted">Vino y bodega ficticios. Imagen ilustrativa del catálogo académico.</p></section>';
  foreach($langs as $lang) vi('products_description',['products_id'=>$id,'language_id'=>$lang,'products_name'=>$w['name'].' · '.$w['grape'],'products_description'=>$desc,'products_seo_title'=>$w['name'].' | Vintara','products_seo_description'=>$w['notes'].' '.$w['region'].', '.$w['country'].'. Botella de 750 ml.']);
  vi('products_to_categories',['products_id'=>$id,'categories_id'=>$categories[$w['category']]]);
  vi('vintara_wines',['products_id'=>$id,'category'=>$w['category'],'grape'=>$w['grape'],'vintage'=>$w['vintage'],'region'=>$w['region'],'country'=>$w['country'],'winery'=>$w['winery'],'volume_ml'=>750,'abv'=>$w['abv'],'tasting_notes'=>$w['notes'],'pairing'=>$w['pairing'],'serving_temperature'=>$w['serving'],'storage'=>$w['storage']]);
 }
 // Archive only the previous seeded products. No historical names or totals change.
 $db->query("UPDATE products p JOIN demo_seed_entities e ON e.entity_id=p.products_id AND e.entity_type='product' AND e.seed_version='terra-nostra-v1' SET p.products_status=0");
 foreach(['STORE_NAME'=>'Vintara S.A.','STORE_OWNER'=>'Vintara S.A.','STORE_OWNER_EMAIL_ADDRESS'=>'hola@vintara.example.test','EMAIL_FROM'=>'Vintara <hola@vintara.example.test>','STORE_LOGO'=>'vintara/logo.svg','MINI_LOGO'=>'vintara/logo.svg','STORE_ADDRESS'=>"Paraíso, Cartago\nCosta Rica",'STORE_PHONE'=>'','SEND_EMAILS'=>'false','MODULE_CONTENT_CARD_PRODUCTS_MAX_DISPLAY'=>'8','VINTARA_CATALOG_V1'=>'1'] as $key=>$value) vc($key,$value);
 $db->commit();
 foreach(glob('/var/www/html/includes/work/*.cache') as $cache) unlink($cache);
 echo "Vintara: 18 wines and 4 categories created; historical orders and CRM preserved.\n";
} catch(Throwable $e) { $db->rollback(); throw $e; }
finally { $db->query("SELECT RELEASE_LOCK('vintara_catalog_migration')"); }
