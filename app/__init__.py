#===========================================================
# APP NAME HERE
# By YOUR NAME HERE
#===========================================================

from flask import Flask, request, session, render_template, flash, redirect, send_file, make_response
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv
from os import getenv
from io import BytesIO
import html
from app.helpers import *


# Create the app
app = Flask(__name__)


#===========================================================
# App Routes Handlers
#===========================================================

#-----------------------------------------------------------
# Welcome page
#-----------------------------------------------------------
@app.get("/")
def show_welcome():
    return render_template("pages/welcome.jinja")


#-----------------------------------------------------------
# Sign-up page
#-----------------------------------------------------------
@app.get("/user/new")
def show_signup_form():
    return render_template("pages/user_form.jinja")


#-----------------------------------------------------------
# Handle Sign-up
#-----------------------------------------------------------
@app.post("/user")
def process_new_user():
    firstname = request.form.get('firstname', '').strip()
    surname = request.form.get('surname', '').strip()
    username = request.form.get('username', '').strip().lower()
    password = request.form.get('password', '').strip()

    with connect_db() as db:
        sql = "SELECT id FROM users WHERE username=?"
        params = (username,)
        user = db.execute(sql, params).fetchone()

        if user:
            flash(f"Username '{username}' already taken", "Error")
            return redirect("/users/new")

        pass_hash = generate_password_hash(password)

        sql = """
            INSERT INTO users (firstname, surname, username, password_hash)
            VALUES (?, ?, ?, ?)
        """
        params = (firstname, surname, username, pass_hash)
        db.execute(sql, params)

        flash("Account created. Please login.", "Success")
        return redirect("/user/login")


#-----------------------------------------------------------
# Log-in page
#-----------------------------------------------------------
@app.get("/user/login")
def show_login_form():
    return render_template("pages/login_form.jinja")


#-----------------------------------------------------------
# Handle Log-in
#-----------------------------------------------------------
@app.post("/Login")
def process_user_login():
    username = request.form.get('username', '').strip().lower()
    password = request.form.get('password', '').strip()

    with connect_db() as db:
        sql = "SELECT id, firstname, surname, password_hash FROM users WHERE username=?"
        params = (username,)
        user = db.execute(sql, params).fetchone()

        if not user:
            flash(f"Unknown user.", "Error")
            return redirect("/user/login")

        if not check_password_hash(user["password_hash"], password):
            flash(f"Incorrect password", "Error")
            return redirect("/user/login")

        session["logged_in"] = True
        session["user"] = {
            "id": user["id"],
            "username": username,
            "firstname": user["firstname"],
            "surname": user["surname"],
        }

        flash("Login successful", "success")
        return redirect("/")


#-----------------------------------------------------------
# Log-out
#-----------------------------------------------------------
@app.get("/logout")
def user_logout():
    session.clear()
    flash(f"You have been logged out.", "success")
    return redirect("/")


#-----------------------------------------------------------
# Compose message page
#-----------------------------------------------------------
@app.get("/message/new")
@login_required
def message_create():
    return render_template("pages/message_form.jinja")


#-----------------------------------------------------------
# Handle new message
#-----------------------------------------------------------
@app.post("/message")
@login_required
def process_new_message():
    title = request.form.get('title', '').strip()
    text = request.form.get('text', '').strip()

    # User ID is in the session
    user_id = session["user"]["id"]

    with connect_db() as db:
        sql = """
            INSERT INTO messages (user_id, title, text)
            VALUES (?,?,?)
        """
        params = (user_id, title, text)

        db.execute(sql,params)
        return redirect("/message/view")

#-----------------------------------------------------------
# Message list page
#-----------------------------------------------------------
@app.get("/message/view")
def show_all_messages():
    with connect_db() as db:
        sql = """
            SELECT id, user_id, title, text
            FROM messages
        """
        params = ()
        messages = db.execute(sql, params).fetchall()

        return render_template("pages/browse.jinja", messages=messages)


#-----------------------------------------------------------
# Edit message page
#-----------------------------------------------------------
@app.get("/message/edit/<int:id>")
@login_required
def show_edit_form(id):
    with connect_db() as db:
        sql = """
            SELECT id, user_id, title, text
            FROM messages
            Where id=?
        """
        params = (id,)
        message = db.execute(sql, params).fetchone()

        return render_template("pages/message_form_edit.jinja", message=message)


#-----------------------------------------------------------
# Handle edit message
#-----------------------------------------------------------
@app.post("/message/<int:id>")
@login_required
def edit_message(id):
    title = request.form.get('title', '').strip()
    text = request.form.get('text', '').strip()

    title = html.escape(title)
    text = html.escape(text)

    with connect_db() as db:
        sql = """
            UPDATE messages
            SET title=?, text=?
            WHERE id=?
        """
        params = (title, text, id)
        db.execute(sql, params)

        flash("Post updated", "success")
        return redirect("/message/view")


#-----------------------------------------------------------
# Handle delete message
#-----------------------------------------------------------
@app.get("/message/delete/<int:id>")
@login_required
def delete_message(id):
    with connect_db() as db:
        sql = """
            SELECT user_id
            FROM messages
            Where id=?
        """
        params = (id,)
        correct_user = db.execute(sql, params).fetchone()

        if correct_user["user_id"] == session["user"]["id"]:
            with connect_db() as db:
                sql = """
                    DELETE FROM messages
                    WHERE id=?
                """
                params = (id,)
                db.execute(sql, params)

                flash("Post deleted", "success")
                return redirect("/message/view")
        else:
            flash("Incorrect user.", "error")
            return redirect("/message/view")
        


#-----------------------------------------------------------
# Help page - Show some help
#-----------------------------------------------------------
@app.get("/help")
def show_help():

    flash("Flash test message")
    flash("Flash test message with a longer bit of text")
    flash("Success test message", "success")
    flash("Error test message", "error")

    return render_template("pages/help.jinja")


#===========================================================
# Configure the app
#===========================================================
load_dotenv()
app.config.from_prefixed_env()
init_logging(app)
init_text_filters(app)
init_date_filters(app)
init_error_handlers(app)
init_database()
register_commands(app)

