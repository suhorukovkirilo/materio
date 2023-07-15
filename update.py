from app import app, database
from models import User, Article, OTP
with app.app_context():
    database.create_all()
print(True)    
