import os
import sqlite3
import re

from flask import Flask, flash, jsonify, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import datetime

from helpers import login_required, only_not_login

# Configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True
app.config["ENV"] = "development"

# Ensure responses aren't cached
@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

db = sqlite3.connect("data.db", check_same_thread=False)

@app.route("/")
@login_required
def index():

    emps = db.execute("SELECT * FROM emps WHERE manager=?", (session["user_id"],)) #placeholder for emps list
    emps = emps.fetchall()

    return render_template("index.html", emps=emps)

@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            message = "You must provide username and password."
            return render_template("login.html", message_fail = message)

        # Ensure password was submitted
        elif not request.form.get("password"):
            message = "You must provide username and password."
            return render_template("login.html", message_fail = message)

        db = sqlite3.connect("data.db")

        # Query database for username
        username=request.form.get("username")
        rows = db.execute("SELECT * FROM users WHERE username = ?",(username,))

        # Ensure username exists and password is correct
        rows=rows.fetchall()

        if len(rows) != 1 or not check_password_hash(rows[0][2], request.form.get("password")):
            message = "Invalid username and/or password."
            return render_template("login.html", message_fail = message)

        # Remember which user has logged in
        session["user_id"] = rows[0][0]

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")

# Registers a user. If user already logged in, returns user to "/"
@app.route("/register", methods=["GET", "POST"])
@only_not_login

def register():
    if request.method == "GET":
        return render_template("register.html")

    else:
        username = request.form.get("username")
        password = request.form.get("password")
        confirmation = request.form.get("confirmation")

        # Checks if any field is left blank
        if username == "" or password == "" or confirmation == "":
            message = "Please fill out all fields"
            print("yes")
            return render_template("register.html", message_fail = message)

        db = sqlite3.connect("data.db")

        users = db.execute("SELECT username FROM users WHERE username=?", (username,))
        users = users.fetchall()

        # Checks if username is taken

        if users != []:
            message = "Username is taken."
            return render_template("register.html", message_fail = message)
        else:
            if password != confirmation:
                message = "Passwords don't match."
                return render_template("register.html", message_fail = message)
            else:
                hash = generate_password_hash(password)
                db.execute("INSERT INTO users (username, hash) VALUES (?, ?)", (username, hash))
                db.commit()
                message = "You have been registred. You can now log in."
                return render_template("registred.html", message_success = message)

"""
Add a new employee

"""

@app.route("/add", methods=["GET", "POST"])
@login_required
def add():
    if request.method == "GET":
        return render_template("add.html")
    else:
        first = request.form.get("first")
        last = request.form.get("last")

        if first =="" or last=="":
            message = "Please fill out all fields."
            return render_template("add.html", message_fail = message)

        stock_pic = "https://freerangestock.com/sample/120140/business-man-profile-vector.jpg"

        db = sqlite3.connect("data.db")
        db.execute("INSERT INTO emps (first, last, manager, pic) VALUES (?, ?, ?, ?)", (first, last, session["user_id"], stock_pic))
        db.commit()
        return redirect ("/")

@app.route("/profile", methods=["GET", "POST"])
@login_required
def profile():
    if request.method == "GET":
        return redirect("/")
    else:
        first = request.form.get("first")
        last = request.form.get("last")
        ident = request.form.get("id")
        url_img = request.form.get("url_img")
        show = request.form.get("show")

        if show == "all":
            notes = db.execute("SELECT * FROM block_notes WHERE emp_id=? ORDER BY date DESC", (ident,))
            notes = notes.fetchall()
            snips = db.execute("SELECT * FROM snips WHERE emp_id=? ORDER BY date DESC", (ident,))
            snips = snips.fetchall()
            return render_template("profile.html", first_n=first, last_n=last, ident=ident, notes=notes, snips=snips, url=url_img)

        else:
            notes = db.execute("SELECT * FROM block_notes WHERE emp_id=? ORDER BY date DESC LIMIT 3", (ident,))
            notes = notes.fetchall()
            snips = db.execute("SELECT * FROM snips WHERE emp_id=? ORDER BY date DESC LIMIT 10", (ident,))
            snips = snips.fetchall()
            return render_template("profile.html", first_n=first, last_n=last, ident=ident, notes=notes, snips=snips, url=url_img)

