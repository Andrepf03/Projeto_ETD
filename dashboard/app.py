"""Dashboard interativo (Streamlit) — Projeto ETD Musica & Entretenimento.

Le a camada gold (data/curated/curated.duckdb) e responde as perguntas analiticas.
Correr a partir da raiz do projeto:  streamlit run dashboard/app.py
"""

from __future__ import annotations

import sys
from pathlib import Path

# garantir que 'src' e importavel quando lancado via streamlit
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import duckdb
import pandas as pd
import plotly.express as px
import streamlit as st

try:
    from src.common.config import get_config

    DB = Path(get_config()["paths"]["duckdb"])
except Exception:
    DB = Path("data/curated/curated.duckdb")

FEATURES = ["danceability", "energy", "valence", "acousticness", "loudness", "tempo"]

st.set_page_config(page_title="Projeto ETD — Musica", layout="wide")


@st.cache_data(show_spinner=False)
def q(sql: str) -> pd.DataFrame:
    con = duckdb.connect(str(DB), read_only=True)
    try:
        return con.sql(sql).to_df()
    finally:
        con.close()


if not DB.exists():
    st.title("Projeto ETD — Musica & Entretenimento")
    st.error(f"Warehouse nao encontrado em '{DB}'. Corre primeiro:  python -m src.run load")
    st.stop()

st.title("Projeto ETD — Musica & Entretenimento")
st.caption(
    "Dados: dataset Spotify (~1,16M faixas, 2000-2023) + MusicBrainz (origem do artista) "
    "+ ReccoBeats (validacao de audio features)."
)

tabs = st.tabs(
    [
        "Visao geral",
        "Q1 - Audio x Popularidade",
        "Q2 - Evolucao 2000-2023",
        "Q3 - Geografia",
        "Q4 - Generos",
    ]
)

# Visao geral
with tabs[0]:
    r = q(
        """SELECT
             (SELECT COUNT(*) FROM fact_track)  AS n_tracks,
             (SELECT COUNT(*) FROM dim_artist)  AS n_artists,
             (SELECT COUNT(*) FROM dim_genre)   AS n_genres,
             (SELECT COUNT(*) FROM dim_region)  AS n_regions,
             (SELECT MIN(year) FROM dim_time)   AS y0,
             (SELECT MAX(year) FROM dim_time)   AS y1"""
    ).iloc[0]
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Faixas", f"{int(r.n_tracks):,}")
    c2.metric("Artistas", f"{int(r.n_artists):,}")
    c3.metric("Generos", int(r.n_genres))
    c4.metric("Regioes (MusicBrainz)", int(r.n_regions))
    st.write(f"Periodo coberto: **{int(r.y0)}-{int(r.y1)}**.")

    cov = q(
        "SELECT COUNT(*) FILTER (WHERE match_method='mb_artist_key')*100.0/COUNT(*) AS pct "
        "FROM fact_track"
    ).iloc[0].pct
    st.info(
        f"Cobertura de origem geografica (MusicBrainz): **{cov:.1f}%** das faixas. "
        "As analises da Q3 usam apenas esse subconjunto - limitacao a ter em conta."
    )
    st.markdown(
        "**Linhagem:** bronze (Parquet particionado) -> silver (limpo + cruzado) "
        "-> gold (star schema em DuckDB). Detalhe em `docs/`."
    )

# Q1 audio x popularidade
with tabs[1]:
    st.subheader("Que atributos de audio se associam a maior popularidade?")
    st.caption(
        "Hipotese: maior danceability/energy e menor acousticness associam-se a maior popularidade."
    )
    rows = []
    for f in FEATURES:
        c = q(
            f"""SELECT corr(t.{f}, p.spotify_popularity) AS c
                FROM fact_track t JOIN fact_track_popularity p USING (track_sk)
                WHERE t.{f} IS NOT NULL AND p.spotify_popularity IS NOT NULL"""
        ).iloc[0].c
        rows.append({"feature": f, "correlacao": round(c, 3) if c is not None else None})
    cdf = pd.DataFrame(rows).dropna()
    st.plotly_chart(
        px.bar(
            cdf.sort_values("correlacao"),
            x="correlacao",
            y="feature",
            orientation="h",
            title="Correlacao (Pearson) de cada feature com a popularidade",
        ),
        use_container_width=True,
    )
    feat = st.selectbox("Ver dispersao para:", FEATURES, index=0)
    sc = q(
        f"""WITH j AS (
              SELECT t.{feat} AS x, p.spotify_popularity AS y
              FROM fact_track t JOIN fact_track_popularity p USING (track_sk)
              WHERE t.{feat} IS NOT NULL AND p.spotify_popularity IS NOT NULL
            )
            SELECT x, y FROM j USING SAMPLE 5000 ROWS"""
    )
    st.plotly_chart(
        px.scatter(
            sc, x="x", y="y", opacity=0.3,
            labels={"x": feat, "y": "popularity"},
            title=f"{feat} vs popularidade (amostra de 5000 faixas)",
        ),
        use_container_width=True,
    )
    st.warning(
        "Observacao **correlacional**, nao causal: a popularidade e influenciada por "
        "curadoria e algoritmos de recomendacao (confundidores)."
    )

