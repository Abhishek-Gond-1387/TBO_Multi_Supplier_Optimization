FROM postgis/postgis:16-3.4

# Add pgvector to the PostGIS image so both spatial and vector extensions are available.
RUN apt-get update \
    && apt-get install -y --no-install-recommends postgresql-16-pgvector \
    && rm -rf /var/lib/apt/lists/*

COPY init/ /docker-entrypoint-initdb.d/
