# Estrategia de Modelacao de Dados

## Abordagem: Medallion + Star Schema
- **Bronze** (`data/staging/bronze/`): copia fiel do dataset em Parquet particionado por
  decada (so tipagem + `decade` derivada). Imutavel.
- **Silver** (`data/staging/silver/`): dados limpos (sem coluna-indice, deduplicados,
  `artist_key` normalizado) e **cruzados** com a MusicBrainz (`tracks_matched.parquet`).
- **Gold** (`data/curated/curated.duckdb`): **star schema** pronto para o dashboard.

Justificacao: o medallion documenta a transformacao passo a passo (linhagem,
reprodutibilidade); o star schema e a forma natural de servir consultas analiticas
(factos = faixas/medicoes; dimensoes = contexto).

## Tabelas (gold)
| Tabela | Tipo | Grao | Chave |
|---|---|---|---|
| `fact_track` | Facto | 1 linha por faixa | `track_sk` (= track_id) |
| `fact_track_popularity` | Facto | 1 linha por faixa (snapshot) | `track_sk` (FK) |
| `dim_artist` | Dimensao | 1 por artista (artist_key) | `artist_sk` |
| `dim_genre` | Dimensao | 1 por genero | `genre_sk` |
| `dim_time` | Dimensao | 1 por ano | `time_sk` |
| `dim_region` | Dimensao | 1 por (pais, area) | `region_sk` |

Diagrama: `docs/diagrams/erd.mmd`.

## Chaves e juncoes
- `track_sk = track_id` (natural, unico apos dedupe).
- Surrogate keys (`row_number()`) nas dimensoes.
- Juncoes fact->dim: `artist_key` (artista), `genre_name` (genero), `year` (tempo).
- `dim_artist.region_sk` liga a origem geografica (MusicBrainz) via (country, area).

## Mapeamento perguntas -> consultas
- **Q1 (audio x popularidade):** `fact_track` JOIN `fact_track_popularity`.
- **Q2 (evolucao ano-a-ano):** `fact_track` JOIN `dim_time` (GROUP BY year).
- **Q3 (geografia):** `fact_track` JOIN `dim_artist` JOIN `dim_region` (so faixas com origem).
- **Q4 (genero x audio):** `fact_track` JOIN `dim_genre`.

## Limitacoes
- `dim_time` so tem `year` (o dataset nao traz data completa).
- `dim_region` depende da cobertura da MusicBrainz (parcial; ver `quality_report.md`).
