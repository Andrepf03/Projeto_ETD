# Relatorio de Qualidade de Dados (Semana 2)

Gerado automaticamente em 2026-05-31 sobre `data/staging/silver/tracks_matched.parquet`.

## Visao geral
- Linhas (silver): 1,159,764
- Anos: 2000 a 2023
- Generos distintos: 82
- Duplicados por track_id (apos dedupe): 0

## Valores em falta (nulos)
- track_id: 0
- popularity: 0
- genre: 0
- year: 0

## Violacoes de dominio
- popularity fora de [0,100]: 0
- audio features fora de [0,1]: 0

## Cobertura de integracao (cruzamento)
- Faixas com pais de origem (MusicBrainz): 17,343 (1.5%)
  - NOTA: a cobertura e limitada pela amostra de artistas enriquecidos; subir
    `musicbrainz_sample_artists` no config melhora a cobertura (a 1 req/s).

## Validacao de schema (Pydantic, amostra)
- Linhas invalidas na amostra: 0

## Decisoes tomadas
- Coluna de indice do CSV removida no clean.
- Deduplicacao por `track_id` (mantida a faixa de maior popularity).
- `artist_key` normalizado (minusculas, sem acentos, so alfanumerico) para a juncao.
- Gate: aborta se houver track_id nulos ou duplicados no silver.
