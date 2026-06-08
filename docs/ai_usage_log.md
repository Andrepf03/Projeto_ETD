# Registo de Uso de IA

Ferramenta: Claude (Anthropic). Cada entrada documenta intencao, requisitos, o que foi
gerado, verificacoes e a revisao/decisao humana.

---

## Entrada 0001 — Fase 0: Especificacao
- **Data:** 2026-05-30
- **Intencao:** Produzir a especificacao completa do projeto (dominio Musica) antes de
  qualquer codigo, em abordagem spec-driven.
- **Requisitos visados:** prompt seccao 9 (12 pontos); criterios de avaliacao 1-8.
- **O que foi gerado:** intencao/problema; 4+1 perguntas analiticas; fontes (+APIs);
  requisitos RF/RNF; arquitetura + diagrama Mermaid do pipeline; modelo medallion +
  star schema + ERD; regras de qualidade; stack justificada; plano semanal; riscos;
  criterios de aceitacao.
- **Verificacoes de facto (pesquisa web):**
  - Spotify descontinuou audio-features/analysis/recommendations para apps novas
    (desde 27/11/2024) -> features passam a vir de dataset + validacao ReccoBeats.
  - ReccoBeats: substituto gratuito das audio features (limites internos -> amostra).
  - Million Playlist Dataset ja nao e descarregavel -> grande volume vem do Kaggle.
  - MusicBrainz: 1 req/s por IP, User-Agent obrigatorio.
- **Revisao humana (Andre/Manuel):**
  - [ ] Pivot das fontes de audio aprovado?
  - [ ] Perguntas analiticas aprovadas/alteradas?
  - [ ] Stack confirmada (Prefect+Makefile / DuckDB / Streamlit / pandera)?

---

## Entrada 0002 — Fase 0: Scaffold + afinacao das fontes
- **Data:** 2026-05-30
- **Intencao:** Gerar a estrutura inicial do repositorio e afinar a fonte de grande
  volume apos inspecao das prints (Spotify Dashboard + pagina Kaggle).
- **O que foi gerado:** arvore de pastas, README, .env.example, .gitignore,
  pyproject.toml, config.yaml, .pre-commit-config.yaml, CI (GitHub Actions),
  esqueletos (src/run.py, prefect_flow.py, dashboard/app.py), teste smoke, docs e
  diagramas Mermaid. Sem logica de implementacao (respeita a fase spec-driven).
