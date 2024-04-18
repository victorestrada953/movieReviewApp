from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, session
from functools import wraps
from bson.objectid import ObjectId
import db_01
import secrets

app = Flask(__name__)
app.secret_key = str(secrets.token_hex(16))

# Set up MongoDB connection
client = db_01.client
db = client['sample_mflix']  # database name
user_collection = db['users']  # the user_collection name
movie_collection = db['movies']
comment_collection = db['comments']

# DB connection verification
if db_01.verify():
    print("You have connected to the database!")

def get_user(email):
    return user_collection.find_one({"email": email})

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user_email = request.form['email']
        user_password = request.form['password']
        user = get_user(user_email)

        if user and user['password'] == user_password:
            session['user'] = user['email']
            return redirect(url_for('dashboard'))
        session['error'] = True
        return redirect(url_for('login'))
    error = session.pop('error', None)
    return render_template('login.html', error=error)

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user' not in session:
            return redirect(url_for('login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/dashboard')
@login_required
def dashboard():
    user_email = session.get('user', None)
    if user_email:
        user_details = get_user(user_email)
        movies = list(db.movies.find().limit(20))  # Limit to 20 movies
        user_comments = list(comment_collection.find({"email": user_email}))
        return render_template('dashboard.html', user=user_details, movies=movies, comments=user_comments)
    else:
        return 'You are not logged in'


@app.route('/logout', methods=['POST'])
def logout():
    session.pop('user', None)
    return redirect(url_for('login'))

@app.route('/') #main landing page
def index():
    # Fetch all user data from MongoDB
    users = list(
        user_collection.find({}, {'name': 1, 'email': 1}))  # retrieves all records with the name and email values only
    return render_template('index.html', users=users)


@app.route('/sign-up', methods=['POST', 'GET'])
def signUp():
    if request.method == 'POST':
        user_name = request.form['name']
        user_email = request.form['email']
        user_password = request.form['password']
        user_obj = {"name": user_name, "email": user_email, "password": user_password}
        if not isuser(user_email):
            user_collection.insert_one(user_obj)
            session['user'] = user_email
            return redirect(url_for('dashboard'))
        else:
            session['error'] = True
        error = session.pop('error', None)
        return render_template('Sign Up.html', error=error)
    else:
        return render_template('Sign Up.html')



@app.route('/error', methods=['GET'])
def error_page():
    if not session.pop('error_triggered', None):  # Check and clear the flag
        # Redirect to home if there was no error triggered (prevent direct access)
        return redirect(url_for('index'))

    return render_template('error.html', error=session['error'])

@app.route('/movie/<movie_id>', methods=['GET', 'POST'])
@login_required
def movie(movie_id):
    try:
        # Convert string ID to ObjectId
        movie_obj_id = ObjectId(movie_id)
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
            "email": session['user'],  # Assuming user_id is stored in session
            "date": datetime.now()
        })
        return redirect(url_for('movie', movie_id=movie_id))

    if not movie:
        return "No movie found", 404

    return render_template('movie.html', movie=movie, comments=comments)

def isuser(email):
    user = user_collection.find_one({'email': email})

    if user:
        return True
    else:
        return False


if __name__ == '__main__':
    app.run(debug=True)
