from flask import Flask, render_template, session, redirect, url_for, request
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)

# init db
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
db = SQLAlchemy(app)

app.secret_key = "example"

# User Accounts
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(30), nullable=False)

    def __init__(self, username, password):
        self.username = username
        self.password = password

# TodoTask
class TodoTask(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.ForeignKey(User.id))
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(500), nullable=False)
    user = db.relationship(User, backref="todotasks")

    def __init__(self, user_id, title, description):
        self.user_id = user_id
        self.title = title
        self.description = description

def get_user_by_name(user_name):
    """Return the object filtered by user name"""
    return User.query.filter_by(username=user_name).first()

def is_logged_in():
    """Return True if user's session is active"""
    if session.get("user"):
        return True
    else:
        return False

def is_account_existing(user_name):
    """Return True if such user name exists in the database"""
    user = get_user_by_name(user_name)
    if user:
        return True
    else:
        return False

def has_account(user_name, password):
    """Return True if user name and password match"""
    user = get_user_by_name(user_name)
    if user and user.password == password:
        return True
    else:
        return False

def get_user_id(user_name):
    """Return the id of user name"""
    user = get_user_by_name(user_name)
    if user:
        return user.id
    else:
        return None

def get_task_user_id(task_id):
    """Return the owner's id of the task"""
    task = TodoTask.query.filter_by(id=task_id).first()
    return task.user_id

# homepage
@app.route('/')
def home():
    return render_template("index.html", login=is_logged_in())

# login page
@app.route('/login', methods=["GET", "POST"])
def login_page():
    # redirect to homepage is user is logged id
    if is_logged_in():
        return redirect(url_for("home"))
    else:
        if request.method == "POST":
            # get entered username and password
            user_name = request.form.get("uname")
            password = request.form.get("pwd")

            # init status of error message
            error_message = False

            # check if POST request is invalid
            if not (user_name and password):
                error_message = "Username and password are required!"

            # check if password is correct or if such account exists
            elif not has_account(user_name, password):
                error_message = "Account doesn't exist or password is wrong!"

            # show message if there was an error
            if error_message:
                return render_template("login.html", message=error_message)
            else:
                # start session
                session['user'] = user_name
                return redirect(url_for("home"))

        # in any other cases, show the same login form
        return render_template("login.html", login=is_logged_in())

# create account page
@app.route('/register', methods=["GET", "POST"])
def register():
    # redirect to homepage is user is logged id
    if is_logged_in():
        return redirect(url_for("home"))
    else:
        if request.method == "POST":

            # init status of error message
            error_message = False

            user_name = request.form.get("uname")
            password = request.form.get("pwd")

            # check if POST request is invalid
            if not (user_name and password):
                error_message = "Username and password are required!"

            # check if such login is already used
            elif is_account_existing(user_name):
                error_message = "Account already exists!"

            # redirect to register page if there any any errors
            if error_message:
                return render_template("register.html", message=error_message, login=is_logged_in())
            else:
                # create an account and start session
                user = User(user_name, password)
                db.session.add(user)
                db.session.commit()
                session['user'] = user_name
                return redirect(url_for("home"))
        else:
            # in any other cases redirect to the same page
            return render_template("register.html", login=is_logged_in())

# log out page
@app.route('/logout')
def logout():
    # stop session
    session.pop("user", None)
    return redirect(url_for("home"))


@app.route('/add-task')
def add_task():
    # redirect to homepage if not logged in
    if not is_logged_in():
        return redirect(url_for("home"))
    else:
        user_name = session["user"]
        user_id = get_user_id(user_name)
        return render_template("add-task.html", user_id=user_id, login=is_logged_in())

# add tasks to database
@app.route('/add-task/<int:id>', methods=["GET", "POST"])
def add_task_to_db(id):
    # redirect to home if request method is wrong or user is not logged in
    if not(request.method == "POST" and is_logged_in()):
        return redirect(url_for("home"))
    else:
        user_name_session = session["user"]
        user_id_session = get_user_id(user_name_session)

        # check if user's id and the id in the form are the same
        if id == user_id_session:
            # get data
            title = request.form.get("title")
            description = request.form.get("description")

            # create task and add to database
            task = TodoTask(id, title, description)
            db.session.add(task)
            db.session.commit()
            message = "Task successfully added!"
        else:
            message = "Task could not be added!"

        # render the same page to add more tasks
        return render_template("add-task.html", message=message, user_id=id, login=is_logged_in())

# display a list of tasks
@app.route("/tasks")
def tasks():
    # redirect homepage if not logged in
    if not is_logged_in():
        return redirect(url_for("home"))
    else:
        # get user id
        user_name = session["user"]
        user_id = get_user_id(user_name)

        # get all tasks for the user
        tasks_list = TodoTask.query.filter_by(user_id=user_id).all()

        return render_template("tasks.html", login=is_logged_in(), tasks_list=tasks_list)


# remove task from the database
@app.route("/delete/<int:id>")
def delete_task(id):
    # redirect home if not logged in
    if not is_logged_in():
        return redirect(url_for("home"))
    else:
        user_name = session["user"]
        user_id_from_task = get_task_user_id(id)
        user_id_from_session = get_user_id(user_name)

        # check if the user's id is the same as owner's id of the task
        if user_id_from_task == user_id_from_session:
            # remove the task
            task = TodoTask.query.filter_by(id=id).first()
            db.session.delete(task)
            db.session.commit()

        # show the page with all tasks
        return redirect(url_for("tasks"))
