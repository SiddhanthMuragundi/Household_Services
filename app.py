from flask import Flask
from model import db,Admin  
from werkzeug.security import generate_password_hash
app = Flask(__name__)
app.secret_key = 'MAD1_Project_Sept'  

# Configure the database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'  
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)  #

ALLOWED_EXTENSIONS = {'pdf', 'jpg', 'jpeg', 'png'}

app.config['MAX_CONTENT_LENGTH'] = 2 * 1024 * 1024  # File Max 2MB file size



with app.app_context():
    db.create_all()  # Create tables if they don't exist
    if Admin.query.first() is None or Admin.query.filter_by(email="admin@email.com").first() is None:
        new_admin = Admin(id=1,name="admin", email="admin@email.com",   password= generate_password_hash("admin"), secret_key=generate_password_hash("secret_key"))

        # Save to the database
        db.session.add(new_admin)
        db.session.commit()


# Importing routes 
from controller import *

if __name__ == '__main__':
    app.run(debug=True)
