FROM postgres:14-alpine

COPY postgresql.conf /etc/postgresql/
COPY pg_hba.conf /etc/postgresql/

RUN chown postgres:postgres /etc/postgresql/postgresql.conf \
    && chown postgres:postgres /etc/postgresql/pg_hba.conf

CMD ["postgres", "-c", "config_file=/etc/postgresql/postgresql.conf", "-c", "hba_file=/etc/postgresql/pg_hba.conf"]