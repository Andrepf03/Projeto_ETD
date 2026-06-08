# Dicionario de Dados

> A preencher ao longo das fases. Uma linha por campo de cada tabela/camada.

## Camada `gold` (analitica)

### fact_track
| Campo | Tipo | Origem | Regra de transformacao | Observacoes |
|---|---|---|---|---|
| track_sk | string (PK) | derivado | chave substituta | |
| spotify_track_id | string | dataset / Spotify API | | |
| isrc | string | Spotify API | normalizado e validado | pode faltar |
| title | string | dataset | trim/normalizacao | |
| danceability | float | dataset / ReccoBeats | dominio [0,1] | |
| ... | | | | |

### fact_track_popularity
| Campo | Tipo | Origem | Regra de transformacao | Observacoes |
|---|---|---|---|---|
| track_sk | string (FK) | derivado | | |
| spotify_popularity | int | dataset / Spotify API | dominio [0,100] | |
| snapshot_date | date | execucao | | |
| ... | | | | |

### Dimensoes (dim_artist, dim_genre, dim_time, dim_region)
| Campo | Tipo | Origem | Regra de transformacao | Observacoes |
|---|---|---|---|---|
| ... | | | | |
