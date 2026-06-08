# Validacao Pos-Load (Semana 3)

Sobre `data/curated/curated.duckdb`.

## Contagens das tabelas
- dim_artist: 63,575
- dim_genre: 82
- dim_time: 24
- dim_region: 37
- fact_track: 1,159,764
- fact_track_popularity: 1,159,764

## Integridade referencial
- track_sk duplicados em fact_track: 0
- FKs de artista orfas: 0
- FKs de genero orfas: 0
- FKs de tempo orfas: 0
- fact_track sem genre_sk (genero nulo na origem): 0

## Estado: OK
