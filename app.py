
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np

st.set_page_config(
    page_title="Agrifood Emissions Dashboard",
    page_icon="🌱",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown('''<style>
    [data-testid="stSidebar"] { background-color: #1a2433; }
    [data-testid="stSidebar"] p,
    [data-testid="stSidebar"] span,
    [data-testid="stSidebar"] div,
    [data-testid="stSidebar"] label,
    [data-testid="stSidebar"] h1,
    [data-testid="stSidebar"] h2,
    [data-testid="stSidebar"] h3 { color: #dce6f0 !important; }
    [data-testid="stSidebar"] .stSelectbox label,
    [data-testid="stSidebar"] .stMultiselect label,
    [data-testid="stSidebar"] .stSlider label { color: #9eb3cc !important; font-size: 0.82rem; }
    [data-testid="metric-container"] {
        background: #f7f9fc; border: 1px solid #e3e8f0;
        border-radius: 10px; padding: 12px 16px;
    }
    [data-testid="stMetricValue"] { font-size: 1.5rem !important; font-weight: 700; color: #1a2433 !important; }
    [data-testid="stMetricLabel"] { font-size: 0.78rem !important; color: #4a5568 !important; }
    .section-header {
        font-size: 1.05rem; font-weight: 700; color: #1a2433;
        border-left: 4px solid #2e86de; padding-left: 10px; margin: 18px 0 10px 0;
    }
    .info-box {
        background: #2c3e55; border-radius: 8px; padding: 10px 14px;
        font-size: 0.83rem; color: #cfe0f0 !important; margin-bottom: 8px;
    }
    div.block-container { padding-top: 1.5rem; }
    .main .block-container, .main p, .main span, .main div { color: #1a2433; }
</style>''', unsafe_allow_html=True)

POLLUTANT_LABELS = {
    "black_carbon": "Black Carbon (Gg)",
    "carbon_monoxide": "Carbon Monoxide (Gg)",
    "mercury": "Mercury (Gg)",
    "ammonia": "Ammonia (Gg)",
    "nm_volatile_organics": "NM Volatile Organics (Gg)",
    "nitrogen_oxides": "Nitrogen Oxides (Gg)",
    "organic_carbon": "Organic Carbon (Gg)",
    "fine_particles_pm10": "Fine Particles PM10 (Gg)",
    "fine_particles_pm2.5": "Fine Particles PM2.5 (Gg)",
    "sulfur_dioxide": "Sulfur Dioxide (Gg)",
}
POLLUTANT_COLS = list(POLLUTANT_LABELS.keys())

import pycountry

def get_country_names():
    names = {}
    for country in pycountry.countries:
        if hasattr(country, 'alpha_3'):
            names[country.alpha_3] = country.name
    # Manual overrides for cleaner display names
    names.update({
        "USA": "United States",
        "GBR": "United Kingdom",
        "IRN": "Iran",
        "RUS": "Russia",
        "KOR": "South Korea",
        "PRK": "North Korea",
        "TZA": "Tanzania",
        "MDA": "Moldova",
        "SYR": "Syria",
        "VEN": "Venezuela",
        "BOL": "Bolivia",
    })
    return names

COUNTRY_NAMES = get_country_names()

@st.cache_data
def load_data():
    df = pd.read_csv("emissions_merged_horizontal.csv")
    df["year"] = df["year"].astype(int)
    for col in POLLUTANT_COLS:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df["total_emissions"] = df[POLLUTANT_COLS].sum(axis=1)
    df["display_name"] = df["REF_AREA"].map(COUNTRY_NAMES).fillna(df["REF_AREA"])
    return df

df = load_data()
all_countries = sorted(df["REF_AREA"].unique())
year_min, year_max = int(df["year"].min()), int(df["year"].max())

with st.sidebar:
    st.markdown("## 🌱 Dashboard Controls")
    st.markdown("---")
    st.markdown("**Country / Region**")
    default_idx = all_countries.index("IND") if "IND" in all_countries else 0
    selected_country = st.selectbox("", all_countries, index=default_idx, label_visibility="collapsed")
    st.markdown("**Year Range**")
    year_range = st.slider("", year_min, year_max, (1995, 2022), label_visibility="collapsed")
    st.markdown("**Primary Pollutant**")
    pollutant_display = {v: k for k, v in POLLUTANT_LABELS.items()}
    selected_pollutant_label = st.selectbox("", list(POLLUTANT_LABELS.values()), label_visibility="collapsed")
    selected_pollutant = pollutant_display[selected_pollutant_label]
    st.markdown("**Comparison Countries**")
    compare_defaults = [c for c in ["USA","CHN","BRA","DEU"] if c in all_countries and c != selected_country][:3]
    compare_countries = st.multiselect("", all_countries, default=[selected_country]+compare_defaults, label_visibility="collapsed")
    st.markdown("---")
    st.markdown('<div class="info-box">Data: FAO Agrifood + JRC Air Pollutants<br>Coverage: 200+ countries · 1990â2022</div>', unsafe_allow_html=True)

mask = (df["REF_AREA"] == selected_country) & df["year"].between(*year_range)
cdf = df[mask].copy()
country_label = COUNTRY_NAMES.get(selected_country, selected_country)

st.markdown(f"## 🌍 Agrifood Emissions — **{country_label}** ({selected_country})")
st.markdown(f"*Exploring air pollutant trends from agrifood systems · {year_range[0]}–{year_range[1]}*")
st.markdown("---")

if not cdf.empty:
    latest = cdf[cdf["year"] == cdf["year"].max()].iloc[0]
    earliest = cdf[cdf["year"] == cdf["year"].min()].iloc[0]
    def safe_delta(a, b):
        return f"{((a-b)/b*100):.1f}%" if b and b!=0 else "N/A"
    c1,c2,c3,c4,c5 = st.columns(5)
    c1.metric("📅 Latest Year", str(int(latest["year"])))
    c2.metric("🏭 Total Emissions", f"{latest['total_emissions']:,.0f} Gg", delta=safe_delta(latest['total_emissions'],earliest['total_emissions']))
    c3.metric(f"📌 {selected_pollutant_label.split(chr(32))[0]}", f"{latest[selected_pollutant]:,.2f}", delta=safe_delta(latest[selected_pollutant],earliest[selected_pollutant]))
    c4.metric("🌡 Agrifood Share", f"{latest['agrifood_share_pct']:.1f}%")
    c5.metric("📊 Data Points", len(cdf))

st.markdown("---")
tab1,tab2,tab3,tab4 = st.tabs(["📈 Trend Analysis","🔬 Pollutant Breakdown","🌐 Global Comparison","📋 Data Table"])

with tab1:
    if cdf.empty:
        st.warning("No data available.")
    else:
        st.markdown('<div class="section-header">Total Emissions vs Selected Pollutant Over Time</div>', unsafe_allow_html=True)
        fig_dual = make_subplots(specs=[[{"secondary_y": True}]])
        fig_dual.add_trace(go.Scatter(x=cdf["year"],y=cdf["total_emissions"],name="Total Emissions (Gg)",mode="lines+markers",line=dict(color="#2e86de",width=2.5),marker=dict(size=5)),secondary_y=False)
        fig_dual.add_trace(go.Scatter(x=cdf["year"],y=cdf[selected_pollutant],name=selected_pollutant_label,mode="lines+markers",line=dict(color="#e84118",width=2.5,dash="dot"),marker=dict(size=5)),secondary_y=True)
        fig_dual.update_layout(hovermode="x unified",legend=dict(orientation="h",yanchor="bottom",y=1.02,xanchor="right",x=1),margin=dict(l=0,r=0,t=40,b=0),height=360,plot_bgcolor="#ffffff",paper_bgcolor="#ffffff")
        fig_dual.update_yaxes(title_text="Total Emissions (Gg)",secondary_y=False,gridcolor="#e8edf3")
        fig_dual.update_yaxes(title_text=selected_pollutant_label,secondary_y=True)
        fig_dual.update_xaxes(gridcolor="#e8edf3")
        st.plotly_chart(fig_dual,use_container_width=True)

        st.markdown('<div class="section-header">Stacked Pollutant Composition Over Time</div>', unsafe_allow_html=True)
        area_df = cdf[["year"]+POLLUTANT_COLS].melt("year",var_name="pollutant",value_name="value")
        area_df["pollutant_label"] = area_df["pollutant"].map(POLLUTANT_LABELS)
        area_df = area_df.dropna(subset=["value"])
        fig_area = px.area(area_df,x="year",y="value",color="pollutant_label",color_discrete_sequence=px.colors.qualitative.Safe,labels={"value":"Emissions (Gg)","year":"Year","pollutant_label":"Pollutant"})
        fig_area.update_layout(hovermode="x unified",height=320,legend=dict(orientation="h",yanchor="bottom",y=1.01,xanchor="right",x=1),margin=dict(l=0,r=0,t=40,b=0),plot_bgcolor="#ffffff",paper_bgcolor="#ffffff")
        fig_area.update_xaxes(gridcolor="#e8edf3")
        fig_area.update_yaxes(gridcolor="#e8edf3")
        st.plotly_chart(fig_area,use_container_width=True)

with tab2:
    if cdf.empty:
        st.warning("No data.")
    else:
        col_a,col_b = st.columns(2)
        with col_a:
            st.markdown('<div class="section-header">Pollutant Share (Latest Year)</div>', unsafe_allow_html=True)
            lr = cdf[cdf["year"]==cdf["year"].max()].iloc[0]
            pv = {POLLUTANT_LABELS[p]:lr[p] for p in POLLUTANT_COLS if pd.notna(lr[p]) and lr[p]>0}
            fig_pie = px.pie(names=list(pv.keys()),values=list(pv.values()),color_discrete_sequence=px.colors.qualitative.Safe,hole=0.38)
            fig_pie.update_traces(textposition="inside",textinfo="percent+label")
            fig_pie.update_layout(showlegend=False,height=340,margin=dict(l=0,r=0,t=20,b=0))
            st.plotly_chart(fig_pie,use_container_width=True)
        with col_b:
            st.markdown('<div class="section-header">Average Annual Emissions by Pollutant</div>', unsafe_allow_html=True)
            av = cdf[POLLUTANT_COLS].mean().reset_index()
            av.columns=["pollutant","avg"]
            av["label"]=av["pollutant"].map(POLLUTANT_LABELS)
            av=av.sort_values("avg",ascending=True)
            fig_bar=px.bar(av,x="avg",y="label",orientation="h",color="avg",color_continuous_scale="Blues",labels={"avg":"Avg Emissions (Gg)","label":""})
            fig_bar.update_layout(coloraxis_showscale=False,height=340,margin=dict(l=0,r=0,t=20,b=0),plot_bgcolor="#ffffff",paper_bgcolor="#ffffff")
            fig_bar.update_xaxes(gridcolor="#e8edf3")
            st.plotly_chart(fig_bar,use_container_width=True)

        st.markdown('<div class="section-header">Correlation Matrix</div>', unsafe_allow_html=True)
        cd = cdf[POLLUTANT_COLS].dropna(how="all").rename(columns=POLLUTANT_LABELS)
        fig_heat=px.imshow(cd.corr(),text_auto=".2f",color_continuous_scale="RdBu_r",zmin=-1,zmax=1)
        fig_heat.update_layout(height=380,margin=dict(l=0,r=0,t=20,b=0))
        st.plotly_chart(fig_heat,use_container_width=True)

        st.markdown(f'<div class="section-header">{selected_pollutant_label} vs Total Emissions</div>', unsafe_allow_html=True)
        fig_sc=px.scatter(cdf,x="total_emissions",y=selected_pollutant,color="year",size=selected_pollutant,size_max=20,hover_data=["year"],color_continuous_scale="Viridis",trendline="ols",labels={"total_emissions":"Total Emissions (Gg)",selected_pollutant:selected_pollutant_label,"year":"Year"})
        fig_sc.update_layout(height=320,margin=dict(l=0,r=0,t=20,b=0),plot_bgcolor="#ffffff",paper_bgcolor="#ffffff")
        fig_sc.update_xaxes(gridcolor="#e8edf3")
        fig_sc.update_yaxes(gridcolor="#e8edf3")
        st.plotly_chart(fig_sc,use_container_width=True)

with tab3:
    if not compare_countries:
        st.info("Select countries in the sidebar.")
    else:
        cmp=df[df["REF_AREA"].isin(compare_countries)&df["year"].between(*year_range)].copy()
        cmp["label"]=cmp["REF_AREA"].map(COUNTRY_NAMES).fillna(cmp["REF_AREA"])
        st.markdown('<div class="section-header">Selected Pollutant Trend</div>', unsafe_allow_html=True)
        fig_cmp=px.line(cmp,x="year",y=selected_pollutant,color="label",markers=True,color_discrete_sequence=px.colors.qualitative.Bold,labels={"label":"Country",selected_pollutant:selected_pollutant_label,"year":"Year"})
        fig_cmp.update_layout(hovermode="x unified",height=340,legend=dict(orientation="h",yanchor="bottom",y=1.02,xanchor="right",x=1),margin=dict(l=0,r=0,t=40,b=0),plot_bgcolor="#ffffff",paper_bgcolor="#ffffff")
        fig_cmp.update_xaxes(gridcolor="#e8edf3")
        fig_cmp.update_yaxes(gridcolor="#e8edf3")
        st.plotly_chart(fig_cmp,use_container_width=True)

        lyr=cmp["year"].max()
        bdf=cmp[cmp["year"]==lyr][["label","total_emissions"]+POLLUTANT_COLS]
        bm=bdf.melt("label",POLLUTANT_COLS,var_name="pollutant",value_name="value")
        bm["pollutant_label"]=bm["pollutant"].map(POLLUTANT_LABELS)
        st.markdown('<div class="section-header">Stacked Emissions — Latest Year</div>', unsafe_allow_html=True)
        fig_gb=px.bar(bm,x="label",y="value",color="pollutant_label",barmode="stack",color_discrete_sequence=px.colors.qualitative.Safe,labels={"value":"Emissions (Gg)","label":"Country","pollutant_label":"Pollutant"})
        fig_gb.update_layout(height=340,legend=dict(orientation="h",yanchor="bottom",y=1.01,xanchor="right",x=1),margin=dict(l=0,r=0,t=50,b=0),plot_bgcolor="#ffffff",paper_bgcolor="#ffffff")
        fig_gb.update_xaxes(gridcolor="#e8edf3")
        fig_gb.update_yaxes(gridcolor="#e8edf3")
        st.plotly_chart(fig_gb,use_container_width=True)

        st.markdown('<div class="section-header">Pollutant Profile Radar (Normalised)</div>', unsafe_allow_html=True)
        rdf=bdf.set_index("label")[POLLUTANT_COLS]
        rn=rdf.div(rdf.max()).fillna(0)
        cats=[POLLUTANT_LABELS[p] for p in POLLUTANT_COLS]
        fig_rad=go.Figure()
        cr=px.colors.qualitative.Bold
        for i,c in enumerate(rn.index):
            v=rn.loc[c].tolist()
            v+=v[:1]
            fig_rad.add_trace(go.Scatterpolar(r=v,theta=cats+cats[:1],fill="toself",name=c,opacity=0.55,line=dict(color=cr[i%len(cr)],width=2)))
        fig_rad.update_layout(polar=dict(radialaxis=dict(visible=True,range=[0,1])),showlegend=True,height=400,margin=dict(l=20,r=20,t=20,b=20))
        st.plotly_chart(fig_rad,use_container_width=True)

with tab4:
    st.markdown('<div class="section-header">Filtered Dataset</div>', unsafe_allow_html=True)
    sc=["REF_AREA","year","agrifood_share_pct","total_emissions"]+POLLUTANT_COLS
    sd=cdf[sc].rename(columns={"REF_AREA":"Country","year":"Year","agrifood_share_pct":"Agrifood Share (%)","total_emissions":"Total Emissions (Gg)",**POLLUTANT_LABELS})
    st.dataframe(sd.style.format({"Agrifood Share (%)":"{:.1f}","Total Emissions (Gg)":"{:,.2f}",**{v:"{:,.4f}" for v in POLLUTANT_LABELS.values()}}).background_gradient(subset=["Total Emissions (Gg)"],cmap="Blues"),use_container_width=True,height=420)
    st.download_button("⬇️ Download CSV",data=sd.to_csv(index=False),file_name=f"emissions_{selected_country}_{year_range[0]}_{year_range[1]}.csv",mime="text/csv")
    st.markdown('<div class="section-header">Summary Statistics</div>', unsafe_allow_html=True)
    st.dataframe(sd.describe().T.style.format("{:.3f}"),use_container_width=True)
