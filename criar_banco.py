"""
criar_banco.py — cria o banco SQLite do projeto em data/dados.db

Rode uma vez:      python criar_banco.py
Recriar do zero:   python criar_banco.py --recriar
Sem dados falsos:  python criar_banco.py --sem-exemplos
"""

import argparse
import random
import sqlite3
from datetime import date, timedelta
from pathlib import Path

# ------------------------------------------------------------------
# CAMINHOS — relativos ao arquivo .py, não ao terminal
# ------------------------------------------------------------------
RAIZ = Path(__file__).parent
PASTA_DADOS = RAIZ / "data"
CAMINHO_BANCO = PASTA_DADOS / "dados.db"

# ------------------------------------------------------------------
# SCHEMA
# ------------------------------------------------------------------
SCHEMA = """
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS clientes (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    nome        TEXT    NOT NULL,
    email       TEXT    UNIQUE,
    cidade      TEXT,
    uf          TEXT    CHECK (length(uf) = 2),
    segmento    TEXT    NOT NULL DEFAULT 'Varejo',
    ativo       INTEGER NOT NULL DEFAULT 1 CHECK (ativo IN (0, 1)),
    criado_em   TEXT    NOT NULL DEFAULT (datetime('now', 'localtime'))
);

CREATE TABLE IF NOT EXISTS produtos (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    nome            TEXT    NOT NULL,
    categoria       TEXT    NOT NULL,
    preco_unitario  REAL    NOT NULL CHECK (preco_unitario >= 0),
    ativo           INTEGER NOT NULL DEFAULT 1 CHECK (ativo IN (0, 1)),
    criado_em       TEXT    NOT NULL DEFAULT (datetime('now', 'localtime'))
);

CREATE TABLE IF NOT EXISTS vendas (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    data_venda      TEXT    NOT NULL,
    cliente_id      INTEGER NOT NULL,
    produto_id      INTEGER NOT NULL,
    quantidade      INTEGER NOT NULL CHECK (quantidade > 0),
    preco_unitario  REAL    NOT NULL CHECK (preco_unitario >= 0),
    valor_total     REAL    GENERATED ALWAYS AS (quantidade * preco_unitario) STORED,
    canal           TEXT    NOT NULL DEFAULT 'Loja',
    status          TEXT    NOT NULL DEFAULT 'Concluída'
                            CHECK (status IN ('Concluída', 'Pendente', 'Cancelada')),
    observacao      TEXT,
    criado_em       TEXT    NOT NULL DEFAULT (datetime('now', 'localtime')),

    FOREIGN KEY (cliente_id) REFERENCES clientes(id) ON DELETE RESTRICT,
    FOREIGN KEY (produto_id) REFERENCES produtos(id) ON DELETE RESTRICT
);

CREATE INDEX IF NOT EXISTS idx_vendas_data    ON vendas(data_venda);
CREATE INDEX IF NOT EXISTS idx_vendas_cliente ON vendas(cliente_id);
CREATE INDEX IF NOT EXISTS idx_vendas_produto ON vendas(produto_id);

CREATE VIEW IF NOT EXISTS vw_vendas_completo AS
SELECT
    v.id,
    v.data_venda,
    c.nome        AS cliente,
    c.cidade,
    c.uf,
    c.segmento,
    p.nome        AS produto,
    p.categoria,
    v.quantidade,
    v.preco_unitario,
    v.valor_total,
    v.canal,
    v.status
FROM vendas v
JOIN clientes c ON c.id = v.cliente_id
JOIN produtos p ON p.id = v.produto_id;
"""

# ------------------------------------------------------------------
# DADOS DE EXEMPLO
# ------------------------------------------------------------------
CLIENTES = [
    ("Aurora Comércio",        "contato@aurora.com.br",   "Sorocaba",       "SP", "Varejo"),
    ("Nordeste Distribuidora", "vendas@nordestedist.br",  "Recife",         "PE", "Atacado"),
    ("Vale Verde Alimentos",   "compras@valeverde.com",   "Campinas",       "SP", "Indústria"),
    ("Litoral Serviços",       "financeiro@litoral.com",  "Santos",         "SP", "Serviços"),
    ("Central Sul Ltda",       "central@centralsul.com",  "Curitiba",       "PR", "Atacado"),
    ("Horizonte Tech",         "hello@horizonte.tech",    "Belo Horizonte", "MG", "Serviços"),
    ("Praia Grande Market",    "market@praiagrande.com",  "Praia Grande",   "SP", "Varejo"),
    ("Rio Bonito S/A",         "sac@riobonito.com.br",    "Rio de Janeiro", "RJ", "Indústria"),
]

PRODUTOS = [
    ("Notebook Pro 14",        "Informática",  4890.00),
    ("Monitor UltraWide 29",   "Informática",  1750.00),
    ("Teclado Mecânico",       "Periféricos",   429.90),
    ("Mouse Ergonômico",       "Periféricos",   219.90),
    ("Headset Studio",         "Áudio",         899.00),
    ("Cadeira Ergonômica",     "Mobiliário",   1990.00),
    ("Mesa Ajustável",         "Mobiliário",   2450.00),
    ("Webcam 4K",              "Periféricos",   749.00),
    ("Dock Station USB-C",     "Informática",  1180.00),
    ("Licença Software Anual", "Software",     1290.00),
]

CANAIS = ["Loja", "E-commerce", "Representante", "Televendas"]
STATUS = ["Concluída", "Concluída", "Concluída", "Concluída", "Pendente", "Cancelada"]


def popular_exemplos(con: sqlite3.Connection, qtd_vendas: int = 420) -> None:
    """Insere clientes, produtos e vendas espalhadas nos últimos 12 meses."""
    cur = con.cursor()

    cur.executemany(
        "INSERT INTO clientes (nome, email, cidade, uf, segmento) VALUES (?, ?, ?, ?, ?)",
        CLIENTES,
    )
    cur.executemany(
        "INSERT INTO produtos (nome, categoria, preco_unitario) VALUES (?, ?, ?)",
        PRODUTOS,
    )

    hoje = date.today()
    random.seed(42)  # semente fixa: mesmos dados toda vez que recriar

    vendas = []
    for _ in range(qtd_vendas):
        data_venda = (hoje - timedelta(days=random.randint(0, 364))).isoformat()
        cliente_id = random.randint(1, len(CLIENTES))
        produto_id = random.randint(1, len(PRODUTOS))
        preco_base = PRODUTOS[produto_id - 1][2]
        preco = round(preco_base * random.uniform(0.92, 1.08), 2)
        quantidade = random.choices(
            [1, 2, 3, 4, 5, 8, 10], weights=[40, 22, 14, 8, 6, 6, 4]
        )[0]

        vendas.append((
            data_venda, cliente_id, produto_id, quantidade, preco,
            random.choice(CANAIS), random.choice(STATUS),
        ))

    cur.executemany(
        """INSERT INTO vendas
           (data_venda, cliente_id, produto_id, quantidade, preco_unitario, canal, status)
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        vendas,
    )
    con.commit()


# ------------------------------------------------------------------
# EXECUÇÃO
# ------------------------------------------------------------------
def main() -> None:
    parser = argparse.ArgumentParser(description="Cria o banco SQLite do projeto.")
    parser.add_argument("--recriar", action="store_true",
                        help="apaga o banco existente e cria tudo de novo")
    parser.add_argument("--sem-exemplos", action="store_true",
                        help="cria as tabelas vazias, sem dados de teste")
    args = parser.parse_args()

    if sqlite3.sqlite_version_info < (3, 31):
        raise SystemExit(
            f"SQLite {sqlite3.sqlite_version} é antigo demais (preciso de 3.31+). "
            "Atualize o Python para 3.9 ou superior."
        )

    PASTA_DADOS.mkdir(exist_ok=True)

    if args.recriar and CAMINHO_BANCO.exists():
        CAMINHO_BANCO.unlink()
        print("Banco anterior removido.")

    banco_novo = not CAMINHO_BANCO.exists()

    con = sqlite3.connect(CAMINHO_BANCO)
    con.executescript(SCHEMA)

    if banco_novo and not args.sem_exemplos:
        popular_exemplos(con)
        print("Dados de exemplo inseridos.")

    print(f"\nBanco criado em: {CAMINHO_BANCO.resolve()}")
    print(f"SQLite: {sqlite3.sqlite_version}\n")
    for tabela in ("clientes", "produtos", "vendas"):
        total = con.execute(f"SELECT COUNT(*) FROM {tabela}").fetchone()[0]
        print(f"  {tabela:<10} {total:>5} registros")

    faturamento = con.execute(
        "SELECT COALESCE(SUM(valor_total), 0) FROM vendas WHERE status = 'Concluída'"
    ).fetchone()[0]
    formatado = f"{faturamento:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    print(f"\n  Faturamento concluído: R$ {formatado}")

    con.close()


if __name__ == "__main__":
    main()