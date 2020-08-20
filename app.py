import os
import re
import psycopg2

from flask import Flask, flash, jsonify, redirect, render_template, request, session
from flask_session import Session
from flask_mail import Mail, Message

from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

from datetime import timedelta

from random import shuffle

from werkzeug.security import check_password_hash, generate_password_hash


# Configure application and Sessions
app = Flask(__name__)
app.config['SESSION_TYPE'] = 'filesystem'
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=120)
Session(app)


# Configure email for user feedback
app.config['MAIL_SERVER'] = "smtp.mail.yahoo.com"
app.config['MAIL_PORT'] = 465
app.config['MAIL_USE_SSL'] = True
app.config['MAIL_USERNAME'] = os.environ['MAIL_USERNAME']
app.config['MAIL_PASSWORD'] = os.environ['MAIL_PASSWORD']
mail = Mail(app)


# Configure app to use Heroku Postgress Database
DATABASE_URL = os.environ['DATABASE_URL']
conn = psycopg2.connect(DATABASE_URL, sslmode='require')


# Configure db variable to use sqlalchemy engine
engine = create_engine(DATABASE_URL)
db = scoped_session(sessionmaker(bind=engine))


# Home Route
@app.route("/")
def index():

    # Load homepage
    return render_template("home.html", home=True)


# Login Route
@app.route("/login", methods=["GET", "POST"])
def login():

    # Forget user_id
    session.clear()

    # User reached route via POST (as by submitting a form)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):

            flash("Must provide a username!")
            return render_template("login.html")

        # Ensure password was submitted
        elif not request.form.get("password"):

            flash("Must provide a password!")
            return render_template("login.html")

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = :name", {"name": request.form.get("username")}).fetchall()

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0].passhash, request.form.get("password")):

            flash("Invalid username and/or password!")
            return render_template("login.html")

        # Remember which user has logged in
        session["user_id"] = rows[0].id

        # Redirect user to homepage
        flash("Logged In!")
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html", login=True)


# Register Route
@app.route("/register", methods=["GET", "POST"])
def register():

    # Forget user_id
    session.clear()

    # User reached route via POST (as by submitting a form)
    if request.method == "POST":

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = :name", {"name": request.form.get("username")}).fetchall()

        words = ('fuck', 'suck', 'shit', 'kill', 'ass', 'cock', 'dick', 'nigga', 'prick', 'bitch',
                'whore', 'cunt', 'crap', 'foda', 'merda', 'caralho', 'puta', 'cona', 'mangalho',
                'pila', 'tetas', 'fode')

        # Ensure username was submitted
        if not request.form.get("username"):

            flash("Must provide username!")
            return render_template("register.html")

        # Ensure username was not an email
        elif "@" in request.form.get("username") or ".com" in request.form.get("username"):

            flash("Do not use email as username!")
            return render_template("register.html")

        # Ensure username has no spaces
        elif " " in request.form.get("username") or " " in request.form.get("password"):

            flash("No spaces allowed!")
            return render_template("register.html")

        # Ensure no curse words in username
        elif re.compile('|'.join(words),re.IGNORECASE).search(request.form.get("username")):

            flash("No swear words allowed in username!")
            return render_template("register.html")

        # Ensure username does not exist
        elif len(rows) != 0:

            flash("Username already exists!")
            return render_template("register.html")

        # Ensure password was submitted
        elif not request.form.get("password"):

            flash("Must provide password!")
            return render_template("register.html")

        # Ensure password confirmation was submitted
        elif not request.form.get("confirmation"):

            flash("Must provide password confirmation!")
            return render_template("register.html")

        # Ensure both submitted passwords match
        elif request.form.get("password") != request.form.get("confirmation"):

            flash("Passwords don't match!")
            return render_template("register.html")

        # Create new user row in users table
        username = request.form.get("username")
        hashedPass = generate_password_hash(request.form.get("confirmation"))
        db.execute("INSERT INTO users (username, passhash) VALUES (:username, :password)",
                    {"username": username, "password": hashedPass})
        db.commit()

        # Remember which user has logged in
        session["user_id"] = db.execute("SELECT id FROM users WHERE username = :username", {"username": username}).fetchone()[0]

        # Redirect user to homepage
        flash("Registered!")
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("register.html", register=True)


# Leaderboard Route
@app.route("/leaderboard")
def leaderboard():

    # Select list of top 10 users with the most points
    top10 = db.execute("WITH top10 AS (SELECT ROW_NUMBER() OVER(ORDER BY points DESC) leaderboard_position, username, points FROM users) SELECT * FROM top10 LIMIT 10")

    # User reached route via GET (as by clicking a link or via redirect)
    return render_template("leaderboard.html", top10=top10, leaderboard=True)


