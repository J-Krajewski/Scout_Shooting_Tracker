from flask import Flask, render_template, request, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import IntegrityError
from flask import jsonify, request, render_template, redirect, url_for, session
from collections import defaultdict
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Change this to a secure secret key
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'  # Use SQLite database
#app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///instance/site.db'

db = SQLAlchemy(app)

class Group(db.Model):
    __tablename__ = "group"
    id = db.Column(db.Integer, primary_key=True)
    district = db.Column(db.String(100), nullable=True)
    number = db.Column(db.Integer, nullable=True)

class User(db.Model):
    __tablename__ = "user"
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    admin = db.Column(db.Boolean, nullable=False)
    group_id = db.Column(db.Integer, db.ForeignKey('group.id'), nullable=False)
    #scores = db.relationship('Event', backref='user', lazy=True)

class Format(db.Model):
    __tablename__ = "format"
    id = db.Column(db.Integer, primary_key=True)
    shots_per_target = db.Column(db.Integer, nullable=False)
    target_type = db.Column(db.String(50), nullable=False)
    distance = db.Column(db.Integer, nullable=False)
    
class Event(db.Model):
    __tablename__ = "event"
    id = db.Column(db.Integer, primary_key=True) 
    description = db.Column(db.String(100), nullable=True)
    date = db.Column(db.String(100), nullable=True)
    time = db.Column(db.String(100), nullable=True)

