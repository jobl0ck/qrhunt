from flask import (
    Blueprint, g, request, render_template, redirect, url_for, flash, Response
)

from qrhunt.db import get_db, get_found_count_for_code_id, calc_points
from qrhunt.auth import admin_required

from uuid import uuid4

import qrcode

from io import BytesIO

bp = Blueprint("admin", __name__, url_prefix="/admin")

@bp.route("/")
@admin_required
def list_codes():
    if not g.user["is_admin"]:
        return 403

    db = get_db()

    codes = db.execute("SELECT * FROM code").fetchall()

    def gen(x):
        solves = get_found_count_for_code_id(x["id"])
        return solves, int(calc_points(solves))

    points = list(map(gen, codes))

    return render_template("admin/list_codes.html", codes=codes, points=points)

@bp.route("/new_code", methods=("GET", "POST"))
@admin_required
def new_code():
    if request.method == "POST":
        name = request.form["name"]
        desc = request.form["description"]
        db = get_db()
        error = None

        if name == None:
            error = "A name is required."
        
        if error is None:
            try:
                db.execute(
                    "INSERT INTO code (name, description, uuid) VALUES (?, ?, ?)",
                    (name, desc, str(uuid4()))
                )
                db.commit()
            except db.IntegrityError:
                error = "db error"
            else:
                return redirect(url_for("admin.list_codes"))
        
        flash(error)

    return render_template("admin/new_code.html")

@bp.route("/view/<id_>")
@admin_required
def view_code(id_):
    db = get_db()

    code = db.execute(
        "SELECT * FROM code WHERE id = ?",
        (int(id_),)
    ).fetchone()

    if code is None:
        return Response(status=404)

    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4
    )

    url = url_for("hunt.find", uuid=code["uuid"])

    print(url)

    qr.add_data(url)

    qr.make()

    img = qr.make_image(fill_color="black", back_color="white")

    io = BytesIO()

    img.save(io)

    return Response(bytes(io.getbuffer()), mimetype="image/png")