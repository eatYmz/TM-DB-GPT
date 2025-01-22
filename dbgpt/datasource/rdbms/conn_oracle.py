"""Oracle connector."""
import logging
from typing import Any, Dict, Iterable, List, Optional, Tuple, cast
from urllib.parse import quote
from urllib.parse import quote_plus as urlquote

from sqlalchemy import MetaData, create_engine, text

from .base import RDBMSConnector

logger = logging.getLogger(__name__)


class OracleConnector(RDBMSConnector):
    """Oracle connector."""

    driver = "oracle+cx_oracle"
    db_type = "oracle"
    db_dialect = "oracle"
    default_port = 1521

    def __init__(
        self,
        engine,
        schema: Optional[str] = None,
        metadata: Optional[MetaData] = None,
        ignore_tables: Optional[List[str]] = None,
        include_tables: Optional[List[str]] = None,
        sample_rows_in_table_info: int = 3,
        indexes_in_table_info: bool = False,
        custom_table_info: Optional[Dict[str, str]] = None,
        view_support: bool = True,  # Oracle 默认支持视图
    ):
        """Initialize Oracle connector.
        
        Args:
            engine: SQLAlchemy engine
            schema: Optional schema name (in Oracle this is the user's schema)
            metadata: Optional SQLAlchemy MetaData object
            ignore_tables: Optional list of tables to ignore
            include_tables: Optional list of tables to include
            sample_rows_in_table_info: Number of sample rows to include in table info
            indexes_in_table_info: Whether to include index info
            custom_table_info: Optional custom table info
            view_support: Whether to support views (default True for Oracle)
        """
        super().__init__(
            engine=engine,
            schema=schema,
            metadata=metadata,
            ignore_tables=ignore_tables,
            include_tables=include_tables,
            sample_rows_in_table_info=sample_rows_in_table_info,
            indexes_in_table_info=indexes_in_table_info,
            custom_table_info=custom_table_info,
            view_support=view_support,
        )

    @classmethod
    def from_uri_db(
        cls,
        host: str,
        port: int,
        user: str,
        pwd: str,
        db_name: str,
        engine_args: Optional[dict] = None,
        **kwargs: Any,
    ) -> "OracleConnector":
        """Create a new OracleConnector from host, port, user, pwd, db_name."""
        # Oracle uses service_name in connection string
        db_url: str = (
            f"{cls.driver}://{quote(user)}:{urlquote(pwd)}@{host}:{str(port)}/"
            f"?service_name={db_name}"
        )
        return cast(OracleConnector, cls.from_uri(db_url, engine_args, **kwargs))

    def _sync_tables_from_db(self) -> Iterable[str]:
        """Read table information from database."""
        table_results = self.session.execute(
            text(
                "SELECT table_name FROM all_tables WHERE owner = USER "
                "UNION "
                "SELECT view_name FROM all_views WHERE owner = USER"
            )
        )
        self._all_tables = {row[0] for row in table_results}
        self._metadata.reflect(bind=self._engine)
        return self._all_tables

    def get_fields(self, table_name, db_name=None) -> List[Tuple]:
        """Get column fields about specified table."""
        session = self._db_sessions()
        cursor = session.execute(
            text(
                """
                SELECT column_name, data_type, data_default, nullable,
                       comments
                FROM all_tab_columns c
                LEFT JOIN all_col_comments cc 
                    ON c.table_name = cc.table_name 
                    AND c.column_name = cc.column_name
                WHERE c.table_name = :table_name
                AND c.owner = USER
                """
            ),
            {"table_name": table_name.upper()},  # Oracle table names are uppercase by default
        )
        fields = cursor.fetchall()
        return [(field[0], field[1], field[2], field[3], field[4]) for field in fields]

    def get_show_create_table(self, table_name: str):
        """Return show create table."""
        cursor = self.session.execute(
            text(
                """
                SELECT DBMS_METADATA.GET_DDL('TABLE', :table_name) FROM DUAL
                """
            ),
            {"table_name": table_name.upper()},
        )
        return cursor.scalar()

    def get_users(self):
        """Get user info."""
        session = self._db_sessions()
        cursor = session.execute(
            text(
                """
                SELECT username, created 
                FROM all_users 
                WHERE username = USER
                """
            )
        )
        users = cursor.fetchall()
        return [(user[0], user[1]) for user in users]

    def get_grants(self):
        """Get grants."""
        session = self._db_sessions()
        cursor = session.execute(
            text(
                """
                SELECT privilege, admin_option 
                FROM user_sys_privs
                """
            )
        )
        grants = cursor.fetchall()
        return [(grant[0], grant[1]) for grant in grants]

    def get_collation(self):
        """Get database collation."""
        cursor = self.session.execute(
            text(
                """
                SELECT parameter, value 
                FROM nls_database_parameters 
                WHERE parameter = 'NLS_SORT'
                """
            )
        )
        result = cursor.fetchone()
        return result[1] if result else None

    def get_charset(self):
        """Get database character set."""
        cursor = self.session.execute(
            text(
                """
                SELECT value 
                FROM nls_database_parameters 
                WHERE parameter = 'NLS_CHARACTERSET'
                """
            )
        )
        result = cursor.fetchone()
        return result[0] if result else 'UTF8'

    def get_table_comments(self, db_name=None):
        """Get table comments."""
        cursor = self.session.execute(
            text(
                """
                SELECT table_name, comments 
                FROM all_tab_comments 
                WHERE owner = USER 
                AND table_type = 'TABLE'
                """
            )
        )
        comments = cursor.fetchall()
        return [(comment[0], comment[1]) for comment in comments]

    def get_database_names(self):
        """Get all database names (schemas in Oracle context)."""
        cursor = self.session.execute(
            text(
                """
                SELECT username 
                FROM all_users 
                WHERE username NOT IN ('SYS','SYSTEM','OUTLN','DIP')
                """
            )
        )
        results = cursor.fetchall()
        return [result[0] for result in results]

    def get_current_db_name(self) -> str:
        """Get current database name (schema in Oracle)."""
        return self.session.execute(text("SELECT USER FROM DUAL")).scalar()

    def table_simple_info(self):
        """Get table simple info."""
        _sql = """
            SELECT table_name, 
                   LISTAGG(column_name, ', ') WITHIN GROUP (ORDER BY column_id) AS columns
            FROM all_tab_columns 
            WHERE owner = USER
            GROUP BY table_name
        """
        cursor = self.session.execute(text(_sql))
        results = cursor.fetchall()
        return [(str(result[0]), str(result[1])) for result in results]

    def get_indexes(self, table_name: str):
        """Get table indexes."""
        cursor = self.session.execute(
            text(
                """
                SELECT index_name, column_name
                FROM all_ind_columns 
                WHERE table_name = :table_name 
                AND table_owner = USER
                ORDER BY index_name, column_position
                """
            ),
            {"table_name": table_name.upper()}
        )
        indexes = cursor.fetchall()
        return [(index[0], index[1]) for index in indexes]

    def get_table_comment(self, table_name: str) -> Dict:
        """Get table comments.

        Args:
            table_name (str): table name
        Returns:
            comment: Dict, which contains text: Optional[str], eg:["text": "comment"]
        """
        cursor = self.session.execute(
            text(
                """
                SELECT comments
                FROM all_tab_comments
                WHERE table_name = :table_name
                AND owner = USER
                AND table_type = 'TABLE'
                """
            ),
            {"table_name": table_name.upper()}
        )
        result = cursor.fetchone()
        return {"text": result[0] if result else None}

    def get_column_comments(self, db_name: str, table_name: str):
        """Return column comments."""
        cursor = self.session.execute(
            text(
                """
                SELECT column_name, comments
                FROM all_col_comments
                WHERE table_name = :table_name
                AND owner = USER
                """
            ),
            {"table_name": table_name.upper()}
        )
        column_comments = cursor.fetchall()
        return [(comment[0], comment[1]) for comment in column_comments]
