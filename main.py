from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, session
from functools import wraps
from bson.objectid import ObjectId
import db_01  # Custom module for database setup
import secrets

app = Flask(__name__)
app.secret_key = str(secrets.token_hex(16))  # Generates a random secret key for session management

# Set up MongoDB connection using a custom module
client = db_01.client
db = client['sample_mflix']  # Specifies the MongoDB database name
user_collection = db['users']  # Specifies the MongoDB collection for users
movie_collection = db['movies']  # Specifies the MongoDB collection for movies
comment_collection = db['comments']  # Specifies the MongoDB collection for comments

# DB connection verification
if db_01.verify():  # Verifies connection to MongoDB
    print("You have connected to the database!")

def get_user(email):
    """ Retrieve a user document/object by email from the users collection. """
    return user_collection.find_one({"email": email}) # Returns user document/object as a dictionary

@app.route('/login', methods=['GET', 'POST'])
def login():
    """ Handle user login requests. Authenticate against MongoDB users collection. """
    if request.method == 'POST':
        user_email = request.form['email']
        user_password = request.form['password']
        user = get_user(user_email)

        if user and user['password'] == user_password:
            session['user'] = user['email']  # Store user email in session if authenticated
            next_url = session.pop('next', None)  # Get and remove 'next' from session
            if next_url:
                return redirect(next_url)
            return redirect(url_for('dashboard'))
        session['error'] = True  # Set error flag in session if authentication fails
        return redirect(url_for('login'))
    error = session.pop('error', None)  # Retrieve and clear any authentication error
    return render_template('login.html', error=error)

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user' not in session:
            session['next'] = request.url  # Store the intended URL
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function


@app.route('/dashboard')
@login_required
def dashboard():
    """ Display the user's dashboard, showing movies and their own comments. """
    user_email = session.get('user', None)
    if user_email:
        user_details = get_user(user_email)
        movies = list(movie_collection.find().limit(20))  # Fetch up to 20 movies from the database
        user_comments = list(comment_collection.find({"email": user_email}))  # Fetch comments made by the user
        return render_template('dashboard.html', user=user_details, movies=movies, comments=user_comments)
    else:
        return 'You are not logged in'

@app.route('/logout', methods=['POST'])
def logout():
    """ Log out the user by clearing their session. """
    session.pop('user', None)
    return redirect(url_for('login'))

@app.route('/')  # Main landing page
def index():
    """ Show a page with all users listed (for demonstration purposes). """
    users = list(user_collection.find({}, {'name': 1, 'email': 1}))  # Retrieve all users with name and email only
    return render_template('index.html', users=users)

@app.route('/sign-up', methods=['POST', 'GET'])
def signUp():
    """ Handle user registration. """
    if request.method == 'POST':
        user_name = request.form['name']
        user_email = request.form['email']
        user_password = request.form['password']
        user_obj = {"name": user_name, "email": user_email, "password": user_password}
        if not isuser(user_email):
            user_collection.insert_one(user_obj)  # Insert new user into MongoDB
            session['user'] = user_email  # Automatically log in the new user
            return redirect(url_for('dashboard'))
        else:
            session['error'] = True  # Set error flag if user already exists
        error = session.pop('error', None)
        return render_template('Sign Up.html', error=error)
    else:
        return render_template('Sign Up.html')

@app.route('/error', methods=['GET'])
def error_page():
    """ Display an error page if an error was triggered. """
    if not session.pop('error_triggered', None):  # Check and clear the error flag
        return redirect(url_for('index'))
    return render_template('error.html', error=session['error'])

@app.route('/movie/<movie_id>', methods=['GET', 'POST'])
@login_required
def movie(movie_id):
    """ Display movie details and handle posting of comments. """
    try:
        movie_obj_id = ObjectId(movie_id)  # Convert string ID to ObjectId
    except:
        return "Invalid movie ID", 404  # Handle error if ID is not a valid ObjectId

    movie = movie_collection.find_one({"_id": movie_obj_id})
    comments = list(comment_collection.find({"movie_id": movie_obj_id}))

    if request.method == 'POST':
        comment_text = request.form['comment']
        comment_collection.insert_one({
            "text": comment_text,
            "movie_id": movie_obj_id,
            "name": get_user(session['user'])['name'],
            "email": session['user'],
            "date": datetime.now()
        })
        return redirect(url_for('movie', movie_id=movie_id))

    if not movie:
        return "No movie found", 404

    return render_template('movie.html', movie=movie, comments=comments)

def isuser(email):
    """ Check if a user exists in the database by email. """
    return bool(user_collection.find_one({'email': email}))

if __name__ == '__main__':
    app.run(debug=True)
