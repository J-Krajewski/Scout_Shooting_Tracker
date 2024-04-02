from flask import Flask, render_template, request, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import IntegrityError
from flask import jsonify, request, render_template, redirect, url_for, session
from collections import defaultdict
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
import statistics



    
class SessionUser():

    def __init__(self, id, username, group_id, type, Group): # Constructor or initialiser 
        self.__id = id
        self.__username = username
        self.__group_id = group_id
        self.__type = type
        self.__group_disrict = Group.query.filter_by(id = self.__group_id).first().district
        self.__group_number = Group.query.filter_by(id = self.__group_id).first().number

    # Any user should be able to add a new scout user 
    def add_new_scout(username, password, group_id, type, db, User):
        existing_user = User.query.filter_by(username=username).first()
        if not existing_user:
            hashed_password = generate_password_hash(password)
            new_user = User(username=username, password=hashed_password, admin=False, group_id=group_id, type=type)
            db.session.add(new_user)
            db.session.commit()
            print(f"Added new user: {username}")
        else:
            print(f"User already exists: {username}")

    # getter methods and setter methods to retrieve private information from object
    def get_username(self):
        return self.__username
    
    def get_id(self):
        return self.__id
    
    def my_profile(self, User):

        user_data = User.query.filter_by(id = self.__id).first()
        n = self.__group_number
        suffix = { 1: "st", 2: "nd", 3: "rd" }.get(n if (n < 20) else (n % 10), 'th')
        group_name = str(str(n) + suffix + " " + self.__group_district)
        print(group_name)

        return self.__username, group_name, self.__id, user_data

class SessionScout(SessionUser):

    def __init__(self, id, username, group_id, type, Group):
        super().__init__(id, username, group_id, type, Group)
        self.__admin = False
        self.__priviledges = []

    def get_username(self):
        return super().get_username()
    
    def get_id(self):
        return super().get_id()

class SessionLeader(SessionUser):

    def __init__(self, id, username, group_id, type, Group):
        super().__init__(id, username, group_id, type, Group)
        self.__admin = True
        self.__priviledges = ["start_shooting"]

    def run_event(self, User):
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

        return event_id, distance, shots_per_target, target_type, shooters, event_date, event_time, shooters_username
    
    def process_shooter(self, db, User, Event, Format, Score, Shot):
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
                        average_score = statistics.mean(user_shot_data)
                        print(average_score)
                        score = Score(event_id=event.id, user_id=user.id, format_id=event_format.id, average=average_score)
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

        return event_id, shot_data, shots_per_target


    def get_username(self):
        return super().get_username()
    
    def get_id(self):
        return super().get_id()
    
    
class SessionDistrictComissioner(SessionUser):

    def __init__(self, id, username, group_id, type, Group):
        super().__init__(id, username, group_id, type, Group)
        self.__admin = True
        self.__priviledges = ["add_district", "add_leader", "delete_leader", "delete_district"]

    def add_leader(username, password, group_id, db, User):
        existing_user = User.query.filter_by(username=username).first()
        if not existing_user:
            hashed_password = generate_password_hash(password)
            new_user = User(username=username, password=hashed_password, admin=True, group_id=group_id)
            db.session.add(new_user)
            db.session.commit()
            print(f"Added new user: {username}")
        else:
            print(f"User already exists: {username}")

    def add_district(district, number, db, Group):
        existing_group = Group.query.filter_by(district=district, number=number).first()
        if not existing_group:
            new_group = Group(district=district, number=number)
            db.session.add(new_group)
            db.session.commit()
            print(f"Added new group: {district}, Number: {number}")
        else:
            print(f"Group already exists: {district}, Number: {number}")

    def get_username(self):
        return super().get_username()
    
    def get_id(self):
        return super().get_id()