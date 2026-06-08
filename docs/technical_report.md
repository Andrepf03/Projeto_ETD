# Relatorio Tecnico — Projeto ETD (Musica & Entretenimento)

Autores: Andre Fazendeiro, Manuel Moura.
Repositorio: https://github.com/Andrepf03/Projeto_ETD

## 1. Contexto e problema
Pipeline ETL modular e reproduzivel sobre faixas musicais, terminando num dashboard
interativo orientado a insights. Objetivo: caracterizar o que distingue e populariza a
musica, com preocupacao de engenharia (arquitetura, qualidade, linhagem, reprodutibilidade).

**Restricao tecnica decisiva:** a Spotify Web API fechou os endpoints de *audio features*
a apps novas (desde 27/11/2024) e, em contas sem Premium, a propria Web API esta
indisponivel. O projeto contorna isto: audio features vem de um dataset historico,
validadas contra a API gratuita ReccoBeats; a origem geografica vem da MusicBrainz.

## 2. Perguntas analiticas
1. Que atributos de audio se associam a maior popularidade? (correlacional)
2. Como evoluiram os atributos sonoros ano-a-ano (2000-2023)?
3. Existem assinaturas sonoras por pais de origem do artista?
4. Quao separaveis sao os generos pelo perfil de audio?
5. (Opcional, nao implementada) popularidade Spotify vs audiencia Last.fm.

## 3. Arquitetura
Componentes desacoplados: extract -> transform -> quality -> load -> visualization,
orquestrados por um CLI (`python -m src.run <fase>`) e prontos para Prefect. Execucao
100% local num laptop. Diagrama: `docs/diagrams/pipeline.mmd`.

## 4. Fontes de dados
- **Grande volume:** Kaggle `amitanshjoshi/spotify-1million-tracks` (~1,16M faixas; audio
  features + popularity + genre + year). Engenharia: leitura streaming + Parquet
  particionado por decada (DuckDB).
- **API:** ReccoBeats (audio features; validacao de uma amostra).
- **Complementar:** MusicBrainz (pais/origem do artista por nome; 1 req/s, User-Agent).
- **Opcional:** Spotify Web API (fechada a apps novas sem Premium; nao usada).
Detalhe: `docs/source_inventory.md`.

## 5. Decisoes de Engenharia de Dados
- Modelo **medallion** (bronze/silver/gold) para linhagem + **star schema** na gold para
  o dashboard (ver `docs/data_model.md`; ERD em `docs/diagrams/erd.mmd`).
- Ingestao **out-of-core** com DuckDB (`COPY ... PARTITION_BY`) — baixa memoria.
- APIs como passos **opcionais e resilientes** (retry/backoff; 1 req/s na MusicBrainz;
  try/except + flags em `config.yaml`) -> o core corre sem rede.
- Configuracao centralizada (`config.yaml`); segredos em `.env` (nunca no Git).
- DuckDB como armazenamento gold (embebido, zero-config, consultavel pelo dashboard).

## 6. Decisoes analiticas / Data Science
- A pergunta 2 foi **reformulada** de "decadas" para "ano-a-ano" porque o dataset cobre
  apenas 2000-2023 (3 decadas) — evita conclusoes sobre decadas inexistentes.
- A pergunta 1 e tratada como **correlacional, nao causal**: a popularidade e influenciada
  por curadoria e algoritmos de recomendacao (confundidores).
- Mantem-se a distincao observacao -> hipotese -> conclusao.

### Principais observacoes (A PREENCHER a partir do dashboard)
> Escrever aqui o que observaram em cada vista, distinguindo observacao de hipotese e
> indicando limitacoes:
> - Q1: que features tem maior/menor correlacao com a popularidade?
> - Q2: que tendencias 2000-2023 (ex.: subiu/desceu)?
> - Q3: diferencas de perfil entre paises (lembrar a cobertura baixa)?
> - Q4: que generos sao mais distinguiveis pelo audio?

## 7. Qualidade de dados
Regras antes/durante o transform: contrato de schema (Pydantic), verificacoes SQL sobre
todos os dados (nulos, dominios [0,1] e [0,100], duplicados) e um **gate** que aborta com
`track_id` nulo/duplicado. Relatorio: `docs/quality_report.md`. Validacao pos-load
(integridade referencial): `docs/load_validation.md`.

## 8. Limitacoes e vieses
- Licenca do dataset "Unknown" no Kaggle -> uso academico/nao-comercial.
- Audio features sao um *snapshot* historico (pre-2024); validadas numa amostra (ReccoBeats).
- Cobertura geografica parcial (~0,9% das faixas tem pais) -> Q3 sobre subconjunto;
  enviesamento a reportar. Aumentavel via `musicbrainz_sample_artists`.
- Popularidade do Spotify influenciada por algoritmo/curadoria (confundidor).
- 2023 e ano parcial; nr. de faixas por ano varia.

## 9. Uso de IA
Desenvolvido com apoio do Claude (Anthropic), em abordagem spec-driven, com registo
continuo em `docs/ai_usage_log.md` (intencao, requisitos, o que foi gerado, verificacoes e
revisao humana por fase). As decisoes e validacoes finais sao humanas.

## 10. Proximos passos
- Aumentar a cobertura da MusicBrainz; implementar a Q5 (Last.fm).
- Migrar a orquestracao para Prefect (flow esbocado em `orchestration/`).
- Cross-check sistematico das audio features (dataset vs ReccoBeats).