@app.route("/addnotes", methods=["GET", "POST"])
@login_required
def addnotes():
    if request.method == "GET":
        return redirect ("/")
    else:
        notes = request.form.get("notes")
        ident = request.form.get("id")
        date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        if notes == "":
            first_n = request.form.get("first")
            last_n = request.form.get("last")
            ident = request.form.get("id")

            notes = db.execute("SELECT * FROM block_notes WHERE emp_id=? ORDER BY date DESC LIMIT 3", (ident,))
            notes = notes.fetchall()
            snips = db.execute("SELECT * FROM snips WHERE emp_id=? ORDER BY date DESC LIMIT 10", (ident,))
            snips = snips.fetchall()

            message = "Write down some notes to submit."
            return render_template("profile.html", message_fail = message, first_n = first_n, last_n=last_n, ident=ident, notes=notes, snips=snips)

        db.execute("INSERT INTO block_notes (emp_id, date, notes, manager) VALUES (?, ?, ?, ?)", (ident, date, notes, session["user_id"]))
        db.commit()

        """
        Creates a list containing each individual word / string seperated by spacebar.

        """
        word = ""
        word_list = []

        for i in range(len(notes)):
            if notes[i] == " ":
                word_list.append(word)
                word = ""
            else:
                word = word + notes[i]
        # Appends the last word that was not appended because last word wasn't followed by a spacebar
        word_list.append(word)

        """
        Creates a dictionary and key:value[] pairs in it based on keys[]

        """
        keys = ["*challenge", "*idea", "*team"]
        string = ""

        keys_dict = {}
        for key in keys:
            keys_dict[key] = []


        initialized = 0

        for word in range(len(word_list)):

            if word_list[word] in keys:
                if initialized == 0:
                    key = word_list[word]
                    initialized += 1
            elif initialized == 1:
                if word_list[word] == "*":
                    keys_dict[key].append(string)
                    string = ""
                    initialized = 0
                else:
                    string = string + " " + word_list[word]

        for key in keys_dict:
            for value in keys_dict[key]:
                db.execute("INSERT INTO snips (emp_id, date, key, snip, manager) VALUES (?, ?, ?, ?, ?)", (ident, date, key, value, session["user_id"]))
                db.commit()

        name=db.execute("SELECT * FROM emps WHERE id=?", (ident,))
        name = name.fetchall()
        first_n = name[0][1]
        last_n = name[0][2]

        notes = db.execute("SELECT * FROM block_notes WHERE emp_id=? ORDER BY date DESC LIMIT 3", (ident,))
        notes = notes.fetchall()
        snips = db.execute("SELECT * FROM snips WHERE emp_id=? ORDER BY date DESC LIMIT 10", (ident,))
        snips = snips.fetchall()

        message = "Notes added."
        return render_template("profile.html", message_success = message, first_n = first_n, last_n=last_n, ident=ident, notes=notes, snips=snips)

@app.route("/editsnip", methods=["GET", "POST"])
@login_required
def editsnip():
    if request.method == "GET":
        first = request.args.get("first")
        print(first)
        last = request.args.get("last")
        emp_id = request.args.get("id")
        image = request.args.get("img")
        snip_id = request.args.get("snip_id")
        snip = db.execute("SELECT * FROM snips WHERE snip_id=?", (snip_id,))
        snip = snip.fetchall()
        snip = snip[0][3]
        return render_template("editsnip.html", snip_id=snip_id, snip=snip, ident=emp_id, first_n=first, last_n=last, url=image)
    else:
        first = request.form.get("first")
        print(first)
        last = request.form.get("last")
        emp_id = request.form.get("id")
        image = request.form.get("img")
        notes = request.form.get("notes")
        snip_id = request.form.get("snip_id")
        db.execute("UPDATE snips SET snip=? WHERE snip_id=?",(notes, snip_id,))
        db.commit()
        snip = db.execute("SELECT * FROM snips WHERE snip_id=?", (snip_id,))
        snip = snip.fetchall()
        return render_template("editsnip.html", snip=notes, snip_id=snip_id, ident=emp_id, first_n=first, last_n=last, url=image )

@app.route("/editnotes", methods=["GET", "POST"])
@login_required
def editnotes():
    if request.method == "GET":
        note_id = request.args.get("note_id")
        first = request.args.get("first")
        last = request.args.get("last")
        emp_id = request.args.get("id")
        image = request.args.get("img")
        notes = db.execute("SELECT * FROM block_notes WHERE note_id=?", (note_id,))
        notes = notes.fetchall()
        notes = notes[0][2]
        return render_template("editnotes.html", note_id=note_id, notes=notes, ident=emp_id, first=first, last=last, url=image)
    else:
        first = request.form.get("first")
        print(first)
        last = request.form.get("last")
        emp_id = request.form.get("id")
        image = request.form.get("img")
        notes = request.form.get("notes")
        note_id = request.form.get("note_id")
        db.execute("UPDATE block_notes SET notes=? WHERE note_id=?",(notes, note_id,))
        db.commit()
        note = db.execute("SELECT * FROM block_notes WHERE note_id=?", (note_id,))
        note = note.fetchall()
        return render_template("editnotes.html", note_id=note_id, notes=notes, ident=emp_id, first=first, last=last, url=image)

