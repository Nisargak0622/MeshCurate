import os
import re
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import (
    LoginManager, login_user, logout_user, login_required, current_user
)
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv

load_dotenv()

from models import db, User, SavedPost, CATEGORIES
from ai_classifier_v3 import classify_post

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-secret-change-this")
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///savedvault.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db.init_app(app)

login_manager = LoginManager(app)
login_manager.login_view = "login"


@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))


def detect_platform(url: str) -> str:
    if "instagram.com" in url:
        return "instagram"
    if "facebook.com" in url or "fb.watch" in url:
        return "facebook"
    return "other"


# ---------------- Auth routes ----------------

@app.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        if not username or not password:
            flash("Username and password are required.", "error")
            return redirect(url_for("register"))

        if User.query.filter_by(username=username).first():
            flash("That username is already taken.", "error")
            return redirect(url_for("register"))

        user = User(username=username, password_hash=generate_password_hash(password))
        db.session.add(user)
        db.session.commit()

        login_user(user)
        flash("Account created! Welcome to MeshCurate.", "success")
        return redirect(url_for("dashboard"))

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            return redirect(url_for("dashboard"))

        flash("Invalid username or password.", "error")
        return redirect(url_for("login"))

    return render_template("login.html")


@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("login"))


# ---------------- Main app routes ----------------

@app.route("/")
@login_required
def dashboard():
    selected_category = request.args.get("category", "All")

    query = SavedPost.query.filter_by(user_id=current_user.id)
    if selected_category != "All":
        query = query.filter_by(category=selected_category)

    posts = query.order_by(SavedPost.created_at.desc()).all()

    return render_template(
        "dashboard.html",
        posts=posts,
        categories=["All"] + CATEGORIES,
        selected_category=selected_category,
    )


@app.route("/add", methods=["GET", "POST"])
@login_required
def add_post():
    if request.method == "POST":
        url = request.form.get("url", "").strip()
        caption = request.form.get("caption", "").strip()
        note = request.form.get("note", "").strip()
        manual_category = request.form.get("category", "").strip()

        if not url:
            flash("Please paste a post/reel link.", "error")
            return redirect(url_for("add_post"))

        platform = detect_platform(url)

        # Use manual category if the user picked one, otherwise let AI look
        # at the actual thumbnail image (and caption, if given) to decide
        if manual_category and manual_category != "Auto":
            category = manual_category
        else:
            category = classify_post(url, caption)

        post = SavedPost(
            user_id=current_user.id,
            url=url,
            platform=platform,
            caption=caption,
            category=category,
            note=note,
        )
        db.session.add(post)
        db.session.commit()

        flash(f"Saved! Categorized as '{category}'.", "success")
        return redirect(url_for("dashboard"))

    return render_template("add_post.html", categories=CATEGORIES)


@app.route("/delete/<int:post_id>", methods=["POST"])
@login_required
def delete_post(post_id):
    post = db.session.get(SavedPost, post_id)
    if post and post.user_id == current_user.id:
        db.session.delete(post)
        db.session.commit()
        flash("Post removed.", "success")
    return redirect(url_for("dashboard"))


@app.route("/favorite/<int:post_id>", methods=["POST"])
@login_required
def toggle_favorite(post_id):
    post = db.session.get(SavedPost, post_id)
    if post and post.user_id == current_user.id:
        post.is_favorite = not post.is_favorite
        db.session.commit()
    return redirect(url_for("dashboard"))


with app.app_context():
    db.create_all()

if __name__ == "__main__":
    # Local development only. In production, gunicorn imports `app`
    # directly and this block never runs.
    port = int(os.environ.get("PORT", 5000))
    debug_mode = os.environ.get("FLASK_DEBUG", "true").lower() == "true"
    app.run(host="0.0.0.0", port=port, debug=debug_mode)