# Q2 evolucao temporal
with tabs[2]:
    st.subheader("Como evoluiram os atributos sonoros ao longo de 2000-2023?")
    chosen = st.multiselect(
        "Features (escalas 0-1; loudness/tempo tem outra escala):",
        FEATURES,
        default=["danceability", "energy", "acousticness"],
    )
    if chosen:
        cols = ", ".join(f"AVG({f}) AS {f}" for f in chosen)
        ev = q(
            f"""SELECT d.year, {cols}
                FROM fact_track t JOIN dim_time d USING (time_sk)
                GROUP BY d.year ORDER BY d.year"""
        )
        ev2 = ev.melt(id_vars="year", var_name="feature", value_name="media")
        st.plotly_chart(
            px.line(ev2, x="year", y="media", color="feature", markers=True,
                    title="Media anual das features (2000-2023)"),
            use_container_width=True,
        )
    st.caption("Nota: 2023 e um ano parcial e o numero de faixas por ano varia.")

# Q3 geografia
with tabs[3]:
    st.subheader("Existem assinaturas sonoras por pais de origem do artista?")
    topn = st.slider("Nr. de paises (por nr. de faixas):", 5, 20, 10)
    feat = st.selectbox("Feature:", FEATURES, index=0, key="geo_feat")
    geo = q(
        f"""SELECT r.country_code, COUNT(*) AS n, AVG(t.{feat}) AS media
            FROM fact_track t
            JOIN dim_artist a USING (artist_sk)
            JOIN dim_region r USING (region_sk)
            WHERE r.country_code IS NOT NULL
            GROUP BY r.country_code HAVING COUNT(*) >= 30
            ORDER BY n DESC LIMIT {topn}"""
    )
    if len(geo):
        st.plotly_chart(
            px.bar(geo.sort_values("media"), x="media", y="country_code", orientation="h",
                   hover_data=["n"],
                   title=f"Media de {feat} por pais (top {topn}, min. 30 faixas)"),
            use_container_width=True,
        )
    else:
        st.info("Sem paises com faixas suficientes - aumenta musicbrainz_sample_artists no extract.")
    st.caption("Apenas faixas com origem identificada na MusicBrainz (cobertura parcial) e paises com >=30 faixas.")

# Q4 generos
with tabs[4]:
    st.subheader("Quao separaveis sao os generos pelo perfil de audio?")
    feat = st.selectbox("Feature:", FEATURES, index=0, key="genre_feat")
    topn = st.slider("Generos a mostrar:", 5, 30, 15, key="genre_n")
    gen = q(
        f"""SELECT g.genre_name, COUNT(*) AS n, AVG(t.{feat}) AS media
            FROM fact_track t JOIN dim_genre g USING (genre_sk)
            GROUP BY g.genre_name ORDER BY n DESC LIMIT {topn}"""
    )
    st.plotly_chart(
        px.bar(gen.sort_values("media"), x="media", y="genre_name", orientation="h",
               hover_data=["n"], title=f"Media de {feat} por genero (top {topn} por nr. de faixas)"),
        use_container_width=True,
    )
    cols = ", ".join(f"AVG({f}) AS {f}" for f in FEATURES)
    hm = q(
        f"""SELECT g.genre_name, {cols}
            FROM fact_track t JOIN dim_genre g USING (genre_sk)
            GROUP BY g.genre_name ORDER BY COUNT(*) DESC LIMIT 15"""
    ).set_index("genre_name")
    hm_norm = (hm - hm.min()) / (hm.max() - hm.min())
    st.plotly_chart(
        px.imshow(hm_norm, aspect="auto", color_continuous_scale="Viridis",
                  title="Perfil medio por genero (top 15) - valores normalizados por feature"),
        use_container_width=True,
    )
    st.caption("Heatmap normalizado: padroes distintos entre linhas = generos distinguiveis pelo audio.")
