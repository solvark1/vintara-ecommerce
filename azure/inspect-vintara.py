import subprocess
c=['docker','compose','--env-file','/opt/vintara/azure/cloud.env','-f','/opt/vintara/azure/compose.yaml','exec','-T','db','sh','-c','MYSQL_PWD="$MYSQL_ROOT_PASSWORD" mysql -uroot --batch']
p=subprocess.run(c,input='SHOW TABLES FROM phoenix; DESCRIBE phoenix.reviews; DESCRIBE phoenix.orders_products; DESCRIBE phoenix.categories_description;',text=True,capture_output=True); print(p.stdout); print(p.stderr)
