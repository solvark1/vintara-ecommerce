<?php
// Local academic demo only. No mail, payment requests or external services are invoked.
if (PHP_SAPI !== 'cli') { http_response_code(403); exit; }
mysqli_report(MYSQLI_REPORT_ERROR | MYSQLI_REPORT_STRICT);
date_default_timezone_set('America/Costa_Rica');
$db = new mysqli(getenv('DB_HOST'), getenv('DB_USER'), getenv('DB_PASSWORD'), getenv('DB_NAME'));
$db->set_charset('utf8mb4');
function run(string $sql, array $args = []): mysqli_stmt {
    global $db;
    $s = $db->prepare($sql);
    if ($args) { $s->bind_param(str_repeat('s', count($args)), ...$args); }
    $s->execute(); return $s;
}
function rows(string $sql, array $args = []): array { return run($sql,$args)->get_result()->fetch_all(MYSQLI_ASSOC); }
function insertRow(string $table, array $data): int {
    global $db;
    run('INSERT INTO `'.$table.'` (`'.implode('`,`',array_keys($data)).'`) VALUES ('.implode(',',array_fill(0,count($data),'?')).')',array_values($data));
    return (int)$db->insert_id;
}
function entity(string $type, string $key, string $table, string $pk, callable $create): int {
    global $db;
    $found=rows('SELECT entity_id FROM demo_seed_entities WHERE seed_version=? AND entity_type=? AND entity_key=?',['vintara-v1',$type,$key]);
    if ($found) {
        $id=(int)$found[0]['entity_id'];
        if (!rows("SELECT `$pk` FROM `$table` WHERE `$pk`=?",[$id])) { throw new RuntimeException("Seed entity $type/$key was removed; no automatic recreation to preserve manual changes."); }
        return $id;
    }
    $id=$create();
    insertRow('demo_seed_entities',['seed_version'=>'vintara-v1','entity_type'=>$type,'entity_key'=>$key,'entity_id'=>$id]);
    return $id;
}
function config(string $key,string $value): void {
    run("INSERT INTO configuration (configuration_title,configuration_key,configuration_value,configuration_description,configuration_group_id,sort_order,date_added) VALUES (?,?,?,'Local academic demo',6,0,NOW()) ON DUPLICATE KEY UPDATE configuration_value=VALUES(configuration_value),last_modified=NOW()",[$key,$key,$value]);
}
function money(int $cents): string { return '$'.number_format($cents/100,2,'.',','); }
$db->query('CREATE TABLE IF NOT EXISTS demo_seed_runs (seed_version varchar(64) PRIMARY KEY, anchor_date date NOT NULL, completed_at datetime NOT NULL) ENGINE=InnoDB');
$db->query('CREATE TABLE IF NOT EXISTS demo_seed_entities (seed_version varchar(64) NOT NULL,entity_type varchar(32) NOT NULL,entity_key varchar(64) NOT NULL,entity_id int NOT NULL,PRIMARY KEY(seed_version,entity_type,entity_key)) ENGINE=InnoDB');
if (!$db->query("SELECT GET_LOCK('vintara_seed',10) AS acquired")->fetch_assoc()['acquired']) { throw new RuntimeException('Another seed is running.'); }
try {
    $db->begin_transaction();
    $completed=rows('SELECT * FROM demo_seed_runs WHERE seed_version=?',['vintara-v1']);
    if ($completed) {
        echo "Vintara demo already loaded. Existing data and edits preserved.\n";
        $db->commit(); exit;
    }
    if (!getenv('DEMO_CUSTOMER_PASSWORD')) { throw new RuntimeException('DEMO_CUSTOMER_PASSWORD is required.'); }
    $anchor=new DateTimeImmutable('today');
    mt_srand(62012026);
    $country=rows("SELECT countries_id,address_format_id FROM countries WHERE countries_iso_code_2='CR'")[0];
    $countryId=(int)$country['countries_id']; $format=(int)$country['address_format_id'];
    $languageIds=array_column(rows('SELECT languages_id FROM languages'),'languages_id');
    $categories=[];
    foreach ([['frutas','Frutas frescas','fruit.webp'],['huerta','De la huerta','vegetables-1.webp'],['selecciones','Selecciones para compartir','apples-pears.webp']] as $i=>$cat) {
        [$key,$name,$image]=$cat;
        $categories[$key]=entity('category',$key,'categories','categories_id',function()use($name,$image,$i,$languageIds){
            $id=insertRow('categories',['categories_image'=>'sample/'.$image,'parent_id'=>0,'sort_order'=>($i+1)*10,'date_added'=>date('Y-m-d H:i:s')]);
            foreach($languageIds as $lang) insertRow('categories_description',['categories_id'=>$id,'language_id'=>$lang,'categories_name'=>$name,'categories_description'=>'El sabor de compartir alimentos frescos. Catálogo de demostración Vintara.']);
            return $id;
        });
    }
    $catalog=[
        ['Naranja de mesa · 1 kg','orange-1.webp',350,'frutas','Naranjas para disfrutar en gajos o preparar un jugo en casa.'],
        ['Limón amarillo · 500 g','lemon-1.webp',225,'frutas','Un toque fresco para bebidas, aderezos y recetas.'],
        ['Pera de temporada · 1 kg','pear-1.webp',425,'frutas','Peras de textura suave para meriendas y ensaladas.'],
        ['Manzana roja · 1 kg','apple-1.webp',475,'frutas','Manzanas crujientes para acompañar tu día.'],
        ['Tomate maduro · 1 kg','tomatoes-1.webp',295,'huerta','Tomates para ensaladas, salsas y cocina diaria.'],
        ['Tomate verde · 500 g','green-tomatoes-1.webp',175,'huerta','Tomates de sabor ligeramente ácido para cocinar.'],
        ['Manzana verde · 1 kg','green-apple-1.webp',495,'frutas','La combinación de frescura y acidez para tus recetas.'],
        ['Toronja rosada · 1 kg','grapefruit-1.webp',395,'frutas','Cítricos para desayunos, jugos y ensaladas.'],
        ['Limón verde · 500 g','lime-1.webp',185,'frutas','Un básico para tu cocina, de la ensalada a la limonada.'],
        ['Naranja para jugo · 2 kg','orange-1.webp',595,'selecciones','Una selección para compartir jugo recién preparado.'],
        ['Limón amarillo familiar · 1 kg','lemons-2.webp',395,'selecciones','La presentación familiar del cítrico más versátil.'],
        ['Peras para compartir · 2 kg','pear-1.webp',745,'selecciones','Una selección de peras para toda la familia.'],
        ['Manzana roja familiar · 2 kg','apple-1.webp',825,'selecciones','El tamaño ideal para las meriendas de la semana.'],
        ['Tomate para salsa · 2 kg','tomatoes-1.webp',495,'huerta','Prepara tu salsa favorita con tomates maduros.'],
        ['Tomate verde familiar · 1 kg','green-tomatoes-1.webp',295,'huerta','Una selección para experimentar en la cocina.'],
        ['Manzana verde familiar · 2 kg','green-apple-1.webp',875,'selecciones','Frescura para postres, ensaladas y meriendas.'],
        ['Toronja para jugo · 2 kg','grapefruit-1.webp',695,'selecciones','Una presentación para compartir el desayuno.'],
        ['Limón verde familiar · 1 kg','lime-1.webp',325,'huerta','El toque final para tus comidas de la semana.'],
    ];
    $products=[];
    foreach($catalog as $i=>$item) {
        [$name,$image,$cents,$category,$description]=$item;
        $model=sprintf('TN-DEMO-%03d',$i+1);
        $id=entity('product',$model,'products','products_id',function()use($i,$name,$image,$cents,$category,$description,$model,$categories,$languageIds,$anchor){
            $id=insertRow('products',['products_quantity'=>mt_rand(35,180),'products_model'=>$model,'products_image'=>'sample/'.$image,'products_price'=>$cents/100,'products_date_added'=>$anchor->modify('-'.(18-$i).' days')->format('Y-m-d 08:00:00'),'products_weight'=>str_contains($name,'2 kg')?2:(str_contains($name,'500 g')?0.5:1),'products_status'=>1,'products_tax_class_id'=>0,'products_ordered'=>0]);
            foreach($languageIds as $lang) insertRow('products_description',['products_id'=>$id,'language_id'=>$lang,'products_name'=>$name,'products_description'=>'<p>'.$description.'</p><ul><li>Presentación: '.htmlspecialchars($name).'</li><li>Imágenes ilustrativas del catálogo original de Phoenix Cart.</li></ul><p class="text-muted small">Producto ficticio para una demostración académica. No se realizan ventas reales.</p>','products_seo_description'=>$description,'products_seo_title'=>$name.' | Vintara']);
            insertRow('products_to_categories',['products_id'=>$id,'categories_id'=>$categories[$category]]);
            return $id;
        });
        $products[]=['id'=>$id,'model'=>$model,'name'=>$name,'cents'=>$cents];
    }
    // Keep Phoenix sample records; only disable their exact known original SKUs.
    run("UPDATE products SET products_status=0 WHERE products_id BETWEEN 1 AND 9 AND products_model IN ('ORA-1','LEM-1','PEA-1','APP-1','TOM-1','GTOM-1','GAPP-1','GPF-1','LIM-1')");
    $provinces=[['San José','San José','10101'],['Alajuela','Alajuela','20101'],['Cartago','Paraíso','30201'],['Heredia','Heredia','40101'],['Guanacaste','Liberia','50101'],['Puntarenas','Puntarenas','60101'],['Limón','Limón','70101']];
    $firstnames=['Sofía','Mateo','Valeria','Santiago','Camila','Daniel','Lucía','Gabriel','Isabella','Andrés','Mariana','David','Elena','Nicolás','Paula','Sebastián','Natalia','Diego','Adriana','Luis'];
    $lastnames=['Mora','Vargas','Rojas','Castro','Solano','Arias','Jiménez','Chaves'];
    $customers=[]; $hash=password_hash(getenv('DEMO_CUSTOMER_PASSWORD'),PASSWORD_DEFAULT);
    for($i=0;$i<40;$i++) {
        $province=$provinces[$i%7]; $first=$firstnames[$i%20]; $last=$lastnames[$i%8].' [DEMO]';
        $email=sprintf('cliente%02d@example.test',$i+1); $created=$anchor->modify('-'.(180+$i).' days')->format('Y-m-d 09:00:00');
        $id=entity('customer',$email,'customers','customers_id',function()use($first,$last,$email,$hash,$province,$countryId,$created){
            $id=insertRow('customers',['customers_firstname'=>$first,'customers_lastname'=>$last,'customers_email_address'=>$email,'customers_telephone'=>'DEMO-SIN-TELEFONO','customers_password'=>$hash,'customers_newsletter'=>'0','status'=>1]);
            $address=insertRow('address_book',['customers_id'=>$id,'entry_firstname'=>$first,'entry_lastname'=>$last,'entry_street_address'=>'Dirección ficticia para demostración','entry_postcode'=>$province[2],'entry_city'=>$province[1],'entry_state'=>$province[0],'entry_country_id'=>$countryId,'entry_zone_id'=>0]);
            run('UPDATE customers SET customers_default_address_id=? WHERE customers_id=?',[$address,$id]);
            insertRow('customers_info',['customers_info_id'=>$id,'customers_info_date_account_created'=>$created,'customers_info_number_of_logons'=>0]);
            return $id;
        });
        $customers[]=['id'=>$id,'name'=>$first.' '.$last,'email'=>$email,'province'=>$province];
    }
    $cancel=entity('status','cancelled','orders_status','orders_status_id',function()use($languageIds){
        $id=(int)rows('SELECT COALESCE(MAX(orders_status_id),0)+1 AS id FROM orders_status')[0]['id'];
        foreach($languageIds as $lang) insertRow('orders_status',['orders_status_id'=>$id,'language_id'=>$lang,'orders_status_name'=>'Cancelado · DEMO','public_flag'=>1,'downloads_flag'=>0]);
        return $id;
    });
    for($i=0;$i<240;$i++) {
        $customer=$customers[($i*7+intdiv($i,13))%40]; $age=($i*17)%180;
        $purchased=$anchor->modify('-'.$age.' days')->setTime(8+($i%11),($i*11)%60);
        $status=($i%11===0)?$cancel:($age>3?3:($age>0?2:1));
        entity('order',sprintf('order-%03d',$i+1),'orders','orders_id',function()use($i,$customer,$purchased,$status,$cancel,$products,$countryId,$format){
            $data=['customers_id'=>$customer['id'],'customers_telephone'=>'DEMO-SIN-TELEFONO','customers_email_address'=>$customer['email'],'payment_method'=>['Contra entrega · DEMO','Transferencia simulada · DEMO','Pago ficticio · DEMO'][$i%3],'date_purchased'=>$purchased->format('Y-m-d H:i:s'),'last_modified'=>$purchased->modify('+1 hour')->format('Y-m-d H:i:s'),'orders_status'=>$status,'currency'=>'USD','currency_value'=>1];
            foreach(['customers','delivery','billing'] as $prefix) {
                $data[$prefix.'_name']=$customer['name']; $data[$prefix.'_street_address']='Dirección ficticia para demostración';
                $data[$prefix.'_city']=$customer['province'][1]; $data[$prefix.'_postcode']=$customer['province'][2];
                $data[$prefix.'_state']=$customer['province'][0]; $data[$prefix.'_country']='Costa Rica';
                $data[$prefix.'_country_id']=$countryId; $data[$prefix.'_address_format_id']=$format;
            }
            if($status===3) $data['orders_date_finished']=$purchased->modify('+2 days')->format('Y-m-d H:i:s');
            $id=insertRow('orders',$data); $subtotal=0;
            for($j=0;$j<2+($i%3);$j++) {
                $product=$products[($i*5+$j*7)%count($products)]; $qty=1+(($i+$j)%3); $subtotal+=$product['cents']*$qty;
                insertRow('orders_products',['orders_id'=>$id,'products_id'=>$product['id'],'products_model'=>$product['model'],'products_name'=>$product['name'],'products_price'=>$product['cents']/100,'final_price'=>$product['cents']/100,'products_tax'=>0,'products_quantity'=>$qty]);
                if($status!==$cancel) run('UPDATE products SET products_ordered=products_ordered+? WHERE products_id=?',[$qty,$product['id']]);
            }
            $shipping=$subtotal>=3000?0:350;
            foreach([['Sub-total:', $subtotal,'ot_subtotal',1],['Envío simulado:', $shipping,'ot_shipping',2],['Total:', $subtotal+$shipping,'ot_total',4]] as [$title,$amount,$class,$sort]) insertRow('orders_total',['orders_id'=>$id,'title'=>$title,'text'=>money($amount),'value'=>$amount/100,'class'=>$class,'sort_order'=>$sort]);
            insertRow('orders_status_history',['orders_id'=>$id,'orders_status_id'=>1,'date_added'=>$purchased->format('Y-m-d H:i:s'),'customer_notified'=>0,'comments'=>sprintf('[DEMO TN-%03d] Pedido y cliente completamente ficticios. Sin cobro ni correo real.',$i+1)]);
            if($status!==1) insertRow('orders_status_history',['orders_id'=>$id,'orders_status_id'=>$status,'date_added'=>$purchased->modify('+1 hour')->format('Y-m-d H:i:s'),'customer_notified'=>0,'comments'=>'Estado simulado para análisis académico.']);
            return $id;
        });
    }
    config('SEND_EMAILS','false');
    insertRow('demo_seed_runs',['seed_version'=>'vintara-v1','anchor_date'=>$anchor->format('Y-m-d'),'completed_at'=>date('Y-m-d H:i:s')]);
    $db->commit();
    echo "Demo completed: 18 products, 40 customers, 240 orders; anchor ".$anchor->format('Y-m-d').". No duplicates on rerun.\n";
} catch(Throwable $e) { $db->rollback(); throw $e; }
finally { $db->query("SELECT RELEASE_LOCK('vintara_seed')"); }