- **Verificacoes de facto (pesquisa web):**
  - Redirect URI do Spotify: desde 09/04/2025, apps novas exigem HTTPS ou loopback
    explicito (http://127.0.0.1:PORT); "localhost" nao e aceite.
  - Dataset "Spotify 1.2M+ Songs" (rodolfofigueroa, tracks_features.csv): audio
    features + year, SEM popularity/genre; licenca "Unknown".
  - Recomendado como fonte principal: "Spotify_1Million_Tracks" (amitanshjoshi), que
    inclui popularity + genre + year + audio features.
- **Decisao humana (a registar):**
  - Fonte principal escolhida: __________
  - Incluir fonte secundaria (1.2M): sim / nao
  - Incluir Last.fm (Q5): sim / nao

---

## Entrada 0003 — Semana 1: Extract
- **Data:** 2026-05-31
- **Intencao:** Implementar a fase de extracao (modular e reproduzivel).
- **Requisitos visados:** RF1, RF2, RNF4; criterios 1 (eng. de dados) e 2 (reprodutibilidade).
- **O que foi gerado:** src/common (config, logging, http com retry), src/extract
  (ingest_dataset via DuckDB com Parquet particionado; musicbrainz; reccobeats;
  make_sample), src/run.py com a fase extract ligada, amostra sintetica em data/samples,
  docs/source_inventory.md. Spotify marcada como opcional (config + README).
- **Decisao de engenharia:** ingestao com DuckDB (COPY ... PARTITION_BY decade) le o CSV
  em streaming -> baixa memoria num laptop; APIs como passos opcionais e resilientes
  (try/except + flags em config) para o core correr sem rede.
- **Verificacao humana (a fazer):** abrir o CSV real e confirmar o cabecalho; correr
  `python -m src.run extract` e verificar a contagem de linhas vs ficheiro; inspecionar
  data/staging/bronze/dataset/decade=*/.

---

## Entrada 0004 — Semana 2: Transform
- **Data:** 2026-05-31
- **Intencao:** Limpeza/normalizacao, cruzamento dataset<->MusicBrainz e regras de qualidade.
- **Requisitos visados:** RF3, RF4, RF5; criterios 1 (eng.), 2 (qualidade), 3 (analise).
- **O que foi gerado:** src/transform/clean.py (bronze->silver: remove coluna-indice,
  TRY_CAST, dedupe por track_id, artist_key normalizado), src/transform/match.py
  (juncao por artist_key + match_method), src/quality/rules.py (Pydantic SilverTrack),
  src/quality/report.py (relatorio + gate SQL), run.py com a fase transform ligada.
- **Decisao analitica:** pergunta 2 reformulada para ano-a-ano (2000-2023), por o dataset
  cobrir so 3 decadas.
- **Decisoes de eng.:** matching exato por artist_key (minusculas, sem acentos, so
  alfanumerico); qualidade em SQL sobre todos os dados + Pydantic numa amostra; gate
  aborta se houver track_id nulos/duplicados.
- **Verificacao humana (a fazer):** correr `python -m src.run transform`; ler
  docs/quality_report.md (cobertura de country, nulos, dominios); decidir se sobe
  `musicbrainz_sample_artists` para reforcar a pergunta 3.

---

## Entrada 0005 — Semana 3: Load
- **Data:** 2026-05-31
- **Intencao:** Construir o data warehouse analitico (star schema) a partir do silver.
- **Requisitos visados:** RF6; criterios 1 (modelacao/camadas) e 2 (validacao).
- **O que foi gerado:** src/load/build_warehouse.py (dim_artist/dim_genre/dim_time/
  dim_region + fact_track/fact_track_popularity em DuckDB), src/load/validate.py
  (integridade referencial + gate), run.py com a fase load ligada, docs/data_model.md
  (descricao da modelacao), ERD (docs/diagrams/erd.mmd) alinhado com o implementado.
- **Decisoes:** medallion (bronze/silver/gold) + star schema na gold; surrogate keys
  nas dimensoes; track_sk = track_id; gold em DuckDB (embebido, consultavel pelo dashboard).
- **Verificacao humana (a fazer):** correr `python -m src.run load`; ler
  docs/load_validation.md (estado OK, sem orfas/duplicados); abrir o curated.duckdb e
  testar uma consulta (ex.: media de energia por genero).

---

## Entrada 0006 — Semana 4: Visualization (dashboard)
- **Data:** 2026-05-31
- **Intencao:** Construir o dashboard interativo orientado a insights sobre a camada gold.
- **Requisitos visados:** RF7; criterios 3 (interpretacao), 4 (dashboard/comunicacao).
- **O que foi gerado:** dashboard/app.py (Streamlit + Plotly) a ler curated.duckdb, com
  5 separadores: Visao geral, Q1 (audio x popularidade, correlacoes + dispersao),
  Q2 (evolucao 2000-2023), Q3 (geografia, subconjunto com origem), Q4 (generos +
  heatmap normalizado). pandas adicionado as dependencias.
- **Decisoes analiticas:** Q1 apresentada como correlacao (nao causal), com aviso sobre
  confundidores (curadoria/algoritmo); Q3 sinaliza a cobertura parcial; heatmap de
  generos normalizado por feature para comparar padroes apesar das escalas diferentes.
- **Verificacao (feita):** todas as consultas SQL do dashboard validadas contra um
  warehouse de teste. **A fazer pelo humano:** `streamlit run dashboard/app.py` sobre os
  dados reais e interpretar criticamente cada vista (observacao -> hipotese -> conclusao).
