import streamlit as st
import plotly.express as px
from database import query

CUSTOM_COLORS = [
    "#4a148c", "#1565c0", "#757575", 
    "#7b1fa2", "#1976d2", "#9e9e9e", 
    "#ab47bc", "#2196f3", "#bdbdbd", 
    "#ce93d8", "#64b5f6", "#e0e0e0"
]
CUSTOM_CONTINUOUS = ["#e0e0e0", "#9e9e9e", "#1976d2", "#4a148c"]

st.set_page_config(
    page_title="Superstore Dashboard",
    page_icon=":material/bar_chart:",
    layout="wide"
)

st.markdown("""
    <style>
        .block-container {
            max-width: 1100px;
        }
    </style>
""", unsafe_allow_html=True)

st.title(":material/analytics: Superstore — Dashboard Analítico")

# ── CARDS DE RESUMO ──────────────────────────────────────
df_totais = query("""
    SELECT 
        SUM(vendas)         AS total_vendas,
        SUM(lucro)          AS total_lucro,
        SUM(quantidade_itens) AS total_itens,
        ROUND(SUM(lucro)/SUM(vendas)*100, 2) AS margem
    FROM fato_vendas
""")

col1, col2, col3, col4 = st.columns(4)
col1.metric(":material/payments: Total Vendas",    f"$ {df_totais['total_vendas'][0]:,.2f}")
col2.metric(":material/trending_up: Lucro Total",     f"$ {df_totais['total_lucro'][0]:,.2f}")
col3.metric(":material/inventory_2: Itens Vendidos",  f"{int(df_totais['total_itens'][0]):,}")
col4.metric(":material/query_stats: Margem de Lucro", f"{df_totais['margem'][0]}%")

st.divider()

# ── FILTROS ──────────────────────────────────────────────
df_anos = query("SELECT DISTINCT ano FROM dim_data ORDER BY ano")
anos = ["Todos"] + df_anos["ano"].astype(str).tolist()
ano_sel = st.selectbox("Filtrar por ano:", anos)

filtro_ano = "" if ano_sel == "Todos" else f"AND d.ano = {ano_sel}"

# ── VENDAS POR CATEGORIA ─────────────────────────────────
query_cat = f"""
    SELECT 
        p.categoria,
        ROUND(SUM(f.vendas), 2)  AS vendas,
        ROUND(SUM(f.lucro), 2)   AS lucro
    FROM fato_vendas f
    JOIN dim_produto p ON f.id_produto = p.id_produto
    JOIN dim_data d    ON f.id_data_pedido = d.id_data
    WHERE 1=1 {filtro_ano}
    GROUP BY p.categoria
    ORDER BY vendas DESC
"""
st.subheader("Vendas e Lucro por Categoria", help=f"```sql\n{query_cat.strip()}\n```")

df_cat = query(query_cat)

col1, col2 = st.columns(2)
with col1:
    fig = px.bar(df_cat, x="categoria", y="vendas",
                 title="Vendas por Categoria", color="categoria",
                 color_discrete_sequence=CUSTOM_COLORS)
    st.plotly_chart(fig, use_container_width=True)
with col2:
    fig = px.bar(df_cat, x="categoria", y="lucro",
                 title="Lucro por Categoria", color="categoria",
                 color_discrete_sequence=CUSTOM_COLORS)
    st.plotly_chart(fig, use_container_width=True)

# ── DESEMPENHO MULTIDIMENSIONAL POR CATEGORIA (RADAR) ─────
query_radar = f"""
    SELECT 
        p.categoria as Categoria,
        SUM(f.vendas) AS Vendas,
        SUM(f.lucro) AS Lucro,
        SUM(f.quantidade_itens) AS Volume,
        (SUM(f.lucro)/SUM(f.vendas))*100 AS Margem
    FROM fato_vendas f
    JOIN dim_produto p ON f.id_produto = p.id_produto
    JOIN dim_data d    ON f.id_data_pedido = d.id_data
    WHERE 1=1 {filtro_ano}
    GROUP BY p.categoria
"""
st.subheader(":material/radar: Desempenho Multidimensional (Radar)", help=f"```sql\n{query_radar.strip()}\n```")

df_radar = query(query_radar)
if not df_radar.empty:
    cols_to_norm = ['Vendas', 'Lucro', 'Volume', 'Margem']
    df_radar_norm = df_radar.copy()
    for col in cols_to_norm:
        max_val = df_radar_norm[col].max()
        if max_val != 0:
            df_radar_norm[col] = df_radar_norm[col] / max_val
            
    df_melt = df_radar_norm.melt(id_vars=['Categoria'], var_name='Métrica', value_name='Score')
    
    fig_radar = px.line_polar(df_melt, r='Score', theta='Métrica', color='Categoria', line_close=True,
                              color_discrete_sequence=CUSTOM_COLORS)
    fig_radar.update_traces(fill='toself')
    st.plotly_chart(fig_radar, use_container_width=True)

# ── VENDAS POR SUBCATEGORIA ───────────────────────────────
query_sub = f"""
    SELECT 
        p.subcategoria,
        ROUND(SUM(f.vendas), 2) AS vendas,
        ROUND(SUM(f.lucro), 2)  AS lucro
    FROM fato_vendas f
    JOIN dim_produto p ON f.id_produto = p.id_produto
    JOIN dim_data d    ON f.id_data_pedido = d.id_data
    WHERE 1=1 {filtro_ano}
    GROUP BY p.subcategoria
    ORDER BY vendas DESC
    LIMIT 10
"""
st.subheader("Top 10 Subcategorias por Receita", help=f"```sql\n{query_sub.strip()}\n```")

