<?php
if(PHP_SAPI!=='cli')exit;
mysqli_report(MYSQLI_REPORT_ERROR|MYSQLI_REPORT_STRICT);
$db=new mysqli(getenv('DB_HOST'),getenv('DB_USER'),getenv('DB_PASSWORD'),getenv('DB_NAME'));
$db->set_charset('utf8mb4');
if($db->query("SELECT 1 FROM configuration WHERE configuration_key='LOCAL_CRC_REFINEMENT_V1'")->num_rows){echo "CRC refinement already applied.\n";exit;}
$db->begin_transaction();
try {
 // Fixed synthetic pricing factor for this academic dataset; not a live FX rate.
 foreach(['products'=>['products_price'],'products_attributes'=>['options_values_price'],'specials'=>['specials_new_products_price'],'customers_basket'=>['final_price'],'orders_products'=>['products_price','final_price'],'orders_products_attributes'=>['options_values_price'],'orders_total'=>['value']] as $table=>$fields){
  foreach($fields as $field)$db->query("UPDATE `$table` SET `$field`=ROUND(`$field`*500,4)");
 }
 $db->query("UPDATE currencies SET value=value/500 WHERE code<>'CRC'");
 $db->query("INSERT INTO currencies (title,code,symbol_left,symbol_right,decimal_point,thousands_point,decimal_places,value,last_updated) SELECT 'Colón costarricense','CRC','₡','','.',',','0',1,NOW() WHERE NOT EXISTS(SELECT 1 FROM currencies WHERE code='CRC')");
 $db->query("UPDATE currencies SET title='Colón costarricense',symbol_left='₡',symbol_right='',decimal_point='.',thousands_point=',',decimal_places='0',value=1 WHERE code='CRC'");
 $db->query("UPDATE orders SET currency='CRC',currency_value=1");
 $db->query("UPDATE orders_total SET text=CONCAT('₡',FORMAT(value,0,'en_US')),title=REPLACE(title,'Envío simulado:','Envío:')");
 foreach(['MODULE_SHIPPING_FLAT_COST','MODULE_SHIPPING_FLAT_HANDLING','MODULE_SHIPPING_FREE_SHIPPING_OVER','MODULE_ORDER_TOTAL_SHIPPING_FREE_SHIPPING_OVER'] as $key){
  $s=$db->prepare('UPDATE configuration SET configuration_value=CAST(configuration_value AS DECIMAL(15,4))*500 WHERE configuration_key=?');$s->bind_param('s',$key);$s->execute();
 }
 $db->query("UPDATE configuration SET configuration_value='CRC' WHERE configuration_key='DEFAULT_CURRENCY'");
 $db->query("UPDATE configuration SET configuration_value='false' WHERE configuration_key='USE_DEFAULT_LANGUAGE_CURRENCY'");
 foreach(['customers'=>['customers_lastname'],'address_book'=>['entry_lastname'],'orders'=>['customers_name','delivery_name','billing_name']] as $table=>$fields) foreach($fields as $field)$db->query("UPDATE `$table` SET `$field`=REPLACE(`$field`,' [DEMO]','')");
 foreach(['products','orders_products'] as $table)$db->query("UPDATE `$table` SET products_model=REPLACE(products_model,'TN-DEMO-','TN-')");
 $db->query("UPDATE customers SET customers_telephone='' WHERE customers_telephone='DEMO-SIN-TELEFONO'");
 $db->query("UPDATE orders SET customers_telephone='' WHERE customers_telephone='DEMO-SIN-TELEFONO'");
 $db->query("UPDATE address_book SET entry_street_address='Zona central' WHERE entry_street_address='Dirección ficticia para demostración'");
 foreach(['customers','delivery','billing'] as $prefix)$db->query("UPDATE orders SET {$prefix}_street_address='Zona central' WHERE {$prefix}_street_address='Dirección ficticia para demostración'");
 $db->query("UPDATE orders SET payment_method=CASE payment_method WHEN 'Contra entrega · DEMO' THEN 'Contra entrega' WHEN 'Transferencia simulada · DEMO' THEN 'Transferencia bancaria' WHEN 'Pago ficticio · DEMO' THEN 'SINPE Móvil' ELSE payment_method END");
 $db->query("UPDATE orders_status SET orders_status_name='Cancelado' WHERE orders_status_name='Cancelado · DEMO'");
 $db->query("UPDATE orders_status_history SET comments=CONCAT('Pedido TN-',LPAD(orders_id,3,'0'),' recibido.') WHERE comments LIKE '[DEMO%'");
 $db->query("UPDATE orders_status_history SET comments='Estado del pedido actualizado.' WHERE comments='Estado simulado para análisis académico.'");
 $remove='<p class="text-muted small">Producto ficticio para una demostración académica. No se realizan ventas reales.</p>';
 $s=$db->prepare("UPDATE products_description pd JOIN demo_seed_entities e ON e.entity_id=pd.products_id AND e.entity_type='product' SET products_description=REPLACE(products_description,?,''),products_seo_title=products_name");$s->bind_param('s',$remove);$s->execute();
 $db->query("UPDATE categories_description SET categories_description='El sabor de compartir alimentos frescos.' WHERE categories_id IN (SELECT entity_id FROM demo_seed_entities WHERE entity_type='category')");
 $db->query("UPDATE configuration SET configuration_value='Paraíso, Cartago\nCosta Rica' WHERE configuration_key='STORE_ADDRESS'");
 $db->query("UPDATE configuration SET configuration_value='' WHERE configuration_key='STORE_PHONE'");
 $db->query("INSERT INTO configuration (configuration_title,configuration_key,configuration_value,configuration_description,configuration_group_id,sort_order,date_added) VALUES ('Local CRC refinement','LOCAL_CRC_REFINEMENT_V1','1','Fixed synthetic pricing factor 500 CRC per previous USD; no live exchange rate',6,0,NOW())");
 $db->commit();
 foreach(glob('/var/www/html/includes/work/*.cache')as $f)unlink($f);
 echo "CRC prices and visible data refinements applied.\n";
}catch(Throwable $e){$db->rollback();throw $e;}
