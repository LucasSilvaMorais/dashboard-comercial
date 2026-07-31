"""
estilo.py — toda a identidade visual do app mora aqui.

Por que um arquivo só: se a cor do acento mudar, você troca em UM lugar
e o app inteiro acompanha. É isso que significa "padronizado".
"""

import base64
from pathlib import Path

import streamlit as st

# ------------------------------------------------------------------
# 1) PALETA — fonte única da verdade das cores
# ------------------------------------------------------------------
PALETA = {
    "bg":        "#12151C",
    "surface":   "#1A1F2B",
    "surface_2": "#232A38",
    "border":    "#2E3646",
    "text":      "#E8EBF2",
    "mute":      "#8A93A6",
    "accent":    "#E9A93C",
    "pos":       "#3DD68C",
    "neg":       "#F2545B",
}

ROSA = "#FF5C8A"  # usado apenas na assinatura

# Sequência de cores dos gráficos: o âmbar lidera, o resto recua em azuis.
CORES_GRAFICO = ["#E9A93C", "#5B8DEF", "#3DD68C", "#B07CD6", "#4FC3D9", "#F2545B"]


# ------------------------------------------------------------------
# 2) CSS GLOBAL
# ------------------------------------------------------------------
CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@500;600;700&family=IBM+Plex+Sans:wght@400;500;600&family=IBM+Plex+Mono:wght@500;600&display=swap');

/* ---------- Tipografia base ---------- */
html, body, [class*="css"], .stApp {
    font-family: 'IBM Plex Sans', -apple-system, sans-serif;
}
h1, h2, h3, h4 {
    font-family: 'Space Grotesk', sans-serif !important;
    letter-spacing: -0.02em;
    color: #E8EBF2;
}

/* ---------- Enxugar o cromo do Streamlit ---------- */
header[data-testid="stHeader"] { background: transparent; }
#MainMenu, footer { visibility: hidden; }
.block-container { padding-top: 2.2rem; padding-bottom: 3rem; max-width: 1400px; }

/* ---------- Sidebar ---------- */
section[data-testid="stSidebar"] {
    background: #1A1F2B;
    border-right: 1px solid #2E3646;
}
section[data-testid="stSidebar"] .block-container { padding-top: 1.5rem; }

/* Botões DENTRO da sidebar = itens de menu.
   Discretos por padrão; o ativo ganha barra âmbar e fundo levemente elevado. */
section[data-testid="stSidebar"] .stButton > button {
    background: transparent !important;
    border: none !important;
    border-left: 2px solid transparent !important;
    border-radius: 6px !important;
    color: #8A93A6 !important;
    font-weight: 500 !important;
    text-align: left !important;
    justify-content: flex-start !important;
    padding: 0.55rem 0.85rem !important;
    box-shadow: none !important;
    transition: all .15s ease;
}
section[data-testid="stSidebar"] .stButton > button:hover {
    background: #232A38 !important;
    color: #E8EBF2 !important;
}
section[data-testid="stSidebar"] .stButton > button[kind="primary"],
section[data-testid="stSidebar"] .stButton > button[kind="primaryFormSubmit"] {
    background: #232A38 !important;
    border: none !important;
    border-left: 2px solid #E9A93C !important;
    color: #E8EBF2 !important;
    font-weight: 600 !important;
}
section[data-testid="stSidebar"] .stButton > button[kind="primary"]:hover {
    background: #2A3242 !important;
    color: #E8EBF2 !important;
}

/* ---------- Botões da área principal ---------- */
div[data-testid="stAppViewContainer"] .stButton > button[kind="primary"] {
    background: #E9A93C;
    color: #12151C;
    border: none;
    border-radius: 7px;
    font-weight: 600;
    padding: 0.5rem 1.4rem;
}
div[data-testid="stAppViewContainer"] .stButton > button[kind="primary"]:hover {
    background: #F5BB58;
    color: #12151C;
}

