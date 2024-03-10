from app import db, User

# Create the database tables
db.create_all()

# Add a sample user to the database
sample_user = User(username='user1', password='password123')
db.session.add(sample_user)
db.session.commit()

# Exit the Python shell
exit()