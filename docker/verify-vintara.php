<?php
if(PHP_SAPI!=='cli')exit(1);
mysqli_report(MYSQLI_REPORT_ERROR|MYSQLI_REPORT_STRICT);
$db=new mysqli(getenv('DB_HOST'),getenv('DB_USER'),getenv('DB_PASSWORD'),getenv('DB_NAME'));
$db->set_charset('utf8mb4');
function checkv(bool $ok,string $message):void { if(!$ok)throw new RuntimeException($message); echo "OK: $message\n"; }
checkv($db->query("SELECT configuration_value FROM configuration WHERE configuration_key='STORE_NAME'")->fetch_assoc()['configuration_value']==='Vintara S.A.','Store identity');
checkv((int)$db->query('SELECT COUNT(*) n FROM vintara_wines')->fetch_assoc()['n']===18,'18 wine profiles');
checkv((int)$db->query('SELECT COUNT(DISTINCT category) n FROM vintara_wines')->fetch_assoc()['n']===4,'4 wine categories');
checkv((int)$db->query('SELECT COUNT(*) n FROM vintara_wines v JOIN products p USING(products_id) WHERE p.products_status=1 AND p.products_price>0 AND p.products_quantity>0')->fetch_assoc()['n']===18,'18 purchasable wines with prices and stock');
checkv((int)$db->query("SELECT COUNT(*) n FROM products p JOIN demo_seed_entities e ON e.entity_id=p.products_id AND e.entity_type='product' AND e.seed_version='terra-nostra-v1' WHERE p.products_status=1")->fetch_assoc()['n']===0,'Previous demo catalog archived');
checkv((int)$db->query('SELECT COUNT(*) n FROM vintara_wines v LEFT JOIN products_to_categories pc USING(products_id) WHERE pc.categories_id IS NULL')->fetch_assoc()['n']===0,'Wine category relationships');
foreach($db->query('SELECT p.products_image FROM products p JOIN vintara_wines v USING(products_id)')->fetch_all(MYSQLI_ASSOC) as $row) checkv(is_file('/var/www/html/images/'.$row['products_image']),'Image '.$row['products_image']);
checkv((int)$db->query('SELECT COUNT(*) n FROM vintara_wines v LEFT JOIN products_description d USING(products_id) WHERE d.products_description IS NULL OR d.products_description NOT LIKE \'%Conservación%\'')->fetch_assoc()['n']===0,'Complete wine descriptions');
echo "VINTARA VERIFIED\n";
