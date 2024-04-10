from flask import Flask, render_template, request, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import IntegrityError
from flask import jsonify, request, render_template, redirect, url_for, session
from collections import defaultdict
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
import statistics

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Change this to a secure secret key
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'  # Use SQLite database
db = SQLAlchemy(app)

from SessionClasses import SessionLeader, SessionDistrictComissioner, SessionScout

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
    type = db.Column(db.String(120), nullable=False) # Scout, Leader or District Comissioner
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

    def add_new_user(username, password, admin, group_id, type):
        existing_user = User.query.filter_by(username=username).first()
        if not existing_user:
            hashed_password = generate_password_hash(password)
            new_user = User(username=username, password=hashed_password, admin=admin, group_id=group_id, type=type)
            db.session.add(new_user)
            db.session.commit()
            print(f"Added new user: {username}")
        else:
            print(f"User already exists: {username}")

    def add_new_format(shots_per_target, target_type, distance):
        existing_format = Format.query.filter_by(shots_per_target=shots_per_target, target_type=target_type, distance=distance).first()
        if not existing_format:
            new_format = Format(shots_per_target=shots_per_target, target_type=target_type, distance=distance)
            db.session.add(new_format)
            db.session.commit()
            print(f"Added new Format: Shots Per Tartget: {shots_per_target}, Target Type: {target_type}, Distance: {distance}")
            return True
        else:
            print(f"Format already exists: Shots Per Tartget: {shots_per_target}, Target Type: {target_type}, Distance: {distance}") 
            return False          

    ## For testing purposes
    add_new_group("Whitley Bay", 9)
    add_new_group("Teddington", 3)
    add_new_user("scout1", "password1", False, 1, "scout")  # Assuming group_id for Whitley Bay is 1
    add_new_user("scout2", "password2", False, 1, "scout") 
    add_new_user("leader", "leader", True, 1, "leader") 
    add_new_user("dc", "dc", True, 1, "district comissioner") 
    add_new_format(3, "Paper targets", 10)
    add_new_format(2, "Paper targets", 5)

def get_session_user_object():

    # Check if user object already exists and is in session 

    if 'user_object_dict' not in session:
        print("There is no user_object_dict in session - redirecting to login page")
        print(session)
        return False

    # Retrieve Information About our Object
    user_object_dict = session.get('user_object_dict')
    print(user_object_dict)

    id = user_object_dict['_SessionUser__id']
    username = user_object_dict['_SessionUser__username']
    group_id = user_object_dict['_SessionUser__group_id']
    type = user_object_dict['_SessionUser__type']

    if type == "leader":
        user_object = SessionLeader(id, username, group_id, type, Group)
    elif type == "scout":
        user_object = SessionScout(id, username, group_id, type, Group)
    elif type == "district comissioner":
        user_object = SessionDistrictComissioner(id, username, group_id, type, Group)
    else:
        return "NO USER OBJECT CREATED"
        
    return user_object

def create_session_subclass(id, username, group_id, type):
    # Create a user subclass for the session
    if type == "scout":
        session_user = SessionScout(id, username, group_id, type, Group)
    elif type == "leader":
        session_user = SessionLeader(id, username, group_id, type, Group)
    elif type == "district comissioner":
        session_user = SessionDistrictComissioner(id, username, group_id, type, Group)

    return session_user

