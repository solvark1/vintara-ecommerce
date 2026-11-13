<?php
if (PHP_SAPI !== 'cli') { http_response_code(403); exit; }
mysqli_report(MYSQLI_REPORT_ERROR | MYSQLI_REPORT_STRICT);
$db=new mysqli(getenv('DB_HOST'),getenv('DB_USER'),getenv('DB_PASSWORD'),getenv('DB_NAME'));
$db->set_charset('utf8mb4');
if ($db->query("SELECT 1 FROM configuration WHERE configuration_key='VINTARA_CATALOG_V1'")->num_rows) { echo "Vintara identity preserved.\n"; exit; }
// Asset files are in a Docker volume, so copy them explicitly on every start.
$dir='/var/www/html/images/vintara';
if(!is_dir($dir)) mkdir($dir,0755,true);
copy('/opt/phoenix/brand-assets/logo.svg',$dir.'/logo.svg');
chown($dir.'/logo.svg','www-data'); chgrp($dir.'/logo.svg','www-data');
$version='vintara-brand-v1';
$s=$db->prepare("SELECT configuration_value FROM configuration WHERE configuration_key='LOCAL_BRAND_VERSION'");$s->execute();
if(($s->get_result()->fetch_assoc()['configuration_value']??'')===$version){echo "Vintara branding is current.\n";exit;}
$db->begin_transaction();
try {
 $cr=$db->query("SELECT countries_id FROM countries WHERE countries_iso_code_2='CR'")->fetch_assoc()['countries_id'];
 $values=['STORE_NAME'=>'Vintara','STORE_OWNER'=>'Equipo IF6201','STORE_OWNER_EMAIL_ADDRESS'=>'hola@vintara.example.test','EMAIL_FROM'=>'Vintara <hola@vintara.example.test>','STORE_COUNTRY'=>$cr,'STORE_ZONE'=>'0','STORE_ADDRESS'=>"Paraíso, Cartago\nCosta Rica\nTienda académica de demostración",'STORE_PHONE'=>'Solo demostración','MINI_LOGO'=>'vintara/logo.svg','STORE_LOGO'=>'vintara/logo.svg','TEMPLATE_SELECTION'=>'override','SEND_EMAILS'=>'false','MODULE_CONTENT_CARD_PRODUCTS_MAX_DISPLAY'=>'8','MODULE_CONTENT_HEADER_MENU_MANUFACTURERS'=>'False','LOCAL_BRAND_VERSION'=>$version];
 $s=$db->prepare("INSERT INTO configuration (configuration_title,configuration_key,configuration_value,configuration_description,configuration_group_id,sort_order,date_added) VALUES (?,?,?,'Vintara local customization',6,0,NOW()) ON DUPLICATE KEY UPDATE configuration_value=VALUES(configuration_value),last_modified=NOW()");
 foreach($values as $key=>$value){$s->bind_param('sss',$key,$key,$value);$s->execute();}
 // Translate the three original built-in states without changing their identifiers.
 foreach([1=>'Pendiente',2=>'En preparación',3=>'Entregado'] as $id=>$name){$s=$db->prepare('UPDATE orders_status SET orders_status_name=? WHERE orders_status_id=?');$s->bind_param('si',$name,$id);$s->execute();}
 $db->commit();
 foreach(glob('/var/www/html/includes/work/*.cache') as $cache) unlink($cache);
 echo "Vintara identity applied.\n";
}catch(Throwable $e){$db->rollback();throw $e;}