@app.route("/deletesnip", methods=["GET"])
@login_required
def deletesnip():
    snip_id = request.args.get("snip_id")
    first = request.args.get("first")
    last = request.args.get("last")
    ident = request.args.get("id")
    image = request.args.get("url_img")
    db.execute("DELETE FROM snips WHERE snip_id=?", (snip_id,))
    db.commit()

    notes = db.execute("SELECT * FROM block_notes WHERE emp_id=? ORDER BY date DESC LIMIT 3", (ident,))
    notes = notes.fetchall()
    snips = db.execute("SELECT * FROM snips WHERE emp_id=? ORDER BY date DESC LIMIT 10", (ident,))
    snips = snips.fetchall()
    return render_template("profile.html", first_n=first, last_n=last, ident=ident, notes=notes, snips=snips, url_img=image)

@app.route("/deletenote", methods=["GET"])
@login_required
def deletenotep():
    note_id = request.args.get("note_id")
    first = request.args.get("first")
    last = request.args.get("last")
    ident = request.args.get("id")
    image = request.args.get("url_img")
    db.execute("DELETE FROM block_notes WHERE note_id=?", (note_id,))
    db.commit()

    notes = db.execute("SELECT * FROM block_notes WHERE emp_id=? ORDER BY date DESC LIMIT 3", (ident,))
    notes = notes.fetchall()
    snips = db.execute("SELECT * FROM snips WHERE emp_id=? ORDER BY date DESC LIMIT 10", (ident,))
    snips = snips.fetchall()
    return render_template("profile.html", first_n=first, last_n=last, ident=ident, notes=notes, snips=snips, url_img=image)

@app.route("/setings", methods=["GET", "POST"])
@login_required
def setings():
    if request.method == "GET":
        return render_template("setings.html")

@app.route("/remove", methods=["GET", "POST"])
@login_required
def remove():
    if request.method == "GET":
        return render_template("remove.html")
    else:
        first = request.form.get("first")
        id = request.form.get("id")

        if first == "" or id == "":
            message = "Please fill out all fields."
            return render_template("remove.html", message_fail=message)

        emp = db.execute("SELECT * FROM emps WHERE id=?", (id,))
        emp = emp.fetchall()
        first_n = emp[0][1]
        last_n = emp[0][2]
        manager = emp[0][3]

        if first != first_n:
            message = "Different employee found. Please make sure ID and first name given is correct."
            return render_template("remove.html", message_fail=message)
        elif int(manager) != int(session["user_id"]):
            message = "Not your employee."
            return render_template("remove.html", message_fail=message)
        else:
            db.execute("DELETE FROM emps WHERE id=?", (id,))
            db.execute("DELETE FROM block_notes WHERE emp_id=?", (id,))
            db.execute("DELETE FROM snips WHERE emp_id=?", (id,))
            db.commit()
            message = "Member removed."
            return render_template("remove.html", message_success=message)

@app.route("/editprofile", methods=["GET", "POST"])
@login_required
def editprofile():
    if request.method == "GET":
        first = request.args.get("first")
        last = request.args.get("last")
        ident = request.args.get("id")
        url_img = request.args.get("img")
        return render_template("editprofile.html", first = first, last = last, ident = ident, url=url_img)
    else:
        first = request.form.get("first")
        last = request.form.get("last")
        url = request.form.get("url")
        ident = request.form.get("ident")

        db.execute("UPDATE emps SET first=?, last=?, pic=? WHERE id=?", (first, last, url, ident,))
        db.commit()

        return render_template("editprofile.html", first = first, last = last, ident = ident, url=url)

@app.route("/howto", methods=["GET"])
@login_required
def howto():
    return render_template("howto.html")

"""
To do:
    -ability to add picture to emloyee
    -how to stop a snip easily? so 100 sentences after a snip dont get put in snips. Maybe "//
    -javascript - min 2 symbols for name and surname when creating an employee
"""


