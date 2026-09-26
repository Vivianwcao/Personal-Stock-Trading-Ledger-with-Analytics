import sqlite3
import psycopg2
from utils import convert_date_string_to_date, convert_utc_string_to_timestamp


# accounts
def migrate_accounts(postgres_conn, sqlite_conn):
    sqlite_cursor = sqlite_conn.cursor()
    postgres_cursor = postgres_conn.cursor()

    sqlite_cursor.execute("""
        SELECT
            id,
            wealth_simple_account_id,
            account_name,
            nickname,
            account_type,
            status,
            balance,
            first_transaction_date,
            institution,
            currency,
            last_successful_sync
        FROM accounts
    """)

    rows = sqlite_cursor.fetchall()

    for row in rows:
        row = dict(row)

        row["first_transaction_date"] = convert_date_string_to_date(
            row["first_transaction_date"]
        )
        row["last_successful_sync"] = convert_utc_string_to_timestamp(
            row["last_successful_sync"]
        )
        postgres_cursor.execute(
            """
            INSERT INTO accounts (
                id,
                wealth_simple_account_id,
                account_name,
                nickname,
                account_type,
                status,
                balance,
                first_transaction_date,
                institution,
                currency,
                last_successful_sync
            )
            VALUES (
                %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s, %s
            )
        """,
            tuple(row.values()),
        )
    postgres_conn.commit()


def migrate_positions(postgres_conn, sqlite_conn):
    cursor = sqlite_conn.cursor()
    rows = cursor.execute("""
        select
            account_id,
            symbol,
            holdings,
            current_price,
            cost_basis,
            trigger,
            last_successful_sync
        from positions
    """)
    # call cursor directly instead of fetchall() - no list in memory first
    with postgres_conn:
        with postgres_conn.cursor() as cur:
            for row in rows:
                row = dict(row)

                row["last_successful_sync"] = convert_utc_string_to_timestamp(
                    row["last_successful_sync"]
                )
                cur.execute(
                    """
                    INSERT INTO positions (
                        account_id,
                        symbol,
                        holdings,
                        current_price,
                        cost_basis,
                        trigger,
                        last_successful_sync
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                """,
                    tuple(row.values()),
                )


def migrate_activities(postgres_conn, sqlite_conn):
    sqlite_cursor = sqlite_conn.cursor()

    rows = sqlite_cursor.execute("""
        select
            id,
            account_id,
            symbol,
            type,
            price,
            units,
            amount,
            fee,
            currency,
            trade_date,
            source   
        from activities;
        """)

    with postgres_conn:
        with postgres_conn.cursor() as cur:
            for row in rows:
                row = dict(row)
                row["trade_date"] = convert_utc_string_to_timestamp(row["trade_date"])
                cur.execute(
                    """
                    insert into activities(
                        id,
                        account_id,
                        symbol,
                        type,
                        price,
                        units,
                        amount,
                        fee,
                        currency,
                        trade_date,
                        source                     
                    ) 
                    values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                    tuple(row.values()),
                )


if __name__ == "__main__":
    sqlite_conn = sqlite3.connect("stocks.db")
    sqlite_conn.row_factory = sqlite3.Row

    postgres_conn = psycopg2.connect("postgresql://postgres:1234@localhost:5432/stocks")

    # migrate_accounts(postgres_conn, sqlite_conn)
    # migrate_positions(postgres_conn, sqlite_conn)
    migrate_activities(postgres_conn, sqlite_conn)

    sqlite_conn.close()
    postgres_conn.close()
