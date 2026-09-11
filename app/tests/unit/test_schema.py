import pytest
from django.db import connection

pytestmark = pytest.mark.django_db


def test_legacy_tables_and_columns_exist():
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'"
        )
        tables = {row[0] for row in cursor.fetchall()}
        assert {
            "airport",
            "airplane",
            "dept",
            "emplo",
            "crew",
            "shift",
            "flight",
            "passengers",
            "buy",
            "ticket",
        } <= tables

        cursor.execute(
            """
            SELECT table_name, column_name
            FROM information_schema.columns
            WHERE table_schema = 'public'
              AND (table_name, column_name) IN (
                ('flight', 'price'), ('ticket', 'seat'), ('emplo', 'deptid')
              )
            """
        )
        assert set(cursor.fetchall()) == {
            ("flight", "price"),
            ("ticket", "seat"),
            ("emplo", "deptid"),
        }
