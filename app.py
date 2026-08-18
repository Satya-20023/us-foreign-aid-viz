"""Interactive US bilateral aid explorer using World Bank DC.DAC.USAL.CD."""

from pathlib import Path

import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st

from auth import is_signed_in, render_auth

DATA = Path(__file__).parent / "data" / "us_bilateral_aid.csv"
META = Path(__file__).parent / "data" / "country_meta.csv"
PLOT = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(color="#f3ead8"),
    colorway=["#d4652f", "#e8a06a", "#c9b99a", "#8fbf9f"],
    margin=dict(t=48, r=16, l=16, b=32),
)

st.set_page_config(page_title="Ledger — US Foreign Aid", layout="wide", page_icon="🌍")


@st.cache_data
def load() -> pd.DataFrame:
    frame = pd.read_csv(DATA)
    frame = frame[frame.aid_usd.notna()]
    frame["year"] = frame["year"].astype(int)
    if META.exists():
        meta = pd.read_csv(META)
        frame = frame.merge(meta, left_on="country_iso", right_on="iso3", how="left")
        frame["region"] = frame["region"].fillna("Unknown")
        frame["income"] = frame["income"].fillna("Unknown")
    else:
        frame["region"] = "Unknown"
        frame["income"] = "Unknown"
    return frame


df = load()
user = render_auth("Ledger")
min_y, max_y = int(df.year.min()), int(df.year.max())

st.markdown(
    """
    <style>
      .kicker { letter-spacing:.16em; text-transform:uppercase; color:#e8a06a; font-size:.78rem; }
      div[data-testid="stMetric"] { background:#1b1814; border:1px solid rgba(243,234,216,.12); padding:12px 16px; border-radius:14px; }
    </style>
    <p class="kicker">World Bank · net bilateral aid flows from the United States</p>
    """,
    unsafe_allow_html=True,
)
st.title("Ledger — US foreign aid, 2001–2023")
st.caption(
    "Official development assistance from the U.S. to recipient countries (current US$). "
    "Source: World Bank indicator DC.DAC.USAL.CD."
)

with st.sidebar:
    st.header("Filters")
    years = st.slider("Years", min_y, max_y, (2010, max_y))
    regions = sorted({str(r) for r in df.region.dropna().unique() if str(r) and str(r) != "nan"})
    picked_regions = st.multiselect("Regions", regions, default=regions)
    incomes = sorted({str(r) for r in df.income.dropna().unique() if str(r) and str(r) != "nan"})
    picked_incomes = st.multiselect("Income group", incomes, default=incomes)
    countries = sorted(df.country.dropna().unique())
    wanted = ["Ukraine", "Afghanistan", "Ethiopia", "Jordan", "Egypt, Arab Rep.", "Iraq"]
    picked_default = [name for name in wanted if name in countries]
    picked = st.multiselect("Highlight countries", countries, default=picked_default)
    log_scale = st.toggle("Log color scale on the map", value=True)
    top_n = st.slider("How many recipients on the bar chart", 8, 30, 15)

view = df[
    df.year.between(years[0], years[1])
    & df.region.isin(picked_regions if picked_regions else regions)
    & df.income.isin(picked_incomes if picked_incomes else incomes)
].copy()
if view.empty:
    st.warning("No rows match these filters. Add a region or income group back in the sidebar.")
    st.stop()
totals = view.groupby(["country", "country_iso"], as_index=False)["aid_usd"].sum()
period_sum = view["aid_usd"].sum()
latest_year = view["year"].max()
latest_sum = view.loc[view.year == latest_year, "aid_usd"].sum()

c1, c2, c3, c4 = st.columns(4)
c1.metric("Recipients in view", f"{totals.country.nunique()}")
c2.metric("Aid in selected years", f"${period_sum/1e9:.1f}B")
c3.metric(f"Latest year ({latest_year})", f"${latest_sum/1e9:.1f}B")
peak = totals.sort_values("aid_usd", ascending=False).iloc[0]
c4.metric("Largest recipient", peak.country, f"${peak.aid_usd/1e9:.2f}B")

map_tab, rank_tab, trend_tab, table_tab = st.tabs(
    ["World map", "Rankings", "Country trends", "Data table"]
)

with map_tab:
    map_df = totals.copy()
    map_df["display"] = map_df["aid_usd"].clip(lower=1)
    if log_scale:
        map_df["display"] = np.log10(map_df["display"])
    fig = px.choropleth(
        map_df,
        locations="country_iso",
        color="display",
        hover_name="country",
        hover_data={"aid_usd": ":$,.0f", "country_iso": False, "display": False},
        color_continuous_scale="YlOrRd",
        title=f"Net US bilateral ODA · {years[0]}–{years[1]}",
        labels={"display": "log10 USD" if log_scale else "USD"},
    )
    fig.update_geos(bgcolor="#12100e", lakecolor="#12100e", landcolor="#1b1814", showcountries=True)
    fig.update_layout(height=620, **PLOT)
    st.plotly_chart(fig, use_container_width=True)
    st.caption("Click legend / hover a country. Negative values (net outflows) are rare and dropped from the color scale floor.")

with rank_tab:
    top = totals.nlargest(top_n, "aid_usd")
    fig = px.bar(
        top.sort_values("aid_usd"),
        x="aid_usd",
        y="country",
        orientation="h",
        title=f"Top {top_n} recipients",
        labels={"aid_usd": "USD"},
        color="aid_usd",
        color_continuous_scale="YlOrRd",
    )
    fig.update_layout(height=560, **PLOT)
    st.plotly_chart(fig, use_container_width=True)
    yearly = view.groupby("year", as_index=False)["aid_usd"].sum()
    fig = px.area(yearly, x="year", y="aid_usd", title="Total US bilateral ODA by year")
    fig.update_layout(**PLOT)
    st.plotly_chart(fig, use_container_width=True)
    by_region = view.groupby("region", as_index=False)["aid_usd"].sum()
    fig = px.bar(by_region.sort_values("aid_usd"), x="aid_usd", y="region", orientation="h", title="Aid by region")
    fig.update_layout(**PLOT)
    st.plotly_chart(fig, use_container_width=True)

with trend_tab:
    if not picked:
        st.info("Pick countries in the sidebar to compare trajectories.")
    else:
        series = view[view.country.isin(picked)]
        fig = px.line(
            series,
            x="year",
            y="aid_usd",
            color="country",
            markers=True,
            title="Selected countries over time",
        )
        fig.update_layout(height=480, **PLOT)
        st.plotly_chart(fig, use_container_width=True)
        share = (
            series.groupby("country")["aid_usd"].sum().sort_values(ascending=False)
        )
        fig = px.pie(
            names=share.index,
            values=share.values,
            title="Share among highlighted countries",
            hole=0.45,
        )
        fig.update_layout(**PLOT)
        st.plotly_chart(fig, use_container_width=True)

with table_tab:
    st.dataframe(
        view.sort_values(["year", "aid_usd"], ascending=[True, False]),
        use_container_width=True,
        hide_index=True,
        column_config={"aid_usd": st.column_config.NumberColumn("Aid (USD)", format="$%d")},
    )
    if is_signed_in():
        st.download_button(
            "Download filtered CSV",
            view.to_csv(index=False),
            file_name="us_aid_filtered.csv",
            mime="text/csv",
        )
    else:
        st.caption("Sign in to download the filtered table. Guest mode is explore-only.")
