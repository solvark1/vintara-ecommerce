<?php
if(PHP_SAPI!=='cli')exit;
mysqli_report(MYSQLI_REPORT_ERROR|MYSQLI_REPORT_STRICT);
$db=new mysqli(getenv('DB_HOST'),getenv('DB_USER'),getenv('DB_PASSWORD'),getenv('DB_NAME'));
$db->set_charset('utf8mb4');
$checks=[
 '18 demo products'=>"SELECT COUNT(*)=18 FROM demo_seed_entities e JOIN products p ON p.products_id=e.entity_id WHERE e.entity_type='product' AND e.seed_version='vintara-v1'",
 '40 demo customers'=>"SELECT COUNT(*)=40 FROM demo_seed_entities e JOIN customers c ON c.customers_id=e.entity_id WHERE e.entity_type='customer' AND e.seed_version='vintara-v1'",
 '240 demo orders'=>"SELECT COUNT(*)=240 FROM demo_seed_entities e JOIN orders o ON o.orders_id=e.entity_id WHERE e.entity_type='order' AND e.seed_version='vintara-v1'",
 '40 valid primary addresses'=>"SELECT COUNT(*)=40 FROM demo_seed_entities e JOIN customers c ON c.customers_id=e.entity_id JOIN address_book a ON a.address_book_id=c.customers_default_address_id AND a.customers_id=c.customers_id JOIN customers_info ci ON ci.customers_info_id=c.customers_id WHERE e.entity_type='customer' AND e.seed_version='vintara-v1'",
 'All order lines and customer references valid'=>"SELECT COUNT(*)=0 FROM orders o LEFT JOIN customers c ON c.customers_id=o.customers_id WHERE c.customers_id IS NULL OR NOT EXISTS(SELECT 1 FROM orders_products op WHERE op.orders_id=o.orders_id)",
 'All order product references valid'=>"SELECT COUNT(*)=0 FROM orders_products op LEFT JOIN products p ON p.products_id=op.products_id LEFT JOIN orders o ON o.orders_id=op.orders_id WHERE p.products_id IS NULL OR o.orders_id IS NULL",
 'Subtotals equal line item sums'=>"SELECT COUNT(*)=0 FROM (SELECT o.orders_id FROM orders o JOIN orders_products op ON op.orders_id=o.orders_id JOIN orders_total t ON t.orders_id=o.orders_id AND t.class='ot_subtotal' GROUP BY o.orders_id,t.value HAVING ABS(SUM(op.final_price*op.products_quantity)-t.value)>0.001) bad",
 'Totals equal subtotal plus delivery'=>"SELECT COUNT(*)=0 FROM orders o JOIN orders_total t ON t.orders_id=o.orders_id AND t.class='ot_total' JOIN orders_total s ON s.orders_id=o.orders_id AND s.class='ot_subtotal' JOIN orders_total d ON d.orders_id=o.orders_id AND d.class='ot_shipping' WHERE ABS(t.value-s.value-d.value)>0.001",
 'Every order has exactly three totals'=>"SELECT COUNT(*)=0 FROM (SELECT o.orders_id,COUNT(t.orders_total_id) n FROM orders o LEFT JOIN orders_total t ON t.orders_id=o.orders_id GROUP BY o.orders_id HAVING n<>3) bad",
 'Every seeded order has a history'=>"SELECT COUNT(*)=0 FROM demo_seed_entities e JOIN orders o ON o.orders_id=e.entity_id WHERE e.entity_type='order' AND NOT EXISTS(SELECT 1 FROM orders_status_history h WHERE h.orders_id=o.orders_id )",
 'No visible DEMO tags'=>"SELECT (SELECT COUNT(*) FROM customers WHERE customers_lastname LIKE '%[DEMO]%')+(SELECT COUNT(*) FROM orders WHERE customers_name LIKE '%[DEMO]%' OR payment_method LIKE '%DEMO%')+(SELECT COUNT(*) FROM orders_status WHERE orders_status_name LIKE '%DEMO%')+(SELECT COUNT(*) FROM products WHERE products_model LIKE '%DEMO%')=0",
 'CRC default and base currency'=>"SELECT COUNT(*)=1 FROM currencies c JOIN configuration f ON f.configuration_key='DEFAULT_CURRENCY' AND f.configuration_value=c.code WHERE c.code='CRC' AND c.value=1",
 'CRC orders'=>"SELECT COUNT(*)=0 FROM orders WHERE currency<>'CRC' OR currency_value<>1",
 'Four statuses and seven provinces'=>"SELECT COUNT(DISTINCT orders_status)=4 AND COUNT(DISTINCT customers_state)=7 FROM orders",
 'No email notifications sent'=>"SELECT COUNT(*)=0 FROM orders_status_history WHERE customer_notified<>0",
 'Outbound email disabled'=>"SELECT configuration_value='false' FROM configuration WHERE configuration_key='SEND_EMAILS'",
 'Brand and template configured'=>"SELECT COUNT(*)=2 FROM configuration WHERE (configuration_key='STORE_NAME' AND configuration_value='Vintara') OR (configuration_key='TEMPLATE_SELECTION' AND configuration_value='override')",
];
$failed=0;
foreach($checks as $label=>$sql){$ok=(bool)$db->query($sql)->fetch_row()[0];echo ($ok?'PASS ':'FAIL ').$label."\n";if(!$ok)$failed++;}
foreach(['products','customers','address_book','customers_info','orders','orders_products','orders_total','orders_status_history','demo_seed_entities','demo_seed_runs'] as $table){$result=$db->query("SELECT * FROM `$table` ORDER BY 1")->fetch_all(MYSQLI_ASSOC);$snap[$table]=['count'=>count($result),'sha256'=>hash('sha256',json_encode($result,JSON_UNESCAPED_UNICODE))];}
echo 'SNAPSHOT '.json_encode($snap)."\n";
exit($failed?1:0);

