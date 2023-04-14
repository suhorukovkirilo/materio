from flask_app import app, database
with app.app_context():
    database.create_all()
print(True)
