import math

from flask import Blueprint, current_app, redirect, render_template, request, session, url_for

from app.auth import is_valid_access_code, login_required


auth_bp = Blueprint("auth", __name__)


@auth_bp.get("/login")
def login_page():
    if session.get("authenticated"):
        return redirect(url_for("dashboard.index"))
    return render_template("login.html")


@auth_bp.post("/login")
def login():
    limiter = current_app.extensions["login_limiter"]
    client = request.remote_addr or "unknown"
    if not limiter.remaining_lock_seconds(client):
        if is_valid_access_code(request.form.get("code", "")):
            limiter.reset(client)
            session.clear()
            session["authenticated"] = True
            return redirect(url_for("dashboard.index"))
        limiter.register_failure(client)
    lock_seconds = limiter.remaining_lock_seconds(client)
    if lock_seconds:
        return render_template("login.html", error="locked", minutes=math.ceil(lock_seconds / 60)), 429
    return render_template("login.html", error="invalid"), 401


@auth_bp.get("/logout")
@login_required
def logout():
    session.clear()
    return redirect(url_for("auth.login_page"))
