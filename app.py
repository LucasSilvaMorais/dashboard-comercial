"""
app.py — ponto de entrada do aplicativo.

Rode com:   streamlit run app.py
"""

from datetime import date

import pandas as pd
import streamlit as st

import database as db
import graficos as gr
from estilo import (
    aplicar_estilo, assinatura, marca, cabecalho,
    secao, kpi, moeda, inteiro,
)

st.set_page_config(
    page_title="Painel Comercial",
    page_icon="◆",
    layout="wide",
    initial_sidebar_state="expanded",
)
aplicar_estilo()
assinatura("Lucas Morais")


# ------------------------------------------------------------------
# MENU
# ------------------------------------------------------------------
MENU = [
    ("Dashboard",   ":material/monitoring:"),
    ("Lançamentos", ":material/edit_note:"),
]

if "pagina" not in st.session_state:
    st.session_state.pagina = "Dashboard"


def barra_lateral() -> None:
    with st.sidebar:
        marca(sigla="PC", nome="Painel Comercial", sub="Gestão de vendas")

        for nome, icone in MENU:
            ativo = st.session_state.pagina == nome
            if st.button(
                f"{icone} {nome}",
                key=f"nav_{nome}",
                use_container_width=True,
                type="primary" if ativo else "secondary",
            ):
                st.session_state.pagina = nome
                st.rerun()

        st.markdown(
            "<div style='height:1px;background:#2E3646;margin:1.3rem 0 .8rem'></div>",
            unsafe_allow_html=True,
        )
        st.caption("v0.3 · base local `data/dados.db`")


# ------------------------------------------------------------------
# CÁLCULO DOS INDICADORES
# ------------------------------------------------------------------
def variacao(atual: float, anterior: float) -> float | None:
    """
    Variação percentual entre dois períodos.
    Devolve None quando não há base de comparação — melhor não mostrar
    nada do que mostrar um '+100%' que não significa nada.
    """
    if not anterior:
        return None
    return (atual - anterior) / anterior * 100


def calcular_kpis(df: pd.DataFrame) -> dict:
    """
    Compara a metade mais recente do período com a metade anterior.
    Assim a variação sempre faz sentido, qualquer que seja o filtro.
    """
    if df.empty:
        return {"faturamento": 0, "vendas": 0, "ticket": 0, "clientes": 0,
                "var_fat": None, "var_vendas": None, "var_ticket": None}

    faturamento = df["valor_total"].sum()
    vendas = len(df)
    ticket = faturamento / vendas if vendas else 0
    clientes = df["cliente"].nunique()

    ini, fim = df["data_venda"].min(), df["data_venda"].max()
    meio = ini + (fim - ini) / 2

    recente = df[df["data_venda"] > meio]
    antigo = df[df["data_venda"] <= meio]

    fat_rec, fat_ant = recente["valor_total"].sum(), antigo["valor_total"].sum()
    tk_rec = fat_rec / len(recente) if len(recente) else 0
    tk_ant = fat_ant / len(antigo) if len(antigo) else 0

    return {
        "faturamento": faturamento,
        "vendas": vendas,
        "ticket": ticket,
        "clientes": clientes,
        "var_fat": variacao(fat_rec, fat_ant),
        "var_vendas": variacao(len(recente), len(antigo)),
        "var_ticket": variacao(tk_rec, tk_ant),
    }


# ------------------------------------------------------------------
# PÁGINA: DASHBOARD
# ------------------------------------------------------------------
def pagina_dashboard() -> None:
    cabecalho(
        titulo="Visão geral",
        subtitulo="Faturamento, ranking e composição das vendas",
        eyebrow="Dashboard",
    )

    # ---------- Filtros ----------
    data_min, data_max = db.periodo_disponivel()
    opcoes = db.opcoes_filtro()

    f1, f2, f3 = st.columns([2, 1.4, 1.4], gap="medium")
    with f1:
        periodo = st.date_input(
            "Período",
            value=(data_min, data_max),
            min_value=data_min,
            max_value=data_max,
            format="DD/MM/YYYY",
        )
    with f2:
        canais = st.multiselect("Canal", opcoes["canais"], placeholder="Todos")
    with f3:
        status = st.multiselect(
            "Status", opcoes["status"], default=["Concluída"], placeholder="Todos"
        )

    # Enquanto o usuário escolhe a segunda data, o widget devolve 1 valor só.
    if not isinstance(periodo, tuple) or len(periodo) != 2:
        st.info("Selecione a data final do período.")
        return

    df = db.listar_vendas(
        data_inicio=periodo[0].isoformat(),
        data_fim=periodo[1].isoformat(),
        status=status or None,
        canais=canais or None,
    )

    if df.empty:
        st.warning("Nenhuma venda encontrada com esses filtros.")
        return

    # ---------- KPIs ----------
    k = calcular_kpis(df)
    c1, c2, c3, c4 = st.columns(4, gap="medium")
    with c1:
        kpi("Faturamento", moeda(k["faturamento"]), k["var_fat"], "no período")
    with c2:
        kpi("Vendas", inteiro(k["vendas"]), k["var_vendas"], "lançamentos")
    with c3:
        kpi("Ticket médio", moeda(k["ticket"]), k["var_ticket"], "por venda")
    with c4:
        kpi("Clientes", inteiro(k["clientes"]), legenda="compraram no período")

    # ---------- Gráficos ----------
    secao("Evolução do faturamento")
    st.plotly_chart(gr.evolucao_mensal(df), use_container_width=True)

    g1, g2 = st.columns(2, gap="large")
    with g1:
        secao("Maiores clientes")
        st.plotly_chart(gr.top_clientes(df), use_container_width=True)
    with g2:
        secao("Composição por categoria")
        st.plotly_chart(gr.por_categoria(df), use_container_width=True)

    secao("Desempenho por canal")
    st.plotly_chart(gr.por_canal(df), use_container_width=True)

    # ---------- Detalhamento ----------
    secao("Detalhamento")
    tabela = df[["data_venda", "cliente", "produto", "categoria",
                 "quantidade", "valor_total", "canal", "status"]].copy()
    tabela["data_venda"] = tabela["data_venda"].dt.strftime("%d/%m/%Y")

    st.dataframe(
        tabela,
        use_container_width=True,
        hide_index=True,
        height=320,
        column_config={
            "data_venda":  st.column_config.TextColumn("Data", width="small"),
            "cliente":     st.column_config.TextColumn("Cliente"),
            "produto":     st.column_config.TextColumn("Produto"),
            "categoria":   st.column_config.TextColumn("Categoria", width="small"),
            "quantidade":  st.column_config.NumberColumn("Qtd", width="small"),
            "valor_total": st.column_config.NumberColumn("Total", format="R$ %.2f"),
            "canal":       st.column_config.TextColumn("Canal", width="small"),
            "status":      st.column_config.TextColumn("Status", width="small"),
        },
    )

    st.download_button(
        "Baixar CSV",
        data=tabela.to_csv(index=False).encode("utf-8-sig"),  # utf-8-sig: acentos no Excel
        file_name=f"vendas_{periodo[0]:%Y%m%d}_{periodo[1]:%Y%m%d}.csv",
        mime="text/csv",
    )


