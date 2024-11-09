

from datetime import datetime
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


# Admin Model
class Admin(db.Model):
    __tablename__ = 'admin'  
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(60), nullable=False)
    date_created = db.Column(db.DateTime, default=datetime.utcnow)
    secret_key= db.Column(db.String(60), nullable=False)
    def __repr__(self):
        return f'<Admin {self.name} - Email: {self.email}>'


# Customer Model
class Customer(db.Model):
    __tablename__ = 'customer'  
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    password = db.Column(db.String(60), nullable=False)
    address = db.Column(db.String(200), nullable=False) 
    date_created = db.Column(db.DateTime, default=datetime.utcnow)
    country = db.Column(db.String(100), nullable=False) 
    state = db.Column(db.String(100), nullable=False)   
    district = db.Column(db.String(100), nullable=False)
    pincode = db.Column(db.String(20), nullable=False)   
    flag_count = db.Column(db.Integer, default=0) # increments as customer_flag in Booking increases and rest to 0 after activation.
    active_status = db.Column(db.Boolean, nullable=False, default=True)  


    # Cascade delete on associated Bookings
    bookings = db.relationship('Booking', backref='customer', cascade="all, delete")

    def __repr__(self):
        return f'<Customer {self.name} - Email: {self.email}>'


# Service Model
class Service(db.Model):
    __tablename__ ='service'  
    id = db.Column(db.Integer, primary_key=True)  
    service_name = db.Column(db.String(100), nullable=False)  
    description = db.Column(db.Text, nullable=True) 
    service_status = db.Column(db.Boolean, nullable=False, default=True)  
    price = db.Column(db.Float, nullable=False) 
    time_required = db.Column(db.String(50), nullable=False)  
    date_created = db.Column(db.DateTime, default=datetime.utcnow) 

# Cascade delete on associated ServiceProfessionals and Bookings
    service_professionals = db.relationship('ServiceProfessional', backref='service', cascade="all, delete")
    bookings = db.relationship('Booking', backref='service', cascade="all, delete")

    def __repr__(self):
        return f'<Service {self.service_name} - Price: {self.price} - Time: {self.time_required} - Status: {self.service_status}>'


class ServiceProfessional(db.Model):
    __tablename__ = 'service_professional'
    id = db.Column(db.Integer, primary_key=True)
    govt_id = db.Column(db.String(100), unique=True, nullable=False) 
    name = db.Column(db.String(100), nullable=False)                  
    email = db.Column(db.String(120), unique=True, nullable=False)   
    phone = db.Column(db.String(20), nullable=False)                  
    password = db.Column(db.String(60), nullable=False)              
    address = db.Column(db.String(200), nullable=False)              
    experience = db.Column(db.Integer, nullable=False)                
    description = db.Column(db.String(200), nullable=False)          
    service_type = db.Column(db.String(100), nullable=False)         
    country = db.Column(db.String(100), nullable=False)             
    state = db.Column(db.String(100), nullable=False)                  
    district = db.Column(db.String(100), nullable=False)               
    pincode = db.Column(db.String(20), nullable=False)                
    date_created = db.Column(db.DateTime, default=datetime.utcnow)   
    service_id = db.Column(db.Integer, db.ForeignKey('service.id'), nullable=True) 
    govt_id_file = db.Column(db.LargeBinary, nullable=True)  

    flag_count = db.Column(db.Integer, default=0)  # increments as flag in Booking increases and rest to 0 after activation.
    active_status = db.Column(db.Boolean, nullable=False, default=False)  
    approve_status = db.Column(db.Boolean, nullable=False, default=False)


    # Cascade delete on associated Bookings
    bookings = db.relationship('Booking', backref='service_professional', cascade="all, delete")

    def __repr__(self):
        return f'<ServiceProfessional {self.name} - Active Status: {self.active_status}>'




# Booking Model
class Booking(db.Model):
    __tablename__ = 'booking'

    id = db.Column(db.Integer, primary_key=True)  
    service_id = db.Column(db.Integer, db.ForeignKey('service.id'), nullable=False)  
    customer_id = db.Column(db.Integer, db.ForeignKey('customer.id'), nullable=False)  
    service_professional_id = db.Column(db.Integer, db.ForeignKey('service_professional.id'), nullable=True)  
    booking_time = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)  
    booking_end_time = db.Column(db.DateTime, nullable=True) 
    status = db.Column(db.String(50), nullable=False, default='Pending') 
    comments = db.Column(db.Text, nullable=True)  
    rating = db.Column(db.Float, nullable=True)  
    flag = db.Column(db.Boolean, default=False)  
    flag_customer = db.Column(db.Boolean, default=False)  
   

    def __repr__(self):
        return f'<Booking {self.id} - Status: {self.status} - Flag: {self.flag}>'
