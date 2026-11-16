<?php
// Public brand only. Technical infrastructure IDs and transaction history remain stable.
if(PHP_SAPI!=='cli')exit;
mysqli_report(MYSQLI_REPORT_ERROR|MYSQLI_REPORT_STRICT);
$db=new mysqli(getenv('DB_HOST'),getenv('DB_USER'),getenv('DB_PASSWORD'),getenv('DB_NAME'));
$db->set_charset('utf8mb4');
$db->begin_transaction();
try {
 $values=['STORE_NAME'=>'Terra Nostra','STORE_OWNER'=>'Terra Nostra','STORE_OWNER_EMAIL_ADDRESS'=>'hola@terranostra.example.test','EMAIL_FROM'=>'Terra Nostra <hola@terranostra.example.test>','STORE_LOGO'=>'vintara/terra-nostra-logo.jpeg','MINI_LOGO'=>'vintara/terra-nostra-logo.jpeg'];
 $stmt=$db->prepare('UPDATE configuration SET configuration_value=? WHERE configuration_key=?');
 foreach($values as $key=>$value){$stmt->bind_param('ss',$value,$key);$stmt->execute();}
 foreach(['products_description'=>['products_description','products_seo_title','products_seo_description'],'categories_description'=>['categories_description','categories_seo_title','categories_seo_description'],'manufacturers_info'=>['manufacturers_description']] as $table=>$columns){
  foreach($columns as $column)$db->query("UPDATE `$table` SET `$column`=REPLACE(REPLACE(`$column`,'Vintara S.A.','Terra Nostra'),'Vintara','Terra Nostra') WHERE `$column` LIKE '%Vintara%'");
 }
 $db->query("UPDATE products SET products_image=REPLACE(products_image,'vintara/vin-','vintara/terra-vin-') WHERE products_image LIKE 'vintara/vin-%'");
 $db->commit();
 foreach(glob('/var/www/html/includes/work/*.cache') as $file)unlink($file);
 echo "Public identity: Terra Nostra. Technology provider: CONTI.\n";
}catch(Throwable $e){$db->rollback();throw $e;}
