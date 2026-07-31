"""
graficos.py — todos os gráficos do app.

Por que separado: o Plotly precisa de ~15 linhas de configuração de tema
por gráfico. Centralizando aqui, o app.py fica legível e todo gráfico
nasce com a mesma aparência.
"""

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from estilo import PALETA, CORES_GRAFICO


def _aplicar_tema(fig: go.Figure, altura: int = 320) -> go.Figure:
    """
    Aplica o tema escuro do app a qualquer figura Plotly.

    Fundo transparente: assim o gráfico herda o fundo da página em vez
    de virar um retângulo branco no meio do tema escuro.
    """
    fig.update_layout(
        height=altura,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="IBM Plex Sans, sans-serif", size=12, color=PALETA["mute"]),
        margin=dict(l=10, r=10, t=30, b=10),
        hoverlabel=dict(
            bgcolor=PALETA["surface_2"],
            bordercolor=PALETA["border"],
            font_size=12,
            font_family="IBM Plex Sans",
        ),
        xaxis=dict(gridcolor=PALETA["border"], zeroline=False, title=None),
        yaxis=dict(gridcolor=PALETA["border"], zeroline=False, title=None),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0, title=None),
        showlegend=False,
    )
    return fig


def evolucao_mensal(df: pd.DataFrame) -> go.Figure:
    """Área + linha do faturamento por mês."""
    serie = (
        df.groupby(df["data_venda"].dt.to_period("M"))["valor_total"]
        .sum()
        .reset_index()
    )
    serie["data_venda"] = serie["data_venda"].dt.to_timestamp()

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=serie["data_venda"],
            y=serie["valor_total"],
            mode="lines+markers",
            line=dict(color=PALETA["accent"], width=2.5, shape="spline"),
            marker=dict(size=6, color=PALETA["accent"]),
            fill="tozeroy",
            fillcolor="rgba(233,169,60,0.10)",  # âmbar translúcido
            hovertemplate="%{x|%b/%Y}<br>R$ %{y:,.2f}<extra></extra>",
        )
    )
    fig.update_xaxes(dtick="M1", tickformat="%b/%y")
    return _aplicar_tema(fig, altura=300)


def top_clientes(df: pd.DataFrame, n: int = 6) -> go.Figure:
    """Barras horizontais — ranking por faturamento."""
    dados = (
        df.groupby("cliente")["valor_total"].sum()
        .sort_values(ascending=True)  # ascending para o maior ficar no topo
        .tail(n)
        .reset_index()
    )

    fig = go.Figure(
        go.Bar(
            x=dados["valor_total"],
            y=dados["cliente"],
            orientation="h",
            marker=dict(color=PALETA["accent"], line=dict(width=0)),
            hovertemplate="%{y}<br>R$ %{x:,.2f}<extra></extra>",
        )
    )
    fig.update_layout(bargap=0.45)
    return _aplicar_tema(fig, altura=300)


def por_categoria(df: pd.DataFrame) -> go.Figure:
    """Rosca — participação de cada categoria no faturamento."""
    dados = df.groupby("categoria")["valor_total"].sum().reset_index()

    fig = go.Figure(
        go.Pie(
            labels=dados["categoria"],
            values=dados["valor_total"],
            hole=0.62,  # rosca em vez de pizza: o centro vazio pesa menos
            marker=dict(colors=CORES_GRAFICO, line=dict(color=PALETA["bg"], width=2)),
            textinfo="percent",
            textfont=dict(size=11, color=PALETA["bg"]),
            hovertemplate="%{label}<br>R$ %{value:,.2f}<extra></extra>",
        )
    )
    fig = _aplicar_tema(fig, altura=300)
    fig.update_layout(showlegend=True)
    return fig


def por_canal(df: pd.DataFrame) -> go.Figure:
    """Barras verticais — faturamento por canal de venda."""
    dados = (
        df.groupby("canal")["valor_total"].sum()
        .sort_values(ascending=False)
        .reset_index()
    )

    fig = go.Figure(
        go.Bar(
            x=dados["canal"],
            y=dados["valor_total"],
            marker=dict(color=PALETA["accent"], line=dict(width=0)),
            hovertemplate="%{x}<br>R$ %{y:,.2f}<extra></extra>",
        )
    )
    fig.update_layout(bargap=0.55)
    return _aplicar_tema(fig, altura=300)