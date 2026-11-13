<?php
// Runtime configuration for the public VM. Does not change the local development environment.
if (PHP_SAPI !== 'cli') exit;
if (getenv('APP_ENV') !== 'azure') exit;
file_put_contents('/etc/apache2/conf-enabled/vintara-proxy.conf', "ServerName localhost\nServerTokens Prod\nServerSignature Off\nSetEnvIf X-Forwarded-Proto \"^https$\" HTTPS=on\n");
file_put_contents('/usr/local/etc/php/conf.d/zz-vintara.ini', "display_errors=Off\nlog_errors=On\nexpose_php=Off\nsession.cookie_httponly=On\n");
mysqli_report(MYSQLI_REPORT_ERROR|MYSQLI_REPORT_STRICT);
$db=new mysqli(getenv('DB_HOST'),getenv('DB_USER'),getenv('DB_PASSWORD'),getenv('DB_NAME'));
$db->set_charset('utf8mb4');
if($db->query("SELECT 1 FROM configuration WHERE configuration_key='AZURE_CREDENTIALS_INITIALIZED'")->num_rows)exit;
$db->begin_transaction();
try{
 $hash=password_hash(getenv('ADMIN_PASSWORD'),PASSWORD_DEFAULT);$name=getenv('ADMIN_USERNAME');
 $s=$db->prepare('UPDATE administrators SET user_password=? WHERE user_name=?');$s->bind_param('ss',$hash,$name);$s->execute();
 if($s->affected_rows!==1)throw new RuntimeException('Expected exactly one administrator to initialize.');
 $hash=password_hash(getenv('DEMO_CUSTOMER_PASSWORD'),PASSWORD_DEFAULT);
 $s=$db->prepare("UPDATE customers c JOIN demo_seed_entities e ON e.entity_type='customer' AND e.entity_id=c.customers_id SET customers_password=?");$s->bind_param('s',$hash);$s->execute();
 // Remove only old local session/login state from the migrated database.
 $db->query('DELETE FROM sessions');$db->query('DELETE FROM whos_online');$db->query("DELETE FROM action_recorder WHERE module='ar_admin_login'");
 $db->query("INSERT INTO configuration(configuration_title,configuration_key,configuration_value,configuration_description,configuration_group_id,sort_order,date_added) VALUES ('Azure credential initialization','AZURE_CREDENTIALS_INITIALIZED','1','Azure-only secrets applied',6,0,NOW())");
 $db->commit();echo "Azure credentials initialized.\n";
}catch(Throwable $e){$db->rollback();throw $e;}
