import sqlite3
import os
from flask import Flask, redirect, url_for, render_template, request, abort
import db as database


def create_app(conn: sqlite3.Connection) -> Flask:
    app = Flask(__name__)
    app.config["DB_CONN"] = conn

    @app.route("/")
    def index():
        return redirect(url_for("books"))

    @app.route("/books")
    def books():
        conn = app.config["DB_CONN"]
        all_books = database.get_all_books(conn)
        return render_template("books.html", books=all_books)

    @app.route("/books/<int:book_id>")
    def book_detail(book_id: int):
        conn = app.config["DB_CONN"]
        book = database.get_book(conn, book_id)
        if book is None:
            abort(404)
        characters = database.get_characters(conn, book_id)
        return render_template("book.html", book=book, characters=characters)

    @app.route("/books/<int:book_id>/characters/<path:name>")
    def character_sentences(book_id: int, name: str):
        conn = app.config["DB_CONN"]
        book = database.get_book(conn, book_id)
        if book is None:
            abort(404)
        role = request.args.get("role") or None
        page = max(1, int(request.args.get("page", 1)))
        per_page = 20
        results = database.get_sentences_for_character(
            conn, book_id, name, role, page, per_page
        )
        all_roles = database.get_roles_for_character(conn, book_id, name)
        total_pages = max(1, (results["total"] + per_page - 1) // per_page)
        return render_template(
            "character.html",
            book=book,
            name=name,
            sentences=results["sentences"],
            total=results["total"],
            page=page,
            total_pages=total_pages,
            role=role,
            all_roles=all_roles,
        )

    @app.route("/search")
    def search():
        conn = app.config["DB_CONN"]
        q = request.args.get("q", "").strip()
        book_id_str = request.args.get("book_id", "")
        role = request.args.get("role") or None
        page = max(1, int(request.args.get("page", 1)))
        per_page = 20
        book_id = int(book_id_str) if book_id_str.isdigit() else None

        results = {"total": 0, "sentences": []}
        if q:
            results = database.search_character(conn, q, book_id, role, page, per_page)

        all_books = database.get_all_books(conn)
        total_pages = max(1, (results["total"] + per_page - 1) // per_page)
        return render_template(
            "search.html",
            q=q,
            book_id=book_id,
            role=role,
            sentences=results["sentences"],
            total=results["total"],
            page=page,
            total_pages=total_pages,
            all_books=all_books,
        )

    @app.route("/stats")
    def stats():
        conn = app.config["DB_CONN"]
        all_books = database.get_all_books(conn)
        book_id_str = request.args.get("book_id", "")
        book_id = int(book_id_str) if book_id_str.isdigit() else (all_books[0]["id"] if all_books else None)
        book = database.get_book(conn, book_id) if book_id else None
        char_stats = database.get_stats_for_book(conn, book_id) if book_id else []
        return render_template(
            "stats.html",
            all_books=all_books,
            book=book,
            book_id=book_id,
            char_stats=char_stats,
        )

    @app.context_processor
    def inject_sidebar():
        return {"sidebar_books": database.get_all_books(app.config["DB_CONN"])}

    return app


if __name__ == "__main__":
    json_path = "dataset.json"
    db_path = "dataset.db"

    if not os.path.exists(db_path):
        print(f"Inizializzazione database da {json_path}...")
        conn = database.init_db(db_path)
        database.import_json(conn, json_path)
        print("Database creato.")
    else:
        conn = database.init_db(db_path)

    app = create_app(conn)
    app.run(debug=True, port=5000)
