"""CLI: python -m app.admin_cli seed-admin --email EMAIL --password PASSWORD"""

import argparse
import sys

from app.auth import hash_password
from app.db_util import ensure_schema_at_startup, get_connection


def seed_admin(email: str, password: str) -> None:
    ensure_schema_at_startup()
    ph = hash_password(password)
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO users (email, password_hash, role)
                VALUES (%s, %s, 'admin')
                ON CONFLICT (email) DO UPDATE
                    SET password_hash = EXCLUDED.password_hash,
                        role = 'admin',
                        deleted_at = NULL
                RETURNING id
                """,
                (email, ph),
            )
            user_id = cur.fetchone()[0]
        conn.commit()
    print(f"Admin seeded: id={user_id} email={email}", flush=True)


def main() -> None:
    parser = argparse.ArgumentParser(description="mjc-chatbot admin CLI")
    sub = parser.add_subparsers(dest="command")

    seed = sub.add_parser("seed-admin", help="Create or reset the first admin account")
    seed.add_argument("--email", required=True)
    seed.add_argument("--password", required=True)

    args = parser.parse_args()
    if args.command == "seed-admin":
        seed_admin(args.email, args.password)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr, flush=True)
        sys.exit(1)
