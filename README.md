# Projeto ETD — Música & Entretenimento

Pipeline **ETL modular e reproduzível** (Extract → Transform → Load → Visualization)
sobre dados de faixas musicais, terminando num **dashboard interativo orientado a
insights**.

- **Autores:** André Fazendeiro, Manuel Moura
- **Repositório:** https://github.com/Andrepf03/Projeto_ETD
- **Estado:** Fase 0 (especificação + scaffold). Ainda sem lógica de implementação.

> ⚠️ **Nota técnica importante.** A Spotify Web API descontinuou, para *apps novas*
> criadas a partir de 27/11/2024, os endpoints de *audio features* / *audio analysis* /
> *recommendations*. Por isso os atributos de áudio vêm de **datasets históricos** e são
> validados contra a API gratuita **ReccoBeats**. A Spotify Web API é usada apenas para
> metadados ainda disponíveis (pesquisa, faixas, artistas, popularidade, ISRC).

## Perguntas analíticas
1. Que atributos de áudio se associam a maior popularidade?
2. Como evoluíram os atributos sonoros ao longo das décadas?
3. Existem "assinaturas sonoras" por país/região de origem do artista?
4. Quão separáveis são os géneros pelo perfil de áudio?
5. *(opcional)* Popularidade Spotify vs audiência Last.fm.

## Fontes de dados
| Papel | Fonte | Notas |
|---|---|---|
| Grande volume (principal) | Kaggle `amitanshjoshi/spotify-1million-tracks` | ~1M faixas; inclui `popularity`, `genre`, `year` + audio features |
| Grande volume (secundária, opcional) | Kaggle `rodolfofigueroa/spotify-12m-songs` | ~1,2M; audio features + `year`; **sem** `popularity`/`genre`; licença *Unknown* |
| API | ReccoBeats | substituto gratuito das *audio features* (validação de amostra) |
| Complementar | MusicBrainz | país/origem do artista (por nome), tags (1 req/s, *User-Agent* obrigatório) |
| API (opcional) | Spotify Web API | **fechada a apps novas sem Premium**; não usada por defeito. `popularity`/`genre` vêm do dataset; origem vem da MusicBrainz |

> Os ficheiros de dados **não** são versionados (ver `.gitignore`). Coloca os CSV
> descarregados em `data/raw/` com os nomes definidos em `config/config.yaml`.

## Configurar a app do Spotify (OPCIONAL — podes ignorar)
Desde 09/04/2025 a Web API ficou fechada a apps novas sem Premium (a opção "Web API"
aparece a cinzento no *dashboard*). **O projeto corre sem ela** — `popularity` e `genre`
vêm do dataset e a origem geográfica vem da MusicBrainz. Só se tiveres acesso:
1. https://developer.spotify.com/dashboard → **Create app**; **Redirect URI**
   `http://127.0.0.1:8888/callback` (loopback `127.0.0.1`, `localhost` não é aceite).
2. Copia **Client ID**/**Client Secret** para o `.env` e põe `sources.spotify.enabled: true`
   no `config/config.yaml`.

## Instalação e execução
    cp .env.example .env          # (opcional) credenciais; nao e preciso para o core
    uv sync                       # ou: pip install -e ".[dev]"
    # 1) descarrega o dataset do Kaggle -> data/raw/spotify_data.csv
    python -m src.run extract     # Semana 1: CSV -> Parquet particionado + APIs (opc.)
    python -m src.run transform   # Semana 2: limpeza + matching + qualidade
    python -m src.run load        # Semana 3: star schema em DuckDB + validacao
    streamlit run dashboard/app.py  # Semana 4: dashboard interativo
    make test                     # testes
    make lint                     # ruff + mypy

Atalho: `python -m src.run all` corre extract -> transform -> load de uma vez.

> Para testar sem o dataset real: `python -m src.extract.ingest_dataset` apos copiar
> `data/samples/spotify_sample.csv` para `data/raw/spotify_data.csv` (amostra sintetica
> incluida, so para *smoke test* — nao usar para analise).

## Estrutura
Ver a árvore do repositório e a pasta `docs/` (dicionário de dados, relatório técnico,
registo de uso de IA e diagramas Mermaid do pipeline e do modelo de dados).

## Documentação
- `docs/technical_report.md` — arquitetura, decisões, limitações.
- `docs/data_dictionary.md` — campos, tipos, origem, regra de transformação.
- `docs/ai_usage_log.md` — registo de uso de IA (intenção, validação, decisão humana).
- `docs/diagrams/pipeline.mmd`, `docs/diagrams/erd.mmd` — diagramas (Mermaid).
