"""
database.py — camada de acesso aos dados.

Regra do projeto: nenhum SQL fora deste arquivo.
O app.py chama funções (listar_vendas, inserir_venda...) e recebe DataFrames.
Se um dia o banco mudar de SQLite para outro, só este arquivo muda.
"""

import sqlite3
from contextlib import contextmanager
from pathlib import Path

import pandas as pd
import streamlit as st

CAMINHO_BANCO = Path(__file__).parent / "data" / "dados.db"


# ==================================================================
# CONEXÃO
# ==================================================================
@contextmanager
def conectar():
    """
    Abre uma conexão, garante o commit e fecha ao final — mesmo se der erro.

    Uso:
        with conectar() as con:
            con.execute(...)

    O PRAGMA foreign_keys precisa ser ligado em TODA conexão: o SQLite
    ignora chaves estrangeiras por padrão. Sem ele, dá para gravar uma
    venda apontando para um cliente que não existe.
    """
    if not CAMINHO_BANCO.exists():
        raise FileNotFoundError(
            f"Banco não encontrado em {CAMINHO_BANCO}. Rode: python criar_banco.py"
        )

    con = sqlite3.connect(CAMINHO_BANCO)
    con.execute("PRAGMA foreign_keys = ON")
    try:
        yield con
        con.commit()
    except Exception:
        con.rollback()   # deu erro no meio? desfaz tudo, não grava pela metade
        raise
    finally:
        con.close()


def consultar(sql: str, parametros: tuple = ()) -> pd.DataFrame:
    """Executa um SELECT e devolve um DataFrame."""
    with conectar() as con:
        return pd.read_sql_query(sql, con, params=parametros)


def executar(sql: str, parametros: tuple = ()) -> int:
    """Executa INSERT/UPDATE/DELETE e devolve o id da linha afetada."""
    with conectar() as con:
        cur = con.execute(sql, parametros)
        return cur.lastrowid


# ==================================================================
# LEITURA — usadas pelo Dashboard e pelos seletores do formulário
# ==================================================================
# @st.cache_data guarda o resultado em memória. Sem isso, o app consultaria
# o banco a cada clique — e no Streamlit são MUITOS cliques.
# ttl=300 = o cache expira em 5 minutos.

@st.cache_data(ttl=300)
def listar_clientes(somente_ativos: bool = True) -> pd.DataFrame:
    sql = "SELECT id, nome, cidade, uf, segmento FROM clientes"
    if somente_ativos:
        sql += " WHERE ativo = 1"
    sql += " ORDER BY nome"
    return consultar(sql)


@st.cache_data(ttl=300)
def listar_produtos(somente_ativos: bool = True) -> pd.DataFrame:
    sql = "SELECT id, nome, categoria, preco_unitario FROM produtos"
    if somente_ativos:
        sql += " WHERE ativo = 1"
    sql += " ORDER BY nome"
    return consultar(sql)


@st.cache_data(ttl=300)
def listar_vendas(
    data_inicio: str | None = None,
    data_fim: str | None = None,
    status: list[str] | None = None,
    canais: list[str] | None = None,
) -> pd.DataFrame:
    """
    Lê a view vw_vendas_completo (já traz nome do cliente e do produto).

    Os filtros são montados dinamicamente: só entra no WHERE o que foi
    informado. Note que os valores NUNCA são concatenados na string SQL —
    vão como parâmetros (?), o que evita SQL injection.
    """
    condicoes, parametros = [], []

    if data_inicio:
        condicoes.append("data_venda >= ?")
        parametros.append(data_inicio)
    if data_fim:
        condicoes.append("data_venda <= ?")
        parametros.append(data_fim)
    if status:
        condicoes.append(f"status IN ({','.join('?' * len(status))})")
        parametros.extend(status)
    if canais:
        condicoes.append(f"canal IN ({','.join('?' * len(canais))})")
        parametros.extend(canais)

    sql = "SELECT * FROM vw_vendas_completo"
    if condicoes:
        sql += " WHERE " + " AND ".join(condicoes)
    sql += " ORDER BY data_venda DESC, id DESC"

    df = consultar(sql, tuple(parametros))
    if not df.empty:
        df["data_venda"] = pd.to_datetime(df["data_venda"])
    return df


@st.cache_data(ttl=300)
def opcoes_filtro() -> dict:
    """Valores distintos de canal e status, para alimentar os filtros da tela."""
    canais = consultar("SELECT DISTINCT canal FROM vendas ORDER BY canal")
    return {
        "canais": canais["canal"].tolist(),
        "status": ["Concluída", "Pendente", "Cancelada"],
    }


@st.cache_data(ttl=300)
def periodo_disponivel() -> tuple:
    """Menor e maior data de venda no banco — define o range do seletor."""
    df = consultar("SELECT MIN(data_venda) AS ini, MAX(data_venda) AS fim FROM vendas")
    if df.empty or df.loc[0, "ini"] is None:
        hoje = pd.Timestamp.today().date()
        return hoje, hoje
    return (
        pd.to_datetime(df.loc[0, "ini"]).date(),
        pd.to_datetime(df.loc[0, "fim"]).date(),
    )


# ==================================================================
# ESCRITA
# ==================================================================
def inserir_venda(
    data_venda: str,
    cliente_id: int,
    produto_id: int,
    quantidade: int,
    preco_unitario: float,
    canal: str,
    status: str,
    observacao: str = "",
) -> int:
    """
    Grava uma venda e devolve o id gerado.

    Não passamos valor_total: é coluna GENERATED, o banco calcula sozinho.
    """
    novo_id = executar(
        """INSERT INTO vendas
           (data_venda, cliente_id, produto_id, quantidade,
            preco_unitario, canal, status, observacao)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        (data_venda, cliente_id, produto_id, quantidade,
         preco_unitario, canal, status, observacao or None),
    )
    limpar_cache()   # sem isso, o dashboard continuaria mostrando o total antigo
    return novo_id


def inserir_cliente(nome: str, email: str, cidade: str, uf: str, segmento: str) -> int:
    novo_id = executar(
        "INSERT INTO clientes (nome, email, cidade, uf, segmento) VALUES (?, ?, ?, ?, ?)",
        (nome, email or None, cidade or None, uf.upper() or None, segmento),
    )
    limpar_cache()
    return novo_id


def inserir_produto(nome: str, categoria: str, preco_unitario: float) -> int:
    novo_id = executar(
        "INSERT INTO produtos (nome, categoria, preco_unitario) VALUES (?, ?, ?)",
        (nome, categoria, preco_unitario),
    )
    limpar_cache()
    return novo_id


def excluir_venda(venda_id: int) -> None:
    executar("DELETE FROM vendas WHERE id = ?", (venda_id,))
    limpar_cache()


def limpar_cache() -> None:
    """Invalida todos os @st.cache_data. Chame após qualquer escrita."""
    st.cache_data.clear()


# ==================================================================
# TESTE RÁPIDO — rode `python database.py` para conferir a conexão
# ==================================================================
if __name__ == "__main__":
    with conectar() as con:
        for tabela in ("clientes", "produtos", "vendas"):
            total = con.execute(f"SELECT COUNT(*) FROM {tabela}").fetchone()[0]
            print(f"{tabela:<10} {total:>5} registros")

    df = consultar("SELECT * FROM vw_vendas_completo LIMIT 3")
    print("\nPrimeiras linhas da view:")
    print(df[["data_venda", "cliente", "produto", "quantidade", "valor_total"]])