FROM postgres:14-alpine

# Copiar configuraciones
COPY postgresql.conf /etc/postgresql/
COPY pg_hba.conf /etc/postgresql/
COPY init.sql /docker-entrypoint-initdb.d/

# Asegurar permisos correctos
RUN chown postgres:postgres /etc/postgresql/postgresql.conf \
    && chown postgres:postgres /etc/postgresql/pg_hba.conf

# Punto de entrada modificado para forzar el uso de nuestras configuraciones
CMD ["postgres", "-c", "config_file=/etc/postgresql/postgresql.conf", "-c", "hba_file=/etc/postgresql/pg_hba.conf"]