import os
import re
import psycopg2

from psycopg2.extras import DictCursor

from flask import Flask, flash, jsonify, redirect, render_template, request, session
from flask_session import Session
from flask_mail import Mail, Message

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
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_ON_TIME_PASSWORD')
mail = Mail(app)


# Configure app to use Postgress Database
DATABASE_URL = os.environ.get('DATABASE_URL')
try:
    conn = psycopg2.connect(DATABASE_URL, sslmode='require')
    print("Connection to DB successful")
except Exception as e:
    print(f"Connection to DB failed: {e}")

# Define DB connection Singleton
db_connection = None
def get_db_connection():
    global db_connection
    if db_connection is None or db_connection.closed:
        db_connection = psycopg2.connect(DATABASE_URL, sslmode='require')
    return db_connection

# Executes a read operation (SELECT) query and returns fetched results
def execute_query(sql, params=None):
    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=DictCursor)
        cursor.execute(sql, params or ())
        results = cursor.fetchall()
        cursor.close()
        return results
    except Exception as e:
        print(f"Database error: {e}")

# Executes a write operation (INSERT, UPDATE, DELETE) query and commits the transaction
def execute_write_query(sql, params=None):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(sql, params or ())
        conn.commit()
        cursor.close()
    except Exception as e:
        print(f"Database error: {e}")


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
        rows = execute_query("SELECT * FROM users WHERE username = %s LIMIT 1;", [request.form.get("username")])

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]['passhash'], request.form.get("password")):

            flash("Invalid username and/or password!")
            return render_template("login.html")

        # Remember which user has logged in
        session["user_id"] = rows[0]['id']

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
        rows = execute_query("SELECT * FROM users WHERE username = %s;", [request.form.get("username")])

        # Fetch all curse words from database
        cursewords = execute_query("SELECT word FROM cursewords;")
        words = tuple(map(lambda word: word[0], cursewords))

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
        execute_write_query("INSERT INTO users (username, passhash) VALUES (%s, %s);", [username, hashedPass])

        # Remember which user has logged in
        session["user_id"] = execute_query("SELECT id FROM users WHERE username = %s LIMIT 1;", [username])[0]['id']

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
    top10 = execute_query("WITH top10 AS (SELECT ROW_NUMBER() OVER(ORDER BY points DESC) leaderboard_position, username, points FROM users) SELECT * FROM top10 LIMIT 10")

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
            execute_write_query("UPDATE users SET points = %s WHERE id = %s", [request.form.get("points"), session['user_id']])

            # Get updated points before reloading game page
            points = execute_query("SELECT points FROM users WHERE id = %s LIMIT 1;", [session["user_id"]])[0]['points']
            return render_template("game.html", cardsequence=cardsequence, points=points)

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        print('User reached route via GET (as by clicking a link or via redirect)')
        # Generate random sequence of 15 card pairs
        cardsequence = [i for i in range(15)] * 2
        shuffle(cardsequence)

        # If user not logged-in, no points are shown
        if session.get("user_id") is None:
            return render_template("game.html", cardsequence=cardsequence, points=0)

        # When a user is logged-in, his points are shown
        else:
            points = execute_query("SELECT points FROM users WHERE id = %s LIMIT 1;", [session["user_id"]])[0]['points']
            return render_template("game.html", cardsequence=cardsequence, points=points)


@app.route("/account", methods=["GET", "POST"])
def account():

    # Select user in database ordered by points position
    current_user = execute_query("WITH leaderboard AS (SELECT ROW_NUMBER() OVER(ORDER BY points DESC) leaderboard_position, username, points, passhash, id FROM users) SELECT * FROM leaderboard WHERE id = %s LIMIT 1;", [session["user_id"]])[0]
    
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
        execute_write_query("UPDATE users SET passhash = %s WHERE id = %s;", [hashedPass, session['user_id']])

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
        execute_write_query("DELETE FROM users WHERE id = %s LIMIT 1;", [session["user_id"]])

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

        try:
            msg = Message(
                        subject = 'Peters Games Feedback',
                        sender = os.environ.get('MAIL_USERNAME'),
                        recipients = [os.environ.get('MAIL_USERNAME')],
                )
            msg.body = request.form.get("message")
            mail.send(msg)

            flash("Thank's for your feedback!")

        except Exception as e:
            flash(f"An error occurred while sending your feedback: {e}")
            # Optionally log the error for debugging
            app.logger.error(f"Failed to send feedback email: {e}")

            # Redirect user to homepage form
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("feedback.html")