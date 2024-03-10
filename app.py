from flask import Flask, render_template, request, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import IntegrityError

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Change this to a secure secret key
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'  # Use SQLite database
#app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///instance/site.db'

db = SQLAlchemy(app)

class User(db.Model):
    __tablename__ = "user"
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    #admin = db.Column(db.Boolean, nullable=False)
    #scores = db.relationship('Session', backref='user', lazy=True)

class Format(db.Model):
    __tablename__ = "format"
    id = db.Column(db.Integer, primary_key=True)
    shots_per_target = db.Column(db.Integer, nullable=False)
    target_type = db.Column(db.String(50), nullable=False)
    distance = db.Column(db.Integer, nullable=False)
    
class Session(db.Model):
    __tablename__ = "session"
    id = db.Column(db.Integer, primary_key=True) 
    description = db.Column(db.String(100), nullable=True)
    date = db.Column(db.String(100), nullable=True) # CHANGE TO GET ON CREATION

class Score(db.Model):
    __tablename__ = "score"
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.Integer, db.ForeignKey('session.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    format_id = db.Column(db.Integer, db.ForeignKey('format.id'), nullable=False)

class Shot(db.Model):
    __tablename__ = "shots"
    id = db.Column(db.Integer, primary_key=True)
    score_id = db.Column(db.Integer, db.ForeignKey('score.id'), nullable=False)
    shot_score = db.Column(db.Integer, primary_key=True)


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
        username = session['username']
        user = User.query.filter_by(username=username).first()

        if user:
            # Getting data from add_session.html
            distance = int(request.form['distance'])
            shots_per_target = int(request.form['shots_per_target'])
            target_type = request.form['target_type']
            description = request.form['description']
            usernames = request.form.getlist('usernames')
            # TO DO: GET DATE TIME ADD TO SESSION 
            # TO DO: FORMAT CREATES NEW FORMAT ENTRY EVERY TIME, SIMPLIFY

            # Adding data to respective tables
            new_session = Session(description=description)
            new_format = Format(target_type=target_type, shots_per_target=shots_per_target, distance=distance) 
            
            db.session.add(new_session)
            db.session.add(new_format)
            db.session.commit()

            # Store session details in the Flask session for use in run_session
            session['session_id'] = new_session.id
            session['distance'] = distance
            session['shots_per_target'] = shots_per_target
            session['target_type'] = target_type
            session['usernames'] = usernames

            print(usernames)

            return redirect(url_for('run_session'))

    return render_template('add_session.html')

@app.route('/run_session', methods=['GET', 'POST'])
def run_session():
    if 'username' not in session or session['username'] != 'admin':
        return redirect(url_for('login'))

    # Retrieve session details from the Flask session
    session_id = session.get('session_id')
    distance = session.get('distance')
    shots_per_target = session.get('shots_per_target')
    target_type = session.get('target_type')
    usernames = session.get('usernames')

    if not all([session_id, distance, shots_per_target, target_type, usernames]):
        return redirect(url_for('add_session'))
    

    # For each user: display: 
    # Input for each shot, which appears (shots_per_target) number of times 
    

    # Clear the session details to avoid reusing them
    session.pop('session_id', None)
    session.pop('distance', None)
    session.pop('shots_per_target', None)
    session.pop('target_type', None)
    session.pop('usernames', None)



    # Use the retrieved session details as needed

    return render_template('run_session.html', 
        session_id=session_id, distance=distance, shots_per_target=shots_per_target, 
        target_type=target_type, usernames=usernames)

@app.route('/process_shots/<int:session_id>', methods=['GET', 'POST'])
def process_shots(session_id):
    if 'username' not in session or session['username'] != 'admin':
        return redirect(url_for('login'))

    shooting_session = Session.query.get(session_id)

    if not shooting_session:
        return redirect(url_for('add_session'))

    if request.method == 'POST':
        for user_id in session.get('user_ids', []):
            for i in range(shooting_session.format.shots_per_target):
                shot_score_value = int(request.form.get(f'user_{user_id}_shot_{i+1}', 0))
                shot = Shot(score_id=user_id, shot_score=shot_score_value)
                db.session.add(shot)

        db.session.commit()

        return redirect(url_for('run_session'))

    user_ids = session.get('user_ids', [])
    
    print(user_ids)

    return render_template('process_shots.html', session_id=session_id, user_ids=user_ids, shots_per_target=shooting_session.format.shots_per_target)


if __name__ == '__main__':
    app.run(debug=True)