df_sub = query(query_sub)

fig = px.bar(df_sub, x="vendas", y="subcategoria",
             orientation="h", color="lucro",
             color_continuous_scale=CUSTOM_CONTINUOUS,
             title="Top 10 Subcategorias — Vendas vs Lucro")
st.plotly_chart(fig, use_container_width=True)

# ── VENDAS POR ESTADO ─────────────────────────────────────
query_estado = f"""
    SELECT 
        l.estado,
        ROUND(SUM(f.vendas), 2) AS vendas,
        ROUND(SUM(f.lucro), 2)  AS lucro
    FROM fato_vendas f
    JOIN dim_localizacao l ON f.id_localizacao = l.id_localizacao
    JOIN dim_data d        ON f.id_data_pedido = d.id_data
    WHERE 1=1 {filtro_ano}
    GROUP BY l.estado
    ORDER BY vendas DESC
    LIMIT 15
"""
st.subheader("Vendas por Estado", help=f"```sql\n{query_estado.strip()}\n```")

df_estado = query(query_estado)

fig = px.bar(df_estado, x="estado", y="vendas",
             color="lucro", color_continuous_scale=CUSTOM_CONTINUOUS,
             title="Top 15 Estados por Vendas")
st.plotly_chart(fig, use_container_width=True)

# ── MAPA DE CALOR (GITHUB STYLE) ──────────────────────────
query_diario = f"""
    SELECT 
        d.data,
        ROUND(SUM(f.vendas), 2) AS vendas
    FROM fato_vendas f
    JOIN dim_data d ON f.id_data_pedido = d.id_data
    WHERE 1=1 {filtro_ano}
    GROUP BY d.data
    ORDER BY d.data
"""
st.subheader("Mapa de Calor (Vendas Diárias)", help=f"```sql\n{query_diario.strip()}\n```")

df_diario = query(query_diario)

import altair as alt
import pandas as pd

if not df_diario.empty:
    df_diario['data'] = pd.to_datetime(df_diario['data'])
    
    heatmap = alt.Chart(df_diario).mark_rect(stroke='white', strokeWidth=2).encode(
        x=alt.X('week(data):O', title='Semana do Ano', axis=alt.Axis(labelAngle=0)),
        y=alt.Y('day(data):O', title='Dia', sort=['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']),
        color=alt.Color('vendas:Q', scale=alt.Scale(range=['#f5f5f5', '#9e9e9e', '#1976d2', '#4a148c']), title='Vendas'),
        tooltip=[alt.Tooltip('data:T', title='Data', format='%Y-%m-%d'), alt.Tooltip('vendas:Q', title='Vendas', format='$,.2f')],
        facet=alt.Facet('year(data):O', columns=1, title=None)
    ).properties(
        width=800,
        height=150
    ).configure_facet(
        spacing=10
    ).configure_view(
        stroke=None
    )
    
    st.altair_chart(heatmap, use_container_width=True)

# ── EVOLUÇÃO MENSAL ───────────────────────────────────────
query_mensal = f"""
    SELECT 
        d.ano,
        d.mes,
        CONCAT(d.ano, '-', LPAD(d.mes, 2, '0')) AS periodo,
        ROUND(SUM(f.vendas), 2) AS vendas,
        ROUND(SUM(f.lucro), 2)  AS lucro
    FROM fato_vendas f
    JOIN dim_data d ON f.id_data_pedido = d.id_data
    WHERE 1=1 {filtro_ano}
    GROUP BY d.ano, d.mes
    ORDER BY d.ano, d.mes
"""
st.subheader("Evolução Mensal de Vendas", help=f"```sql\n{query_mensal.strip()}\n```")

df_mensal = query(query_mensal)

fig = px.line(df_mensal, x="periodo", y="vendas",
              title="Vendas Mensais", markers=True,
              color_discrete_sequence=["#1976d2"])
st.plotly_chart(fig, use_container_width=True)

# ── VENDAS POR SEGMENTO ───────────────────────────────────
query_seg = f"""
    SELECT 
        c.segmento,
        ROUND(SUM(f.vendas), 2) AS vendas,
        ROUND(SUM(f.lucro), 2)  AS lucro
    FROM fato_vendas f
    JOIN dim_cliente c ON f.id_cliente = c.id_cliente
    JOIN dim_data d    ON f.id_data_pedido = d.id_data
    WHERE 1=1 {filtro_ano}
    GROUP BY c.segmento
"""
st.subheader("Vendas por Segmento de Cliente", help=f"```sql\n{query_seg.strip()}\n```")

df_seg = query(query_seg)

col1, col2 = st.columns(2)
with col1:
    fig = px.pie(df_seg, names="segmento", values="vendas",
                 title="Participação por Segmento — Vendas",
                 color_discrete_sequence=CUSTOM_COLORS)
    st.plotly_chart(fig, use_container_width=True)
with col2:
    fig = px.pie(df_seg, names="segmento", values="lucro",
                 title="Participação por Segmento — Lucro",
                 color_discrete_sequence=CUSTOM_COLORS)
    st.plotly_chart(fig, use_container_width=True)
