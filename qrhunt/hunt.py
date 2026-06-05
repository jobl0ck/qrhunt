from flask import (
    Blueprint, g, Response, render_template, flash
)

from qrhunt.db import get_db, get_found_count_for_code_id, calc_points

bp = Blueprint("hunt", __name__)

@bp.route("/hunt/<uuid>")
def find(uuid):
    db = get_db()

    code = db.execute(
        "SELECT * FROM code WHERE uuid = ?",
        (uuid, )
    ).fetchone()

    if code is None:
        return Response(status=404)

    already_found = db.execute(
        "SELECT * FROM finds WHERE code_id = ? AND user_id = ?",
        (code["id"], g.user["id"])
    ).fetchone() is not None
    
    if g.user is not None and not g.user["is_admin"] and not already_found:
        db.execute(
            "INSERT INTO finds (code_id, user_id) VALUES (?, ?)",
            (code["id"], g.user["id"])
        )
        db.commit()
    
    if already_found:
        flash("You have already found this code.")
    
    return render_template("hunt/find.html", code=code)

@bp.route("/leaderboard")
def leaderboard():

    db = get_db()

    users = db.execute("SELECT * FROM user WHERE is_admin = 0").fetchall()

    data = []

    for user in users:
        solved = db.execute("SELECT code_id FROM finds WHERE user_id = ?", (user["id"],))

        points = 0

        for code in solved:
            points += calc_points(get_found_count_for_code_id(code["code_id"]))
    
        data.append({
            "name": user["username"],
            "points": int(points),
            "me": user["id"] == g.user["id"]
        })
    
    data.sort(key=lambda x: x["points"], reverse=True)

    return render_template("hunt/leaderboard.html", data=data)