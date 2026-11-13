<?php
mysqli_report(MYSQLI_REPORT_ERROR | MYSQLI_REPORT_STRICT);
define('DIR_FS_CATALOG', '/var/www/html/');
chdir('/opt/phoenix/install');
require 'includes/application.php';
$db = new Database(getenv('DB_HOST'), getenv('DB_USER'), getenv('DB_PASSWORD'), getenv('DB_NAME'));
$hasConfig = $db->query("SHOW TABLES LIKE 'configuration'")->num_rows > 0;
$initialized = $hasConfig && $db->query("SELECT 1 FROM configuration WHERE configuration_key = 'LOCAL_BOOTSTRAP_COMPLETE'")->num_rows > 0;
if (!$initialized) {
    // Upstream SQL omits this DROP; allow retry after an interrupted first install.
    $db->query("DROP TABLE IF EXISTS outgoing_tpl_info");
    foreach (['phoenix.sql', 'phoenix_data_sample.sql'] as $file) {
        if (!Installer::load_sql($db, '/opt/phoenix/install/' . $file)) {
            throw new RuntimeException('Cannot import ' . $file);
        }
    }
    Installer::configure('STORE_NAME', 'Proyecto IF6201 - Phoenix Cart');
    Installer::configure('STORE_OWNER', 'Equipo IF6201');
    Installer::configure('STORE_OWNER_EMAIL_ADDRESS', 'tienda@example.test');
    Installer::configure('SESSION_WRITE_DIRECTORY', '/var/www/html/includes/work/');
    $stmt = $db->prepare('INSERT INTO administrators (user_name, user_password) VALUES (?, ?)');
    $username = getenv('ADMIN_USERNAME');
    $hash = Password::hash(getenv('ADMIN_PASSWORD'));
    $stmt->bind_param('ss', $username, $hash);
    $stmt->execute();
    $db->query("INSERT INTO configuration (configuration_title, configuration_key, configuration_value, configuration_description, configuration_group_id, sort_order, date_added) VALUES ('Local bootstrap', 'LOCAL_BOOTSTRAP_COMPLETE', '1', 'Initialization completed', 6, 0, NOW())");
    echo "Database initialized with sample products.\n";
}
$url = rtrim(getenv('STORE_URL'), '/');
$host = parse_url($url, PHP_URL_HOST);
$common = "<?php\nerror_reporting(E_ALL);\n";
$values = [
 'HTTP_SERVER' => $url,
 'COOKIE_OPTIONS' => ['lifetime'=>0,'domain'=>$host,'path'=>'/','samesite'=>'Lax','secure'=>str_starts_with($url,'https://'),'httponly'=>true],
 'DIR_WS_CATALOG' => '/', 'DIR_FS_CATALOG'=>'/var/www/html/',
 'DB_SERVER'=>getenv('DB_HOST'), 'DB_SERVER_USERNAME'=>getenv('DB_USER'),
 'DB_SERVER_PASSWORD'=>getenv('DB_PASSWORD'), 'DB_DATABASE'=>getenv('DB_NAME'),
];
foreach ($values as $key=>$value) { $common .= 'const '.$key.' = '.var_export($value,true).";\n"; }
$common .= "date_default_timezone_set('America/Costa_Rica');\n";
file_put_contents('/var/www/html/includes/configure.php',$common);
$admin = $common;
foreach (['DIR_WS_ADMIN'=>'/admin/','HTTP_CATALOG_SERVER'=>$url,'DIR_FS_DOCUMENT_ROOT'=>'/var/www/html/','DIR_FS_ADMIN'=>'/var/www/html/admin/','DIR_FS_BACKUP'=>'/var/www/html/admin/backups/'] as $key=>$value) {
 $admin .= 'const '.$key.' = '.var_export($value,true).";\n";
}
file_put_contents('/var/www/html/admin/includes/configure.php',$admin);
chmod('/var/www/html/includes/configure.php',0444);
chmod('/var/www/html/admin/includes/configure.php',0444);
// The installer is outside the Apache document root.