/* ---------- Campos de formulário ---------- */
.stTextInput input, .stNumberInput input, .stDateInput input,
.stSelectbox div[data-baseweb="select"] > div, .stTextArea textarea {
    background: #12151C !important;
    border: 1px solid #2E3646 !important;
    border-radius: 7px !important;
    color: #E8EBF2 !important;
}
.stTextInput input:focus, .stNumberInput input:focus, .stTextArea textarea:focus {
    border-color: #E9A93C !important;
}
label, .stMarkdown p { color: #C3C9D6; }

/* ---------- Marca da sidebar ---------- */
.marca {
    display: flex; align-items: center; gap: .7rem;
    padding: 0 .3rem 1.1rem .3rem;
    margin-bottom: .9rem;
    border-bottom: 1px solid #2E3646;
}
.marca-sigla {
    width: 34px; height: 34px; flex-shrink: 0;
    display: grid; place-items: center;
    background: #E9A93C; color: #12151C;
    border-radius: 8px;
    font-family: 'Space Grotesk', sans-serif; font-weight: 700; font-size: .95rem;
}
.marca-nome {
    font-family: 'Space Grotesk', sans-serif; font-weight: 600;
    font-size: 1rem; color: #E8EBF2; line-height: 1.15;
}
.marca-sub { font-size: .72rem; color: #8A93A6; letter-spacing: .04em; text-transform: uppercase; }

/* ---------- Cabeçalho de página ---------- */
.cabecalho { margin-bottom: 1.6rem; }
.cabecalho .eyebrow {
    font-family: 'IBM Plex Mono', monospace; font-size: .7rem;
    color: #E9A93C; letter-spacing: .12em; text-transform: uppercase;
    margin-bottom: .35rem;
}
.cabecalho h1 { font-size: 1.85rem; margin: 0 0 .25rem 0; }
.cabecalho .sub { color: #8A93A6; font-size: .92rem; }

/* ---------- Card de KPI (o elemento-assinatura) ---------- */
.kpi {
    background: #1A1F2B;
    border: 1px solid #2E3646;
    border-radius: 12px;
    padding: 1.05rem 1.2rem 1.1rem 1.2rem;
    position: relative;
    overflow: hidden;
    height: 100%;
}
.kpi::before {
    content: ''; position: absolute; top: 0; left: 0;
    width: 46px; height: 2px; background: #E9A93C;
}
.kpi-rotulo {
    font-size: .74rem; color: #8A93A6;
    letter-spacing: .09em; text-transform: uppercase;
    margin-bottom: .55rem;
}
.kpi-valor {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 1.5rem; font-weight: 600; color: #E8EBF2;
    line-height: 1.1;
    white-space: nowrap;
    font-variant-numeric: tabular-nums;
}
.kpi-rodape { margin-top: .5rem; font-size: .78rem; color: #8A93A6; }
.kpi-var { font-family: 'IBM Plex Mono', monospace; font-weight: 600; }
.var-pos { color: #3DD68C; }
.var-neg { color: #F2545B; }

/* ---------- Título de seção ---------- */
.secao {
    font-family: 'Space Grotesk', sans-serif; font-weight: 600;
    font-size: 1.05rem; color: #E8EBF2;
    margin: 2rem 0 .9rem 0; padding-bottom: .5rem;
    border-bottom: 1px solid #2E3646;
}

/* ---------- Tabelas ---------- */
div[data-testid="stDataFrame"] { border: 1px solid #2E3646; border-radius: 10px; }

/* ---------- Acessibilidade ---------- */
*:focus-visible { outline: 2px solid #E9A93C; outline-offset: 2px; }
@media (prefers-reduced-motion: reduce) { * { transition: none !important; } }
</style>
"""


# ------------------------------------------------------------------
# 3) FUNÇÕES DE INTERFACE
# ------------------------------------------------------------------
def aplicar_estilo() -> None:
    """Injeta o CSS. Chame uma vez, logo após st.set_page_config()."""
    st.markdown(CSS, unsafe_allow_html=True)


def marca(sigla: str = "PC", nome: str = "Painel Comercial", sub: str = "Gestão de vendas") -> None:
    """Bloco de identidade no topo da sidebar."""
    st.markdown(
        f"""<div class="marca">
              <div class="marca-sigla">{sigla}</div>
              <div>
                <div class="marca-nome">{nome}</div>
                <div class="marca-sub">{sub}</div>
              </div>
            </div>""",
        unsafe_allow_html=True,
    )


def cabecalho(titulo: str, subtitulo: str = "", eyebrow: str = "") -> None:
    """Cabeçalho padrão de página — mantém todas as telas com o mesmo ritmo."""
    html = '<div class="cabecalho">'
    if eyebrow:
        html += f'<div class="eyebrow">{eyebrow}</div>'
    html += f"<h1>{titulo}</h1>"
    if subtitulo:
        html += f'<div class="sub">{subtitulo}</div>'
    html += "</div>"
    st.markdown(html, unsafe_allow_html=True)


def secao(titulo: str) -> None:
    """Divisor de seção dentro de uma página."""
    st.markdown(f'<div class="secao">{titulo}</div>', unsafe_allow_html=True)


def kpi(rotulo: str, valor: str, variacao: float | None = None, legenda: str = "") -> None:
    """
    Card de indicador.

    rotulo   -> 'Faturamento'
    valor    -> 'R$ 1.087.999' (já formatado)
    variacao -> 12.4 vira '▲ 12,4%' em verde; -3.1 vira '▼ 3,1%' em vermelho
    legenda  -> texto pequeno ao lado da variação
    """
    rodape = ""
    if variacao is not None:
        classe = "var-pos" if variacao >= 0 else "var-neg"
        seta = "▲" if variacao >= 0 else "▼"
        texto = f"{abs(variacao):.1f}".replace(".", ",")
        rodape = f'<span class="kpi-var {classe}">{seta} {texto}%</span>'
        if legenda:
            rodape += f" &nbsp;{legenda}"
    elif legenda:
        rodape = legenda

    st.markdown(
        f"""<div class="kpi">
              <div class="kpi-rotulo">{rotulo}</div>
              <div class="kpi-valor">{valor}</div>
              {f'<div class="kpi-rodape">{rodape}</div>' if rodape else ''}
            </div>""",
        unsafe_allow_html=True,
    )


def moeda(valor: float) -> str:
    """Formata no padrão brasileiro: 1087999.25 -> 'R$ 1.087.999,25'."""
    return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def inteiro(valor: int) -> str:
    """420000 -> '420.000'."""
    return f"{valor:,}".replace(",", ".")


# ------------------------------------------------------------------
# 4) ASSINATURA DO DESENVOLVEDOR
# ------------------------------------------------------------------
CAMINHO_FOTO = Path(__file__).parent / "assets" / "foto.jpg"


@st.cache_data
def _foto_base64() -> str | None:
    """
    Converte a imagem em texto base64.

    Necessário porque o HTML injetado pelo Streamlit não enxerga arquivos
    locais — a imagem precisa viajar embutida na própria tag <img>.
    O cache evita reler o arquivo do disco a cada clique.
    """
    if not CAMINHO_FOTO.exists():
        return None
    return base64.b64encode(CAMINHO_FOTO.read_bytes()).decode()


def assinatura(nome: str = "Lucas Morais") -> None:
    """
    Selo fixo no canto superior direito: foto circular + crédito.

    position: fixed mantém o selo no lugar mesmo com a página rolando.
    Some em telas estreitas para não cobrir o conteúdo.
    """
    b64 = _foto_base64()
    iniciais = "".join(p[0] for p in nome.split()[:2]).upper()

    if b64:
        avatar = f'<img src="data:image/jpeg;base64,{b64}" alt="{nome}">'
    else:
        avatar = f'<div class="assinatura-iniciais">{iniciais}</div>'

    st.markdown(
        f"""
        <style>
        .assinatura {{
            position: fixed;
            top: 14px; right: 26px;
            z-index: 1000;
            display: flex; flex-direction: column;
            align-items: center; gap: .45rem;
            pointer-events: none;
        }}

        /* Anel: gradiente rosa->âmbar girando devagar sob a foto */
        .assinatura-anel {{
            width: 62px; height: 62px;
            border-radius: 50%;
            padding: 2px;
            background: conic-gradient(from 0deg, {ROSA}, #E9A93C, {ROSA});
            box-shadow: 0 0 0 3px #12151C, 0 4px 18px rgba(255,92,138,.28);
            animation: girar 8s linear infinite;
        }}
        @keyframes girar {{ to {{ transform: rotate(360deg); }} }}

        /* A foto gira ao contrário na mesma velocidade: fica parada na tela. */
        .assinatura-anel img,
        .assinatura-iniciais {{
            width: 100%; height: 100%;
            border-radius: 50%;
            object-fit: cover;
            display: block;
            border: 2px solid #12151C;
            animation: girar 8s linear infinite reverse;
        }}
        .assinatura-iniciais {{
            display: grid; place-items: center;
            background: #232A38; color: #E9A93C;
            font-family: 'Space Grotesk', sans-serif;
            font-weight: 700; font-size: 1.1rem;
        }}

        .assinatura-credito {{
            text-align: center;
            line-height: 1.25;
            text-shadow: 0 1px 6px #12151C;
        }}
        .assinatura-credito .por {{
            display: block;
            font-family: 'IBM Plex Mono', monospace;
            font-size: .58rem; font-weight: 600;
            letter-spacing: .13em; text-transform: uppercase;
            color: {ROSA};
        }}
        .assinatura-credito .nome {{
            display: block;
            font-family: 'Space Grotesk', sans-serif;
            font-size: .78rem; font-weight: 600;
            color: #FFFFFF;
        }}

        /* Some em telas estreitas e respeita quem prefere menos animação. */
        @media (max-width: 900px) {{ .assinatura {{ display: none; }} }}
        @media (prefers-reduced-motion: reduce) {{
            .assinatura-anel, .assinatura-anel img, .assinatura-iniciais {{
                animation: none;
            }}
        }}
        </style>

        <div class="assinatura">
          <div class="assinatura-anel">{avatar}</div>
          <div class="assinatura-credito">
            <span class="por">Developed by</span>
            <span class="nome">{nome}</span>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )