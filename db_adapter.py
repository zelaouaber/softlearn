# =========================================================
# ADAPTATEUR BASE DE DONNEES
# SQLite (local) ou PostgreSQL (production)
# =========================================================

import sqlite3
import re
import config


def get_db():
    """
    Retourne une connexion a la base.
    - PostgreSQL si DATABASE_URL est definie (Render)
    - SQLite sinon (dev local)
    """
    if config.USE_POSTGRES:
        import psycopg2
        from psycopg2.extras import RealDictCursor

        conn = psycopg2.connect(
            config.DATABASE_URL,
            cursor_factory=RealDictCursor
        )
        return PostgresWrapper(conn)
    else:
        conn = sqlite3.connect(config.SQLITE_PATH)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        return SqliteWrapper(conn)


# =========================================================
# TRADUCTION SQLITE -> POSTGRESQL
# =========================================================

def _traduire_strftime(query: str) -> str:
    """
    Convertit strftime('%Y-%m', col) -> to_char(col, 'YYYY-MM')
    Gere aussi strftime('%Y-%m', 'now') -> to_char(CURRENT_DATE, 'YYYY-MM')
    """
    def _repl(m):
        fmt = m.group(1)
        col = m.group(2).strip()

        pg_fmt = (fmt
                  .replace('%Y', 'YYYY')
                  .replace('%m', 'MM')
                  .replace('%d', 'DD')
                  .replace('%H', 'HH24')
                  .replace('%M', 'MI')
                  .replace('%S', 'SS'))

        # 'now' -> CURRENT_DATE
        if col.lower().strip("'") == 'now':
            col = 'CURRENT_DATE'

        return f"to_char({col}, '{pg_fmt}')"

    return re.sub(
        r"strftime\(\s*'([^']+)'\s*,\s*([^)]+)\)",
        _repl,
        query,
    )


def _traduire_insert_or(query: str) -> str:
    """
    Convertit :
      INSERT OR REPLACE INTO t (...) VALUES (...)
        -> INSERT INTO t (...) VALUES (...) ON CONFLICT DO UPDATE SET ...  [complexe]

      INSERT OR IGNORE INTO t (...) VALUES (...)
        -> INSERT INTO t (...) VALUES (...) ON CONFLICT DO NOTHING

    Pour OR REPLACE, on transforme en OR IGNORE car dans SoftLearn
    les cas d'usage sont "ne pas dupliquer" (progressions_lecons,
    pretests). L'UPDATE sera fait par une requête séparée si besoin.
    """
    # INSERT OR IGNORE -> ON CONFLICT DO NOTHING
    if re.search(r"INSERT\s+OR\s+IGNORE", query, re.IGNORECASE):
        query = re.sub(
            r"INSERT\s+OR\s+IGNORE\s+INTO",
            "INSERT INTO",
            query,
            flags=re.IGNORECASE,
        )
        # Ajoute ON CONFLICT DO NOTHING si pas déjà présent
        if "ON CONFLICT" not in query.upper():
            query = query.rstrip().rstrip(";") + " ON CONFLICT DO NOTHING"

    # INSERT OR REPLACE -> on le traite plus bas avec ON CONFLICT DO UPDATE
    if re.search(r"INSERT\s+OR\s+REPLACE", query, re.IGNORECASE):
        # On ne peut pas deviner les colonnes update automatiquement ici,
        # donc on transforme en OR IGNORE + on laisse l'appelant gérer
        # le ON CONFLICT DO UPDATE manuellement (voir view_lecon, create_pretest).
        # Solution de secours : ON CONFLICT DO NOTHING (au moins pas de crash)
        query = re.sub(
            r"INSERT\s+OR\s+REPLACE\s+INTO",
            "INSERT INTO",
            query,
            flags=re.IGNORECASE,
        )
        if "ON CONFLICT" not in query.upper():
            query = query.rstrip().rstrip(";") + " ON CONFLICT DO NOTHING"

    return query


def _traduire_placeholders(query: str) -> str:
    """? -> %s"""
    return query.replace("?", "%s")


def _traduire_query(query: str) -> str:
    """Pipeline complet de traduction."""
    query = _traduire_strftime(query)
    query = _traduire_insert_or(query)
    query = _traduire_placeholders(query)
    return query


# =========================================================
# WRAPPER SQLITE
# =========================================================

class SqliteWrapper:
    """Wrapper pour uniformiser sqlite3 avec l'API psycopg2."""

    def __init__(self, conn):
        self.conn = conn

    def execute(self, query, params=None):
        if params:
            return self.conn.execute(query, params)
        return self.conn.execute(query)

    def commit(self):
        self.conn.commit()

    def rollback(self):
        self.conn.rollback()

    def close(self):
        self.conn.close()

    def cursor(self):
        return self.conn.cursor()


# =========================================================
# WRAPPER POSTGRESQL
# =========================================================

class PostgresWrapper:
    """Wrapper pour psycopg2 avec API similaire a sqlite3."""

    def __init__(self, conn):
        self.conn = conn

    def execute(self, query, params=None):
        query_pg = _traduire_query(query)
        cursor = self.conn.cursor()
        if params:
            cursor.execute(query_pg, params)
        else:
            cursor.execute(query_pg)
        return PostgresCursorWrapper(cursor)

    def commit(self):
        self.conn.commit()

    def rollback(self):
        self.conn.rollback()

    def close(self):
        self.conn.close()

    def cursor(self):
        return self.conn.cursor()


class PostgresCursorWrapper:
    """Wrapper pour uniformiser le curseur psycopg2 avec sqlite3."""

    def __init__(self, cursor):
        self.cursor = cursor

    def fetchone(self):
        row = self.cursor.fetchone()
        if row is None:
            return None
        return CaseInsensitiveRow(row)

    def fetchall(self):
        rows = self.cursor.fetchall()
        return [CaseInsensitiveRow(r) for r in rows]

    def __iter__(self):
        for row in self.cursor:
            yield CaseInsensitiveRow(row)

    @property
    def lastrowid(self):
        return getattr(self.cursor, "lastrowid", None)


class CaseInsensitiveRow:
    def __init__(self, row_dict):
        self._data = dict(row_dict)

    def __getitem__(self, key):
        if key in self._data:
            return self._data[key]
        for k, v in self._data.items():
            if k.lower() == key.lower():
                return v
        raise KeyError(key)

    def keys(self):
        return self._data.keys()

    def get(self, key, default=None):
        try:
            return self[key]
        except KeyError:
            return default

    def __contains__(self, key):
        return any(k.lower() == key.lower() for k in self._data)