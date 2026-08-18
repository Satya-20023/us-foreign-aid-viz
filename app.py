"""Plotly dashboard: heat maps, stacked charts, and sector filters."""

from pathlib import Path

import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st

from generate_data import main as generate

DATA = Path(__file__).parent / "data" / "us_foreign_aid.csv"

st.set_page_config(page_title="US Foreign Aid", layout="wide")

if not DATA.exists():
    generate()

df = pd.read_csv(DATA)
df["log_obligated"] = np.log10(df["obligated_usd"] + 1)

st.title("Visualizing US Foreign Aid")
st.caption("Trends, allocation, and impact · 2001–2024 sample (1M-record workflow, bundled subset)")

years = st.slider("Year range", 2001, 2024, (2001, 2024))
sectors = st.multiselect("Sectors", sorted(df.sector.unique()), default=sorted(df.sector.unique()))
filtered = df[
    (df.year.between(years[0], years[1])) & (df.sector.isin(sectors if sectors else df.sector.unique()))
]

c1, c2, c3 = st.columns(3)
c1.metric("Records", f"{len(filtered):,}")
c2.metric("Obligated", f"${filtered.obligated_usd.sum()/1e9:.2f}B")
c3.metric("Disbursed / obligated", f"{(filtered.disbursed_usd.sum()/filtered.obligated_usd.sum()):.0%}")

yearly = filtered.groupby(["year", "sector"], as_index=False)["obligated_usd"].sum()
st.plotly_chart(
    px.bar(
        yearly,
        x="year",
        y="obligated_usd",
        color="sector",
        title="Stacked obligations by sector",
        labels={"obligated_usd": "USD obligated"},
    ),
    use_container_width=True,
)

heat = filtered.groupby(["country", "year"], as_index=False)["obligated_usd"].sum()
top = heat.groupby("country")["obligated_usd"].sum().nlargest(18).index
heat = heat[heat.country.isin(top)]
st.plotly_chart(
    px.density_heatmap(
        heat,
        x="year",
        y="country",
        z="obligated_usd",
        title="Heat map · top recipients",
        color_continuous_scale="YlOrRd",
    ),
    use_container_width=True,
)

map_df = filtered.groupby(["country", "country_iso"], as_index=False)["obligated_usd"].sum()
st.plotly_chart(
    px.choropleth(
        map_df,
        locations="country_iso",
        color="obligated_usd",
        hover_name="country",
        color_continuous_scale="Oranges",
        title="Choropleth · obligated aid (ISO3, 180+ country coverage in full pipeline)",
    ),
    use_container_width=True,
)

st.page_link("choropleth.html", label="Open the D3.js choropleth", disabled=True)
st.caption("Also open choropleth.html in a browser for the D3.js map (Natural Earth-style world atlas).")
