import sqlite3
from datetime import datetime

import click
from flask import current_app, g

from werkzeug.security import generate_password_hash

import secrets

def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect(
            current_app.config["DATABASE"],
            detect_types=sqlite3.PARSE_DECLTYPES
        )
        g.db.row_factory = sqlite3.Row
    
    return g.db

def close_db(e=None):
    db = g.pop("db", None)

    if db is not None:
        db.close()

def init_db():
    db = get_db()

    with current_app.open_resource("schema.sql") as f:
        db.executescript(f.read().decode("utf-8"))

@click.command("init-db")
def init_db_command():
    """Clear the existing data and create new tables"""
    init_db()
    click.echo("Initialized the database.")

@click.command("create-admin")
def create_admin_command():
    db = get_db()

    password = secrets.token_urlsafe(20)

    db.execute(
        "DELETE FROM user WHERE username = 'admin'"
    )

    db.execute(
        "INSERT INTO user (username, password, is_admin) VALUES (?, ?, 1)",
        ("admin", generate_password_hash(password))
    )
    db.commit()

    click.echo(f"admin password: {password}")

sqlite3.register_converter(
    "timestamp", lambda v: datetime.fromisoformat(v.decode())
)

def init_app(app):
    app.teardown_appcontext(close_db)
    app.cli.add_command(init_db_command)
    app.cli.add_command(create_admin_command)

def get_found_count_for_code_id(id_):
    db = get_db()

    count = db.execute(
        "SELECT COUNT(*) FROM finds WHERE code_id = ?",
        (id_,)
    ).fetchone()[0]

    return count

def calc_points(solve_count, initial=500, minimum=100, decay=10):
    if solve_count == 1: solve_count -= 1 
    return ((minimum - initial) / (decay**2)) * (solve_count**2) + initial