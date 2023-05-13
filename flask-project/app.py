#!/usr/local/bin/python3
# Import the necessary modules
import os
from flask import Flask, render_template, request, redirect, url_for, session, flash
from yelp import findBusiness
from forms import LoginForm, RegisterForm
from flask_login import login_user, logout_user, login_required, current_user
from models import db, loginManager, UserModel
from flask_dance.contrib.github import make_github_blueprint, github
from flask_dance.consumer import oauth_authorized

# Create a new Flask application instance
app = Flask(__name__)
app.secret_key="secret"

#database configuration
DBUSER = 'lhhung'
DBPASS = 'password'
DBHOST = 'db'
DBPORT = '5432'
DBNAME = 'pglogindb'

app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql+psycopg2://{user}:{passwd}@{host}:{port}/{db}'.format(
        user=DBUSER,
        passwd=DBPASS,
        host=DBHOST,
        port=DBPORT,
        db=DBNAME)
#app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///login.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

#initialize the database
db.init_app(app)

#initailize oauth keys
app.config["GITHUB_OAUTH_CLIENT_ID"] = os.environ['GITHUB_OAUTH_CLIENT_ID']
app.config["GITHUB_OAUTH_CLIENT_SECRET"] = os.environ['GITHUB_OAUTH_CLIENT_SECRET']
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

#initialize the login manager
loginManager.init_app(app)

github_bp = make_github_blueprint()
app.register_blueprint(github_bp, url_prefix="/login")


@oauth_authorized.connect
def githubLoggedIn(blueprint, token):
    if not github.authorized:
        return redirect(url_for("github.login"))
    resp = github.get('/user')
    if resp.ok:
        user_info = resp.json()
        email = user_info['email']
        user = UserModel.query.filter_by(email=email).first()
        if user is None:
            flash("You need to register first")
            return redirect(url_for('register'))
        login_user(user)
        flash("You have successfully signed in via GitHub!")
        return redirect(url_for("showBusiness"))
    flash("Failed to sign in with GitHub.")

@app.route("/github")
def loginGithub():
    if not github.authorized or not current_user.is_authenticated:
        return redirect(url_for("github.login"))
    return redirect(url_for("login"))


def addUser(email, password):
    user = UserModel()
    user.setPassword(password)
    user.email=email
    db.session.add(user)
    db.session.commit()

#handler for bad requests
@loginManager.unauthorized_handler
def authHandler():
    form=LoginForm()
    flash('Please login to access this page')
    return render_template('login.html',form=form)

# some setup code because we don't have a registration page or database
@app.before_first_request
def create_table():
    db.create_all()
    user = UserModel.query.filter_by(email = 'lhhung@uw.edu' ).first()
    if user is None:
        addUser("lhhung@uw.edu","qwerty")
    else:
        logout_user()

# Define a route for the root URL ("/") that returns "Hello World"
@app.route('/')
@app.route('/home')
@login_required
def showBusiness():
    if(request.args.get('city')):
        session['city']=request.args.get('city')
    if 'city' in session:
        return render_template('home.html', myData=findBusiness(city=session['city']))
    # This function will be called when someone accesses the root URL
    return render_template('home.html', myData=findBusiness())

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('showBusiness'))
    form=LoginForm()
    if request.method == 'POST':
        if not form.validate_on_submit():
            flash('Please enter a valid email and password')
            return render_template('login.html',form=form)
        user = UserModel.query.filter_by(email = form.email.data ).first()
        if user is None:
            flash('Please enter a valid email')
            return render_template('login.html',form=form)
        if not user.checkPassword(form.password.data):
            flash('Please enter a valid password')
            return render_template('login.html',form=form)
        login_user(user)
        session['email'] = form.email.data
        session['city']='Tacoma'
        return redirect(url_for('showBusiness'))
    # This function will be called when someone accesses the root URL
    return render_template('login.html',form=form)

@app.route('/register', methods=['GET', 'POST'])
def register():
    #redirect back to home
    if current_user.is_authenticated:
        return redirect(url_for('showBusiness'))
    form=RegisterForm()
    if request.method == 'POST':
        if not form.validate_on_submit():
            if form.password.data != form.confirmPassword.data:
                flash('Passwords do not match')
            else:
                flash('Error in registration')
            return render_template('register.html',form=form)
        user = UserModel.query.filter_by(email = form.email.data ).first()
        if user is None:
            if form.password.data == form.confirmPassword.data:
                addUser(form.email.data,form.password.data)
                flash('Registration successful')
                return redirect(url_for('login'))
            else:
                flash('Passwords do not match')
                return render_template('register.html',form=form)
        else:
            flash('User already exists')
            return render_template('register.html',form=form)
    return render_template('register.html',form=form)

@app.route('/logout', methods=['GET', 'POST'])
def logout():
    logout_user()
    session.pop('email', None)
    session.pop('city', None)
    #del github_bp.token
    # This function will be called when someone accesses the root URL
    return redirect(url_for('login'))

# Run the application if this script is being run directly
if __name__ == '__main__':
    # The host is set to '0.0.0.0' to make the app accessible from any IP address.
    # The default port is 5000.
    app.run(host='0.0.0.0', debug='true', port=5000)
