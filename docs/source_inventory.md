# Inventario de Fontes (Semana 1 — Extract)

| # | Fonte | Tipo | Acesso | Volume | Licenca | Papel no projeto |
|---|---|---|---|---|---|---|
| 1 | Kaggle `amitanshjoshi/spotify-1million-tracks` (`spotify_data.csv`) | Dataset (CSV) | Download Kaggle (conta gratuita) | ~1.000.000 faixas | ver pagina Kaggle | **Grande volume**; audio features + `popularity` + `genre` + `year`. Responde Q1, Q2, Q4. |
| 2 | ReccoBeats API | API REST | Gratuita, sem chave | amostra (~500 faixas) | ToS ReccoBeats | Audio features "vivas" -> cross-check de qualidade com o dataset. |
| 3 | MusicBrainz API | API REST | Aberta, sem chave (User-Agent obrigatorio, 1 req/s) | amostra (~200 artistas) | dados sob CC0/aberta | Pais/origem do artista (por nome) -> Q3 (assinatura geografica). |
| (opc.) | Spotify Web API | API REST | Fechada a apps novas sem Premium | — | — | Nao usada por defeito; `popularity`/origem cobertos por (1) e (3). |

## Campos-chave por fonte

- **Dataset (1):** `track_id`, `track_name`, `artist_name`, `popularity`, `genre`, `year`,
  e audio features (`danceability`, `energy`, `valence`, `acousticness`, `loudness`,
  `tempo`, `instrumentalness`, `liveness`, `speechiness`, `key`, `mode`, `tempo`,
  `duration_ms`, `time_signature`). **Confirmar o cabecalho ao abrir o CSV.**
- **ReccoBeats (2):** audio features por faixa (mesmas metricas do Spotify depreciado),
  identificadas por `reccobeats_id` (resolvido a partir do `track_id` do Spotify).
- **MusicBrainz (3):** `mb_artist_mbid`, `mb_name`, `country`, `area`, `begin_area`,
  `type`, ligados por **nome de artista**.

## Chaves de cruzamento (matching)

1. `track_id` — liga dataset (1) <-> ReccoBeats (2).
2. **Nome de artista normalizado** (minusculas, sem pontuacao/"feat.") — liga
   dataset (1) <-> MusicBrainz (3). Quando ambiguo, marca-se `needs_review`.
3. Fuzzy `artista + titulo` (RapidFuzz, limiar 90) como recurso quando o exato falha.

## Notas / limitacoes ja identificadas
- A licenca do dataset deve ser verificada na pagina Kaggle; uso academico/nao-comercial.
- Audio features do dataset sao um **snapshot historico**; a ReccoBeats valida uma amostra.
- Cobertura de `country` na MusicBrainz e **parcial** -> reportar enviesamento em Q3.
