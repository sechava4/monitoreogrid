## Allow remote access to mysql db on ubuntu server

Instrucciones detalladas:
- https://www.digitalocean.com/community/tutorials/how-to-allow-remote-access-to-mysql

Para la configuración necesitamos un hostname, se saca intentándose conectar desde python mysq:
```
mysql.connector.connect(
                user="admin",
                password="actuadores",
                host="104.236.94.94",
                database="monitoreodb",
            )
```
Obtendremos un output como el siguiene:
```
mysql.connector.errors.DatabaseError: 1130: Host '179.14.141.215' is not allowed to connect to this MySQL server

```
De allí extraemos el hostmane. En este caso 179.14.141.215

- Entramos al servidor con putty:

![image](https://user-images.githubusercontent.com/37352122/139784925-99fe37e6-cfe3-4931-8d01-ac60bc84d1b0.png)

Luego ejecutamos los siguientes comandos:
```
sudo mysql
create user  'admin'@'179.14.141.215' identified by 'actuadores';
grant all on monitoreodb.* to 'admin'@'179.14.141.215';
 GRANT CREATE, ALTER, DROP, INSERT, UPDATE, DELETE, SELECT, REFERENCES, RELOAD on *.* TO 'admin'@'179.14.141.215' WITH GRANT OPTION;
exit
sudo ufw allow from 179.14.141.215 port 3306
```
Finalente, configuramos mysql para conectarse a la base de datos remota:

![image](https://user-images.githubusercontent.com/37352122/139785496-d070dc6e-c4b8-4b7a-8e80-38ac89445d66.png)