@app.route('/')
def home():
    # Retrieve the user object
    user_object = get_session_user_object()

    if user_object:
        username = user_object.get_username()
        print(username)
    else: 
        return redirect(url_for('login'))

    return render_template('home.html', username=username)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # Get the username from HTML form
        username = request.form['username']
        password = request.form['password']
        # Get corresponding user object from database
        user = User.query.filter_by(username=username).first()

        if user and check_password_hash(user.password, password):
            print(username)
            print(user.admin)

            # Retrieve User Data From Database for object creation
            id = user.id
            username = user.username
            type = user.type
            group_id = user.group_id

            # Create a user subclass for the session
            session_user = create_session_subclass(id=id, username=username, type=type, group_id=group_id)
            session['user_object_dict'] = session_user.__dict__
            print(session_user.__dict__)
           
            return redirect(url_for('home'))
        else:
            return 'Invalid login credentials. <a href="/login">Try again</a>'
        
    return render_template('login.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        # Get information from HTML form 
        username = request.form['username']
        password = request.form['password']
        admin_checkbox_checked = 'admin' in request.form
        district_name = request.form['district']
        group_number = request.form['group_number']
        type = "scout"

        print(username)

        try:
            # Check if the district exists, and get the associated District object
            district = Group.query.filter_by(district=district_name, number=group_number).first()

            if not district:
                return 'Group does not exist. <a href="/signup">Try a different group</a>'
            
            hashed_password = generate_password_hash(password)

            #print(district.id)
            #print(int(district.id))

            # Create a new user and assign the district and group
            group_id = int(int(district.id))
            new_user = User(username=username, password=hashed_password, admin=admin_checkbox_checked, 
                            group_id=group_id, type=type)

            db.session.add(new_user)
            db.session.commit()

            # Create a user session object and add to the session 
            session_user = create_session_subclass(id=new_user.id, username=new_user.username, 
                                                   type=new_user.type, group_id=new_user.group_id)
            session['user_object_dict'] = session_user.__dict__

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

    session.pop('user_object_dict', None)
    session.pop('event_id', None)
    session.pop('distance', None)
    session.pop('shots_per_target', None)
    session.pop('target_type', None)
    session.pop('shooters', None)
    session.pop('shooters_username', None)

    return redirect(url_for('home'))

@app.route('/add_event', methods=['GET', 'POST'])
def add_event():
    if 'user_object_dict' not in session:
        print("Admin is False or Username not in session ")
        print(session)
        return redirect(url_for('login'))
    
    user_object = get_session_user_object()

    if request.method == 'POST':
        username = user_object.get_username()
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
            #new_format = Format(target_type=target_type, shots_per_target=shots_per_target, distance=distance) 
            add_new_format(shots_per_target=shots_per_target, target_type=target_type, distance=distance)

            db.session.add(new_event)
            #db.session.add(new_format)
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
    formats = Format.query.all()
    return render_template('add_event.html', groups=groups, formats=formats)

    

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



def retrieve_shooting_data(user_id, user):
    scores = Score.query.filter_by(user_id=user_id).all()
    
    event_dict = defaultdict(list)

    if user:
        shooter_name = user.username
        print("Username:", shooter_name)
    else:
        print("User not found.")

    averages = []

    for score in scores:
        shots = Shot.query.filter_by(score_id=score.id).all()
        shot_scores = [shot.shot_score for shot in shots]
        
        # find event information from event_id 
        searched_event = Event.query.filter_by(id=score.event_id).first()
        event_date = searched_event.date
        event_time = searched_event.time
        
        format = Format.query.filter_by(id=score.format_id).first()
        print(format)
        averages.append(score.average)

        event_dict[(score.event_id, score.format_id, event_date, event_time, 
                    format.shots_per_target, format.target_type, format.distance)].append(shot_scores)

    # Convert defaultdict to list of dictionaries
    event_list = [{'shooter_name': shooter_name, 'event_id': event[0], 'format_id': event[1], 
                     'event_date': event[2], "event_time": event[3],
                     'spt': event[4], 'target_type': event[5], 'distance': event[6],
                     'shot_scores': scores, 'averages': averages} for event, scores in event_dict.items()]
    
   

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
    #if 'username' in session and session['admin'] == False:
    #    print("Admin is False or Username not in session ")
    #    print(session)
    #    return redirect(url_for('login'))
    
    user_object = get_session_user_object()

    try:
        event_id, distance, shots_per_target, target_type, shooters, event_date, event_time, shooters_username = user_object.run_event(User=User)
    except:
        print("This user type cannot run event")
        redirect(url_for('add_event'))

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
    if 'user_object_dict' not in session:
        print("User Object Dictionary Not In Session")
        print(session)
        return redirect(url_for('login'))

    
    user_object = get_session_user_object()

    try:
        event_id, shot_data, shots_per_target = user_object.process_shooter(db, User, Event, Format, Score, Shot)
    except:
        print("This user is not able to run the process shooter method")


    return render_template('process_shooter.html', event_id=event_id, shot_data=shot_data, shots_per_target=shots_per_target)


@app.route('/search')
def search():

    if 'username' in session and session['admin'] == True:
        return redirect(url_for('login'))

    users = User.query.all()
    return render_template('search.html', users=users)

@app.route('/my_profile')
def my_profile():

    if 'user_object_dict' not in session:
        return redirect(url_for('login'))
    
    user_object = get_session_user_object()

    
    #username = user_object.get_username()
    #user_id = user_object.get_id()
    
    #username = session.get("username")
    #user_id = session.get("user_id")

    #user_data = User.query.filter_by(id = user_id).first()
    #user_group_id = user_data.group_id
    #user_group_data = Group.query.filter_by(id = user_group_id).first()
    #n = user_group_data.number
    #suffix = { 1: "st", 2: "nd", 3: "rd" }.get(n if (n < 20) else (n % 10), 'th')
    #group_name = str(str(user_group_data.number) + suffix + " " + user_group_data.district)
    #print(group_name)
    username, group_name, user_id, user_data = user_object.my_profile(User)
    event_list = retrieve_shooting_data(user_id=user_id, user=user_data)
    
    return render_template('my_profile.html', 
                           group_name = group_name, 
                           username = username, 
                           event_list=event_list
                           )
 

if __name__ == '__main__':
    app.run(debug=True)