# Logout Route
@app.route("/logout")
def logout():
    """Log user out"""

    # Forget user_id
    session.clear()

    # Redirect user to homepage form
    flash('Logged Out!')
    return redirect("/")


# Game Route
@app.route("/game", methods=["GET", "POST"])
def game():

    # User reached route via POST (after finishing a game and click button to try again)
    if request.method == "POST":

        # Generate random sequence of 15 card pairs
        cardsequence = [i for i in range(15)] * 2
        shuffle(cardsequence)

        # If user not logged-in, no points are shown
        if session.get("user_id") is None:
            return render_template("game.html", cardsequence=cardsequence, points=0)

        # When a user is logged-in, his points are shown
        else:
            # When user finishes a game, update points in database
            db.execute("UPDATE users SET points = :points WHERE id = :id",
                        {"points": request.form.get("points"), "id": session['user_id']})
            db.commit()

            # Get updated points before reloading game page
            points = db.execute("SELECT points FROM users WHERE id = :id", {"id": session["user_id"]}).fetchone()[0]
            return render_template("game.html", cardsequence=cardsequence, points=points)

    # User reached route via GET (as by clicking a link or via redirect)
    else:

        # Generate random sequence of 15 card pairs
        cardsequence = [i for i in range(15)] * 2
        shuffle(cardsequence)

        # If user not logged-in, no points are shown
        if session.get("user_id") is None:
            return render_template("game.html", cardsequence=cardsequence, points=0)

        # When a user is logged-in, his points are shown
        else:
            points = db.execute("SELECT points FROM users WHERE id = :id", {"id": session["user_id"]}).fetchone()[0]
            return render_template("game.html", cardsequence=cardsequence, points=points)


@app.route("/account", methods=["GET", "POST"])
def account():

    # Select user in database ordered by points position
    current_user = db.execute("WITH leaderboard AS (SELECT ROW_NUMBER() OVER(ORDER BY points DESC) leaderboard_position, username, points, passhash, id FROM users) SELECT * FROM leaderboard WHERE id = :id",
                                {"id": session["user_id"]}).fetchone()
    
    # User reached route via POST (as by submitting change_pass form)
    if request.method == "POST" and request.form['btn'] == 'change_pass':
        
        # Ensure current password was submitted
        if not request.form.get("password"):
            flash("Must provide current password!")
            return render_template("account.html", current_user=current_user, account=True)

        # Ensure new password was submitted
        elif not request.form.get("new_password"):
            flash("Must provide new password!")
            return render_template("account.html", current_user=current_user, account=True)

        # Ensure new password confirmation was submitted
        elif not request.form.get("confirmation"):
            flash("Must provide new password confirmation!")
            return render_template("account.html", current_user=current_user, account=True)

        # Ensure password inserted matches records
        elif not check_password_hash(current_user["passhash"], request.form.get("password")):
            flash("Your current password does not match our records!")
            return render_template("account.html", current_user=current_user, account=True)

        # Ensure both submitted new passwords match
        elif request.form.get("new_password") != request.form.get("confirmation"):
            flash("New passwords don't match!")
            return render_template("account.html", current_user=current_user, account=True)

        # When current password is correct, and new password and confirmation are the same
        # Update password (hash) field in user row
        hashedPass = generate_password_hash(request.form.get("confirmation"))
        db.execute("UPDATE users SET passhash = :passhash WHERE id = :id", {"passhash": hashedPass, "id": session['user_id']})
        db.commit()

        # Redirect user to home page
        flash("Password Updated!")
        return render_template("account.html", current_user=current_user, account=True)
    
    # User reached route via POST (as by submitting del_account form)
    elif request.method == "POST" and request.form['btn'] == 'del_account':

        # Ensure current password was submitted
        if not request.form.get("password"):
            flash("Must provide current password to delete account!")
            return render_template("account.html", current_user=current_user, account=True)
        
        # Ensure correct current password was submitted
        elif not check_password_hash(current_user["passhash"], request.form.get("password")):
            flash("Provide correct password to delete account!")
            return render_template("account.html", current_user=current_user, account=True)

        # When current password is correct, delete user info drom database
        db.execute("DELETE FROM users WHERE id = :id", {"id": session["user_id"]})
        db.commit()

        # Forget user_id
        session.clear()

        # Redirect user to home page
        flash("Account Deleted!")
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("account.html", current_user=current_user, account=True)


@app.route("/feedback", methods=["GET", "POST"])
def feedback():

    # User reached route via POST (as by submitting feedback form)
    if request.method == "POST":

        # Configure and send message as email
        msg = Message(
                subject = 'Peters Games Feedback',
                sender = os.environ['MAIL_USERNAME'],
                recipients = [os.environ['MAIL_USERNAME']],
                body = request.form.get("message"))
        mail.send(msg)

        # Redirect user to homepage form
        flash("Thank's for your feedback!")
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("feedback.html")