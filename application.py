from flask import Flask, render_template, request, redirect, session, flash
from werkzeug.security import check_password_hash, generate_password_hash
from functools import wraps
from tempfile import mkdtemp
from flask_session import Session
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from cs50 import SQL

app = Flask(__name__)

app.config["TEMPLATES_AUTO_RELOAD"] = True

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

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///movie.db")

def login_required(f):
    """
    Decorate routes to require login.

    http://flask.pocoo.org/docs/1.0/patterns/viewdecorators/
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/login")
        return f(*args, **kwargs)
    return decorated_function

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":

        if not request.form.get("username") or not request.form.get("password2") or not request.form.get("password3"):
            return render_template("register.html", message="Please type in username or password!")

        elif request.form.get("password2") != request.form.get("password3"):
            return render_template("register.html", message="passwords do not match!")

        rows = db.execute("INSERT INTO users(username, hash) VALUES (:username, :password)",
                        username = request.form.get("username"), password = generate_password_hash(request.form.get("password2")))
        if rows is None:
            return("Registration error", 403)

        session["user_id"] = rows
        return redirect("/login")

    else:
        return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        if request.method == "POST":
            username = request.form.get("username")
            password = request.form.get("password")

            if not username or not password:
                return render_template("login.html", message="Please type in username or password!")

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = :username",
                          username=request.form.get("username"))

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            return render_template("login.html", message="Invalid username or password!")


        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


@app.route("/rate", methods=["GET", "POST"])
@login_required
def rate():
    if request.method =="POST":
        title = request.form.get("title")
        category = request.form.get("wood")
        types = request.form.get("m_type")
        genre = request.form.get("genre")
        ratings = (request.form.get("rating"))
        comment = request.form.get("comments")

        if not title or not comment or not category or not types or not genre or not ratings:
            return render_template("rate.html", message="All fields must be filled!")

        rows = db.execute("""INSERT INTO ratings(user_id, title, category, type, genre, rating, comment)
            VALUES (:user_id, :title, :category, :types, :genre, :rating, :comment)""",
                        user_id = session["user_id"],
                        title = title,
                        category = category,
                        types = types,
                        genre = genre,
                        rating = ratings,
                        comment = comment)
        flash("You have rated a movie!")
        return redirect("/rated")

    else:
        return render_template("rate.html")

@app.route("/rated")
@login_required
def rated():

    historys = db.execute("""
        SELECT *
        FROM ratings
        ORDER BY title
        """)

    return render_template("rated.html", historys=historys)

@app.route("/logout")
@login_required
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")


@app.route("/dashboard")
@login_required
def dashboard():
    historys = db.execute("""
        SELECT *
        FROM ratings
        WHERE user_id=:id
        ORDER BY title""", id=session["user_id"])

    return render_template("rated.html", historys=historys)



def errorhandler(e):
    """Handle error"""
    if not isinstance(e, HTTPException):
        e = InternalServerError()
    return(e.name, e.code)


# Listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)