class Score(db.Model):
    __tablename__ = "score"
    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey('event.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    format_id = db.Column(db.Integer, db.ForeignKey('format.id'), nullable=False)
    average = db.Column(db.Float, nullable=True)

class Shot(db.Model):
    __tablename__ = "shots"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    score_id = db.Column(db.Integer, db.ForeignKey('score.id'), nullable=False)
    shot_score = db.Column(db.Integer, nullable=False)

# Create the database tables before running the app
with app.app_context():
    db.create_all()

    def add_new_group(district, number):
        existing_group = Group.query.filter_by(district=district, number=number).first()
        if not existing_group:
            new_group = Group(district=district, number=number)
            db.session.add(new_group)
            db.session.commit()
            print(f"Added new group: {district}, Number: {number}")
        else:
            print(f"Group already exists: {district}, Number: {number}")

    def add_new_user(username, password, admin, group_id):
        existing_user = User.query.filter_by(username=username).first()
        if not existing_user:
            new_user = User(username=username, password=password, admin=admin, group_id=group_id)
            db.session.add(new_user)
            db.session.commit()
            print(f"Added new user: {username}")
        else:
            print(f"User already exists: {username}")

    add_new_group("Whitley Bay", 9)
    add_new_group("Teddington", 3)
    add_new_user("scout1", "password1", False, 1)  # Assuming group_id for Whitley Bay is 1
    add_new_user("scout2", "password2", False, 1) 
    add_new_user("leader", "leader", True, 1) 


@app.route('/')
def home():
     return render_template('home.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        user = User.query.filter_by(username=username, password=password).first()

        if user:
            print("User Found, Starting Shooting Event")
            print(username)
            print(user.admin)
            session['username'] = username
            session['admin'] = user.admin
            session["user_id"] = user.id
            return redirect(url_for('home'))
        else:
            return 'Invalid login credentials. <a href="/login">Try again</a>'
        
        

    return render_template('login.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        admin_checkbox_checked = 'admin' in request.form
        district_name = request.form['district']
        group_number = request.form['group_number']


        try:
            # Check if the district exists, and get the associated District object
            district = Group.query.filter_by(district=district_name, number=group_number).first()

            if not district:
                return 'Group does not exist. <a href="/signup">Try a different group</a>'
            
            print(district.id)
            print(int(district.id))

            # Create a new user and assign the district and group
            new_user = User(username=username, password=password, admin=admin_checkbox_checked, group_id=int(district.id))

            db.session.add(new_user)
            db.session.commit()

            print("ADDED")

            session['username'] = username
            session['admin'] = admin_checkbox_checked


            return redirect(url_for('home'))
        except IntegrityError:
            db.session.rollback()
            return 'Username already exists. <a href="/signup">Try a different username</a>'


    # Provide a list of existing groups for the user to choose from during signup
    groups = Group.query.all()
    return render_template('signup.html', groups=groups)

@app.route('/users')
def user_list():
    # Only allow access to the user list for an admin user (for demonstration purposes)
    if 'username' in session and session['admin'] == True:
        users = User.query.all()
        return render_template('user_list.html', users=users)
    else:
        return 'You do not have permission to access this page.'

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('home'))

@app.route('/add_event', methods=['GET', 'POST'])
def add_event():
    if 'username' not in session or session['admin'] == False:
        print("Admin is False or Username not in session ")
        print(session)
        return redirect(url_for('login'))

    if request.method == 'POST':
        username = session['username']
        user = User.query.filter_by(username=username).first()

        if user:
            # Getting data from add_event.html
            distance = int(request.form['distance'])
            shots_per_target = int(request.form['shots_per_target'])
            

            if 'autoDateTime' in request.form:
                auto_date_time = request.form['autoDateTime']
            else:
                auto_date_time = False

            if auto_date_time:
                print("Using Automatic Date Time")
                current_datetime = datetime.now()
                date = current_datetime.date().strftime('%Y-%m-%d')
                time = current_datetime.time().strftime('%H:%M')
            else:
                print("Using Manual Date Time")
                date = request.form['date']
                time = request.form['time']
           
            target_type = request.form['target_type']
            description = request.form['description']
            shooters = session.get('shooters')

            # Adding data to respective tables
            new_event = Event(description=description, date=date, time=time)
            new_format = Format(target_type=target_type, shots_per_target=shots_per_target, distance=distance) 

            db.session.add(new_event)
            db.session.add(new_format)
            db.session.commit()

            # Store event details in the Flask session for use in run_event
            session['event_id'] = new_event.id
            session['event_date'] = date
            session['event_time'] = time
            session['distance'] = distance
            session['shots_per_target'] = shots_per_target
            session['target_type'] = target_type
            

            print("/add_event: shooters", shooters)
            print("/add_event: session['shooters']:", session.get('shooters'))
            print("DATE:", date)
            print("TIME:", time)

            return redirect(url_for('run_event'))

    groups = Group.query.all()

    return render_template('add_event.html', groups=groups)

    

@app.route('/search_users', methods=['POST'])
def search_users():
    search_query = request.form.get('search_query')

    print("/search_users: search_query: ", search_query)

    if not search_query:
        return jsonify({'error': 'Invalid search query'})

    users = User.query.filter(User.username.ilike(f'%{search_query}%')).all()

    print("/search_users: users: ", search_query)

    user_list = [{'id': user.id, 'username': user.username} for user in users]

    print("/search_users: user_list: ", user_list)

    return jsonify({'users': user_list})


@app.route('/review_scores')
def review_scores():
    return render_template('review_scores.html')

from collections import defaultdict

def retrieve_shooting_data(user_id, user):
    scores = Score.query.filter_by(user_id=user_id).all()
    
    event_dict = defaultdict(list)

    if user:
        shooter_name = user.username
        print("Username:", shooter_name)
    else:
        print("User not found.")

    for score in scores:
        shots = Shot.query.filter_by(score_id=score.id).all()
        shot_scores = [shot.shot_score for shot in shots]

        # find event information from event_id 
        searched_event = Event.query.filter_by(id=score.event_id).first()
        event_date = searched_event.date
        event_time = searched_event.time
        
        format = Format.query.filter_by(id=score.format_id).first()
        print(format)
        

        event_dict[(score.event_id, score.format_id, event_date, event_time, 
                    format.shots_per_target, format.target_type, format.distance)].append(shot_scores)

    # Convert defaultdict to list of dictionaries
    event_list = [{'shooter_name': shooter_name, 'event_id': event[0], 'format_id': event[1], 
                     'event_date': event[2], "event_time": event[3],
                     'spt': event[4], 'target_type': event[5], 'distance': event[6],
                     'shot_scores': scores} for event, scores in event_dict.items()]

    print("Shooting Event List",event_list)

    return event_list

@app.route('/get_user_scores/<int:user_id>')
def get_user_scores(user_id):
    user = User.query.get(user_id)
    if not user:
        return jsonify({'error': 'User not found'})

    event_list = retrieve_shooting_data(user_id=user_id, user=user)

    return jsonify({'events': event_list})


@app.route('/add_user_to_event', methods=['POST'])
def add_user_to_event():
    ## Getting this from the search function in add_event
    shooter_id = request.form.get('user_id')
    event_shooters = session.get('shooters', [])

    print("/add_user_to_event: shooter_id:", shooter_id)
    print("/add_user_to_event: event_shooters", event_shooters)
    
    if shooter_id:
        # Check if the user is already in the event
        if shooter_id not in event_shooters:
            event_shooters.append(shooter_id)
            session['shooters'] = event_shooters

    # Retrieve the list of groups for rendering the template
    groups = Group.query.all()

    # Retrieve the list of users for rendering the template
    users = User.query.all()

    print("/add_user_to_event: session['shooters']: ", session.get('shooters'))
    
    return render_template('add_event.html', groups=groups, users=users)


@app.route('/run_event', methods=['GET', 'POST'])
def run_event():
    if 'username' in session and session['admin'] == False:
        print("Admin is False or Username not in session ")
        print(session)
        return redirect(url_for('login'))

    # Initialize shooters_username outside the if block
    shooters_username = []

    # Retrieve session details from the Flask session
    event_id = session.get('event_id')
    distance = session.get('distance')
    shots_per_target = session.get('shots_per_target')
    target_type = session.get('target_type')
    shooters = session.get('shooters')
    event_date = session.get('event_date')
    event_time = session.get('event_time')

    # Check if shooters is not None before using it in the query
    if shooters is not None:
        # Fetch user objects from the database based on the IDs
        users = User.query.filter(User.id.in_(shooters)).all()

        # Extract usernames from the user objects
        shooters_username = [user.username for user in users]
    
    session['shooters_username'] = shooters_username

    if not all([event_id, distance, shots_per_target, target_type, shooters, shooters_username]):
        print("event_id:", event_id)
        print("event_date:", event_date)
        print("event_time:", event_time)
        print("distance:", distance)
        print("shot_per_target:", shots_per_target)
        print("target_type:", target_type)
        print("shooters:", shooters)
        print("shooters_username:", shooters_username)
        
        #print(session)
        return redirect(url_for('add_event'))

    # For each user: display: 
    # Input for each shot, which appears (shots_per_target) number of times 
    
    # Clear the session details to avoid reusing them
    #session.pop('event_id', None)
    #session.pop('distance', None)
    #session.pop('shots_per_target', None)
    #session.pop('target_type', None)
    #session.pop('shooters', None)
    #session.pop('shooters_username', None)

    # Use the retrieved session details as needed

    return render_template('run_event.html', 
        event_id=event_id, 
        distance=distance, 
        shots_per_target=shots_per_target, 
        target_type=target_type, 
        shooters=shooters, 
        shooters_username=shooters_username, date=event_date, time=event_time
        )

@app.route('/process_shooter/<int:event_id>', methods=['GET', 'POST'])
def process_shooter(event_id):
    if 'username' not in session or session['admin'] == False:
        print("Admin is False or Username not in session ")
        print(session)
        return redirect(url_for('login'))
    
    event_id = session.get('event_id')
    distance = session.get('distance')
    shots_per_target = session.get('shots_per_target')
    target_type = session.get('target_type')
    shooters = session.get('shooters')
    shooters_username = session.get('shooters_username')

    print("event_id:", event_id)
    print("distance:", distance)
    print("shot_per_target:", shots_per_target)
    print("target_type:", target_type)
    print("shooters:", shooters)
    print("shooters_username:", shooters_username)

    # Initialize a dictionary to store shot data for each user
    shot_data = {}

    if request.method == 'POST':
        selected_users = request.form.getlist('selected_users[]')
        print(selected_users)

        for username in selected_users:
            user_shot_data = []
            for i in range(1, shots_per_target + 1):
                shot_key = f'user_{username}_shot_{i}'
                print("shot key:", shot_key)
                shot_score = int(request.form.get(shot_key, 0))
                print("shot score:", shot_score)
                user_shot_data.append(shot_score)
            shot_data[username] = user_shot_data

            # Add shot data to the database
            user = User.query.filter_by(username=username).first()
            if user:
                event = Event.query.get(event_id)
                event_format = Format.query.filter_by(shots_per_target=shots_per_target, target_type=target_type, distance=distance).first()
                
                if event and event_format:
                    score = Score(event_id=event.id, user_id=user.id, format_id=event_format.id)
                    db.session.add(score)
                    db.session.commit()

                    for shot_score in user_shot_data:
                        shot = Shot(score_id=score.id, shot_score=shot_score)
                        db.session.add(shot)
                        db.session.commit()

                ## Calculate Shot Statistics 


            else:
                print("Shooting event or format not found")
        else:
            print("User not found")

        # Now shot_data is a dictionary where keys are usernames and values are lists of shot scores
        print("Shot data:", shot_data)

        # Here you can process the shot data and save it to the database

        ## Get event

        event = Event.query.get(id=event_id).first()
        #event_shooters 
        scores = Score.query.get(event_id=event_id).all()

        print(scores)
            
            # for each user in event
                # get all shot scores
                # add all shot scores
                # find total number of shots taken != shots per target 
                # calculate average
                # update database 
        

    return render_template('process_shooter.html', event_id=event_id, shot_data=shot_data, shots_per_target=shots_per_target)


@app.route('/search')
def search():

    if 'username' in session and session['admin'] == True:
        return redirect(url_for('login'))

    users = User.query.all()
    return render_template('search.html', users=users)

@app.route('/my_profile')
def my_profile():

    if 'username' not in session:
        return redirect(url_for('login'))
    
    username = session.get("username")
    user_id = session.get("user_id")

    user_data = User.query.filter_by(id = user_id).first()
    user_group_id = user_data.group_id
    user_group_data = Group.query.filter_by(id = user_group_id).first()
    n = user_group_data.number
    suffix = { 1: "st", 2: "nd", 3: "rd" }.get(n if (n < 20) else (n % 10), 'th')
    group_name = str(str(user_group_data.number) + suffix + " " + user_group_data.district)
    print(group_name)

    event_list = retrieve_shooting_data(user_id=user_id, user=user_data)
    
    return render_template('my_profile.html', 
                           group_name = group_name, 
                           username = username, 
                           event_list=event_list
                           )
 

if __name__ == '__main__':
    app.run(debug=True)
