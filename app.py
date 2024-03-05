from flask import Flask, render_template, request, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import IntegrityError

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Change this to a secure secret key
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'  # Use SQLite database
db = SQLAlchemy(app)

class User(db.Model):
    __tablename__ = "user"
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    #admin = db.Column(db.Boolean, nullable=False)
    scores = db.relationship('ShootingSession', backref='user', lazy=True)
    

class ShootingSession(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    distance = db.Column(db.Integer, nullable=False)
    shots_per_target = db.Column(db.Integer, nullable=False)
    target_type = db.Column(db.String(50), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)


# Create the database tables before running the app
with app.app_context():
    db.create_all()




@app.route('/')
def home():
    if 'username' in session:
        return f'Hello, {session["username"]}! <a href="/logout">Logout</a>'
    else:
        return 'You are not logged in. <a href="/login">Login</a> or <a href="/signup">Sign up</a>'

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        user = User.query.filter_by(username=username, password=password).first()

        if user:
            session['username'] = username
            return redirect(url_for('home'))
        else:
            return 'Invalid login credentials. <a href="/login">Try again</a>'

    return render_template('login.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        try:
            new_user = User(username=username, password=password)
            db.session.add(new_user)
            db.session.commit()
            session['username'] = username
            return redirect(url_for('home'))
        except IntegrityError:
            db.session.rollback()
            return 'Username already exists. <a href="/signup">Try a different username</a>'

    return render_template('signup.html')

@app.route('/users')
def user_list():
    # Only allow access to the user list for an admin user (for demonstration purposes)
    if 'username' in session and session['username'] == 'admin':
        users = User.query.all()
        return render_template('user_list.html', users=users)
    else:
        return 'You do not have permission to access this page.'

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('home'))

@app.route('/add_session', methods=['GET', 'POST'])
def add_session():
    if 'username' not in session or session['username'] != 'admin':
        return redirect(url_for('login'))

    if request.method == 'POST':
        #username = request.form['username']
        username = session['username']
        user = User.query.filter_by(username=username).first()

        if user:
            distance = int(request.form['distance'])
            shots_per_target = int(request.form['shots_per_target'])
            target_type = request.form['target_type']

            new_session = ShootingSession(distance=distance, shots_per_target=shots_per_target, target_type=target_type, user=user)
            db.session.add(new_session)
            db.session.commit()
            return redirect(url_for('home'))

    return render_template('add_session.html')

@app.route('/run_session', methods=['GET', 'POST'])
def run_session():
    if 'username' not in session or session['username'] != 'admin':
        return redirect(url_for('login'))

    if request.method == 'POST':
        # Process the form data and run the session
        distance = int(request.form.get('distance'))
        shots_per_target = int(request.form.get('shots_per_target'))
        target_type = request.form.get('target_type')

        # Create a new ShootingSession instance and add it to the database
        session_usernames = request.form.getlist('usernames')
        user = User.query.filter_by(username=session_usernames[0]).first()  # Assuming the first username is valid
        new_session = ShootingSession(distance=distance, shots_per_target=shots_per_target, target_type=target_type, user=user)
        db.session.add(new_session)
        db.session.commit()

        # Retrieve the newly created session ID
        session_id = new_session.id

        return render_template('session_details.html', session_id=session_id, distance=distance, shots_per_target=shots_per_target, target_type=target_type)

    return render_template('run_session.html')


if __name__ == '__main__':
    app.run(debug=True)
