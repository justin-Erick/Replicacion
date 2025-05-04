# 🔁 **Configuración de Replicación en PostgreSQL con Docker**
Este proyecto configura **replicación física** en PostgreSQL usando contenedores Docker.

---

## 📌 **Archivos críticos**
### 🛠️ `docker-compose.yml`
Define dos servicios:
- **`uno`** (Primary)
- **`dos`** (Standby)

🔹 Configuración incluida:
- Volúmenes persistentes (`db_data_uno`, `db_data_dos`)
- Variables de entorno (usuario, contraseña, DB)
- Red interna `db_network` para comunicación

### 🔑 `uno/pg_hba.conf`  
Configura la autenticación para replicación desde la red Docker:

```conf
host replication replicator 172.25.0.0/16 md5
```

### ⚙️ `uno/postgresql.conf`
Habilita la replicación en el nodo primario:
```conf
wal_level = replica
max_wal_senders = 10
```

### 🏗️ dos/postgresql.conf
Activa el modo réplica en el standby:

```conf
hot_standby = on
```

### 🚀 Cómo ejecutar
1️⃣ Iniciar los contenedores

```conf
docker-compose up -d --build
```

### 2️⃣ Configurar la replicación
🔹 En el Primary (uno)

```conf
docker exec -it uno psql -U admin -d mi_db -c "CREATE USER replicator WITH REPLICATION ENCRYPTED PASSWORD 'replicatorpassword';"
docker exec -it uno psql -U admin -d mi_db -c "SELECT * FROM pg_create_physical_replication_slot('replica_slot');"
```

🔹 En el Standby (dos)
```conf
docker exec -it dos bash -c "PGPASSWORD='replicatorpassword' pg_basebackup -h uno -U replicator -p 5432 -D /var/lib/postgresql/data -P --wal-method=stream -R --slot=replica_slot --verbose"
docker restart dos
```


### 🛠️ Verificación
1️⃣ Comprobar replicación

🔹 En el Primary (uno)

```conf
docker exec -it uno psql -U admin -d mi_db -c "SELECT * FROM pg_stat_replication;"
```
🔹 En el Standby (dos)
```conf
docker exec -it dos psql -U admin -d mi_db -c "SELECT pg_is_in_recovery();"  # Debe devolver 't' (true)
```

### 2️⃣ Probar con datos
🔹 En el Primary (uno):

```conf
docker exec -it uno psql -U admin -d mi_db -c "CREATE TABLE test (id SERIAL, data TEXT); INSERT INTO test (data) VALUES ('Replicación exitosa!');"
```
🔹 En el Standby (dos):
Consulta los datos replicados:

```conf
docker exec -it dos psql -U admin -d mi_db -c "SELECT * FROM test;"
```