# ------------------------------------------------------------------
# PÁGINA: LANÇAMENTOS
# ------------------------------------------------------------------
def pagina_lancamentos() -> None:
    cabecalho(
        titulo="Novo lançamento",
        subtitulo="Registre uma venda e ela aparece no dashboard na hora",
        eyebrow="Lançamentos",
    )

    clientes = db.listar_clientes()
    produtos = db.listar_produtos()

    if clientes.empty or produtos.empty:
        st.warning("Cadastre ao menos um cliente e um produto antes de lançar vendas.")
        return

    mapa_clientes = dict(zip(clientes["nome"], clientes["id"]))
    mapa_produtos = dict(zip(produtos["nome"], produtos["id"]))
    precos = dict(zip(produtos["nome"], produtos["preco_unitario"]))

    with st.form("form_venda", clear_on_submit=True):
        col1, col2 = st.columns(2, gap="large")

        with col1:
            data_venda = st.date_input("Data da venda", value=date.today(), format="DD/MM/YYYY")
            cliente_nome = st.selectbox("Cliente", options=list(mapa_clientes.keys()))
            produto_nome = st.selectbox("Produto", options=list(mapa_produtos.keys()))
            quantidade = st.number_input("Quantidade", min_value=1, value=1, step=1)

        with col2:
            preco = st.number_input(
                "Preço unitário (R$)",
                min_value=0.0,
                value=float(precos[produto_nome]),
                step=10.0,
                format="%.2f",
                help="Vem do cadastro do produto; ajuste se houve desconto.",
            )
            canal = st.selectbox("Canal", ["Loja", "E-commerce", "Representante", "Televendas"])
            status = st.selectbox("Status", ["Concluída", "Pendente", "Cancelada"])
            observacao = st.text_area("Observação", placeholder="Opcional", height=80)

        st.markdown(
            f"<div style='color:#8A93A6;font-size:.85rem;margin:.5rem 0 1rem'>"
            f"Total do lançamento: <strong style='color:#E9A93C;font-family:IBM Plex Mono,monospace'>"
            f"{moeda(quantidade * preco)}</strong></div>",
            unsafe_allow_html=True,
        )

        enviado = st.form_submit_button("Salvar lançamento", type="primary")

    if enviado:
        if data_venda > date.today():
            st.error("A data da venda não pode ser futura.")
        elif preco <= 0:
            st.error("Informe um preço unitário maior que zero.")
        else:
            try:
                novo_id = db.inserir_venda(
                    data_venda=data_venda.isoformat(),
                    cliente_id=int(mapa_clientes[cliente_nome]),
                    produto_id=int(mapa_produtos[produto_nome]),
                    quantidade=int(quantidade),
                    preco_unitario=float(preco),
                    canal=canal,
                    status=status,
                    observacao=observacao,
                )
                st.success(f"Lançamento #{novo_id} salvo — {moeda(quantidade * preco)}")
            except Exception as erro:
                st.error(f"Não foi possível salvar: {erro}")

    secao("Últimos lançamentos")

    df = db.listar_vendas().head(10)
    if df.empty:
        st.info("Nenhuma venda registrada ainda. Use o formulário acima para começar.")
        return

    tabela = df[["data_venda", "cliente", "produto", "quantidade",
                 "valor_total", "canal", "status"]].copy()
    tabela["data_venda"] = tabela["data_venda"].dt.strftime("%d/%m/%Y")

    st.dataframe(
        tabela,
        use_container_width=True,
        hide_index=True,
        column_config={
            "data_venda":  st.column_config.TextColumn("Data", width="small"),
            "cliente":     st.column_config.TextColumn("Cliente"),
            "produto":     st.column_config.TextColumn("Produto"),
            "quantidade":  st.column_config.NumberColumn("Qtd", width="small"),
            "valor_total": st.column_config.NumberColumn("Total", format="R$ %.2f"),
            "canal":       st.column_config.TextColumn("Canal", width="small"),
            "status":      st.column_config.TextColumn("Status", width="small"),
        },
    )


# ------------------------------------------------------------------
# ROTEAMENTO
# ------------------------------------------------------------------
ROTAS = {
    "Dashboard": pagina_dashboard,
    "Lançamentos": pagina_lancamentos,
}

barra_lateral()
ROTAS[st.session_state.pagina]()