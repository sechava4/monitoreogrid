## Allow remote access to mysql db on ubuntu server
https://www.digitalocean.com/community/tutorials/how-to-allow-remote-access-to-mysql

Para la configuración necesitamos un hostname, se saca intentándose conectar desde python mysq:

- login to the server using putty
sudo mysql

create user  'admin'@'191.95.116.191' identified by ‘actuadores’;
grant all on monitoreodb.* to 'admin'@'191.95.116.191';
 GRANT CREATE, ALTER, DROP, INSERT, UPDATE, DELETE, SELECT, REFERENCES, RELOAD on *.* TO 'admin'@'181.140.41.33' WITH GRANT OPTION;


exit
sudo ufw allow from 191.95.116.191 port 3306