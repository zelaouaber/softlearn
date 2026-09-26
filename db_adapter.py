# =========================================================
# ADAPTATEUR BASE DE DONNEES
# SQLite (local) ou PostgreSQL (production)
# =========================================================

import sqlite3
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
# WRAPPER SQLITE
# =========================================================

class SqliteWrapper:
    """Wrapper pour uniformiser sqlite3 avec l'API psycopg2."""

    def __init__(self, conn):
        self.conn = conn

    def execute(self, query, params=None):
        # SQLite utilise ? au lieu de %s
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
        self._last_cursor = None

    def execute(self, query, params=None):
        """
        Convertit les '?' de SQLite en '%s' de PostgreSQL.
        Retourne un curseur compatible.
        """
        # Convertit ? -> %s
        query_pg = query.replace("?", "%s")

        # Convertit AUTOINCREMENT -> SERIAL (au cas ou)
        # (ce n'est utile que pour CREATE TABLE, pas pour les requetes)

        cursor = self.conn.cursor()

        if params:
            cursor.execute(query_pg, params)
        else:
            cursor.execute(query_pg)

        self._last_cursor = cursor
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


class CaseInsensitiveRow:
    """
    Permet d'acceder aux colonnes comme avec sqlite3.Row
    (row['id'], row['nom'], etc.)
    """

    def __init__(self, row_dict):
        self._data = dict(row_dict)

    def __getitem__(self, key):
        # Essaie la cle exacte, puis lowercase
        if key in self._data:
            return self._data[key]
        # Fallback : recherche insensible a la casse
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