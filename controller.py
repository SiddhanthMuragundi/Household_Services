from flask import render_template, request, redirect, url_for, flash, session,send_file
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from model import db, Admin, Customer, ServiceProfessional, Service,Booking  
from app import app  
from functools import wraps
from sqlalchemy import func, cast, String
from datetime import datetime,timedelta
from werkzeug.security import check_password_hash
from datetime import datetime
from io import BytesIO


ALLOWED_EXTENSIONS = {'pdf', 'jpg', 'jpeg', 'png'}  

#function to check file extension
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS 

#check authentication
def auth_required(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please sign in to continue.', 'danger')  
            return redirect(url_for('login'))  
        return func(*args, **kwargs)
    return wrapper

#check for admin only pages
def admin_only(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please sign in to continue.', 'danger')
            return redirect(url_for('login'))
        
        if session.get('user_role') != 'admin':
            error_message = 'You do not have access to this page.'
            return render_template('unauthorised_access.html', error=error_message)  # Passing error to home page
        
        return func(*args, **kwargs)
    return wrapper

#check for customer only pages
def customer_only(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please sign in to continue.', 'danger')
            return redirect(url_for('login'))
        
        if session.get('user_role') != 'customer':
            error_message = 'You do not have access to this page.'
            return render_template('unauthorised_access.html', error=error_message)  # Passing error to home page
        
        return func(*args, **kwargs)
    return wrapper

#check for service_prof only pages
def service_professional_only(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please sign in to continue.', 'danger')
            return redirect(url_for('login'))
        
        if session.get('user_role') != 'service_professional':
            error_message = 'You do not have access to this page.'
            return render_template('unauthorised_access.html', error=error_message)  # Passing error to home page
        
        return func(*args, **kwargs)
    return wrapper


def authenticate_user(email, password, role):
    user = None

    # Retrieve the user based on the role
    if role == 'admin':
        user = Admin.query.filter_by(email=email).first()
    elif role == 'customer':
        user = Customer.query.filter_by(email=email).first()
    elif role == 'service_professional':
        user = ServiceProfessional.query.filter_by(email=email).first()

    # Check if user exists and credentials match
    if user and check_password_hash(user.password, password):
    
        if role == 'customer':
            if not user.active_status:
                session['active_status'] = False
                return False
            session['user_id'] = user.id
            session['user_role'] = role
            return True

        
        elif role == 'service_professional':
            if not user.approve_status:
                session['approve_status'] = False
                return False
            if not user.active_status:
                session['active_status'] = False
                return False
            session['user_id'] = user.id
            session['user_role'] = role
            return True

        
        session['user_id'] = user.id
        session['user_role'] = role
        return True

   
    flash("Invalid login credentials. Please try again.", "error")
    return False

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        role = request.form['user_role']
        email = request.form['email']
        password = request.form['password']

        if not authenticate_user(email, password, role):
            
            if 'approve_status' in session and not session['approve_status']:
                session.pop('approve_status', None) # Clear the session flag
                return render_template('account_not_approved.html')
            elif 'active_status' in session and not session['active_status']:
                session.pop('active_status', None)  
                return render_template('account_blocked.html')
            return redirect(url_for('login'))  

        # Redirect based on role after successful authentication
        if role == 'admin':
            return redirect(url_for('admin_dashboard'))
        elif role == 'customer':
            return redirect(url_for('customer_dashboard'))
        elif role == 'service_professional':
            return redirect(url_for('serviceprof_dashboard'))
    
    return render_template('login.html')




@app.route('/')
def home():
    if 'user_id' in session:
        user_id = session['user_id']
        role = session['user_role']  
        
        if role == 'admin':
            user = Admin.query.get(user_id)
            return redirect(url_for('admin_dashboard')) 
        elif role == 'customer':
            user = Customer.query.get(user_id)
            return redirect(url_for('customer_dashboard')) 
        elif role == 'service_professional':
            user = ServiceProfessional.query.get(user_id)
            return redirect(url_for('serviceprof_dashboard')) 
        else:
            flash('Invalid role.', 'danger')
            return redirect(url_for('home'))  
        
        
    return render_template('home.html')



@app.route('/admin_dashboard')
@auth_required
@admin_only
def admin_dashboard():
    user_id = session['user_id']
    role = session['user_role'] 
    user = Admin.query.get(user_id)
    return render_template('admin_dashboard.html',user=user, role=role)

@app.route('/customer_dashboard')
@auth_required
@customer_only
def customer_dashboard():
    user_id = session['user_id']
    role = session['user_role'] 
    user = Customer.query.get(user_id)
    flag_count=user.flag_count
    return render_template('customer_dashboard.html',user=user, role=role,flag_count=flag_count)

@app.route('/serviceprof_dashboard')
@auth_required
@service_professional_only
def serviceprof_dashboard():
    user_id = session['user_id']
    role = session['user_role'] 
    user = ServiceProfessional.query.get(user_id)
    flag_count=user.flag_count
    return render_template('serviceprof_dashboard.html',user=user, role=role,flag_count=flag_count)


@app.route('/logout',methods=['POST','GET'])
def logout():
    session.pop('user_id', None)  # Remove user_id from session
    flash('You have been logged out.', 'info')  
    return redirect(url_for('login'))



@app.route('/forgot_password', methods=['POST', 'GET'])
def forgot_password():
    if request.method == 'POST':
        role = request.form['user_role']
        email = request.form['email']
        
        new_password = request.form['new_password']  
        confirm_password = request.form['confirm_new_password']  

        # Ensure that the new password and confirm password match
        if new_password != confirm_password:
            flash('New password and confirm password do not match.', 'danger')
            return redirect(url_for('forgot_password'))

        if role == "service_professional":
            user = ServiceProfessional.query.filter_by(email=email).first()
            if user:
                hashed_password = generate_password_hash(new_password)
                user.password = hashed_password
                db.session.commit()
                flash('Password reset successful. You can now login.', 'success')
                return redirect(url_for('login'))
            else:
                flash('No user found with this email.', 'danger')
                return redirect(url_for('forgot_password'))

        elif role == "customer":
            user = Customer.query.filter_by(email=email).first()
            if user:
                hashed_password = generate_password_hash(new_password)
                user.password = hashed_password
                db.session.commit()
                flash('Password reset successful. You can now login.', 'success')
                return redirect(url_for('login'))
            else:
                flash('No user found with this email.', 'danger')
                return redirect(url_for('forgot_password'))

        elif role == "admin":
            
            secret_key=request.form['secret_key']
            

            user = Admin.query.filter_by(email=email).first()
            if check_password_hash(user.secret_key, secret_key):

                if user:
                    hashed_password = generate_password_hash(new_password)
                    user.password = hashed_password
                    db.session.commit()
                    flash('Password reset successful. You can now login.', 'success')
                    return redirect(url_for('login'))
                else:
                    flash('No user found with this email.', 'danger')
                    return redirect(url_for('forgot_password'))
            else:
                flash('You are not authorised to perform this action.', 'danger')
                return redirect(url_for('forgot_password'))

 
    return render_template('forgot_password.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    active_service_names = db.session.query(Service.service_name).filter_by(service_status=True).all()
    active_service_names = [service[0] for service in active_service_names]  
    return render_template('registrationform.html', service_names=active_service_names)


@app.route('/register_customer', methods=['GET','POST'])
def register_customer():
    name = request.form['customer-username']
    password = request.form['customer-password']
    email = request.form['customer-email']
    phone = request.form['customer-phone-no']
    address = request.form['customer-address']
    district = request.form['customer-district']
    state=request.form['customer-state']
    country = request.form['customer-country']  
    pincode = request.form['customer-pincode']

    # Check if email already exists in the Customer table
    existing_email = Customer.query.filter_by(email=email).first()
    if existing_email:
        flash('This email is already registered. Please use a different one.', 'danger')
        return redirect(url_for('register'))

    # Check if phone already exists in the Customer table
    existing_phone = Customer.query.filter_by(phone=phone).first()
    if existing_phone:
        flash('This phone number is already registered. Please use a different one.', 'danger')
        return redirect(url_for('register'))

    
    hashed_password = generate_password_hash(password)

    # Create a new customer instance
    new_customer = Customer(name=name, email=email, phone=phone, address=address, password=hashed_password, district=district, state=state, country=country, pincode=pincode)

    # Save to the database
    db.session.add(new_customer)
    db.session.commit()
    user = Customer.query.filter_by(email=email).first()
    session['user_id']=user.id
    session['user_role'] = 'customer'
    flash('Customer registered successfully!', 'success')
    return redirect(url_for('customer_dashboard'))


@app.route('/register_service_prof', methods=['GET','POST'])
def register_service_prof():

    govt_id = request.form['service-prof-govt-id-no']
    name = request.form['service-prof-name']
    email = request.form['service-prof-email']
    password = request.form['service-prof-password']
    phone = request.form['service-prof-phone-no']
    description = request.form['service-prof-description']
    service_type = request.form['service-prof-type']
    experience = request.form['service-prof-experience']
    address = request.form['service-prof-address']
    district = request.form['service-prof-district']
    state = request.form['service-prof-state']
    country = request.form['service-prof-country']
    pincode = request.form['service-prof-pincode']


    # Check if govt_id already exists in the ServiceProfessional table
    existing_govt_id = ServiceProfessional.query.filter_by(govt_id=govt_id).first()
    if existing_govt_id:
        flash('This Govt ID is already registered. Please use a different one.', 'danger')
        return redirect(url_for('login'))

    # Check if email already exists in the ServiceProfessional table
    existing_email = ServiceProfessional.query.filter_by(email=email).first()
    if existing_email:
        flash('This email is already registered. Please use a different one.', 'danger')
        return redirect(url_for('login'))

    # Check if phone already exists in the ServiceProfessional table
    existing_phone = ServiceProfessional.query.filter_by(phone=phone).first()
    if existing_phone:
        flash('This phone number is already registered. Please use a different one.', 'danger')
        return redirect(url_for('login'))


    # File upload logic (govt id file upload in the database as BLOB)
    if 'service-prof-govt-id-file' not in request.files:
        flash('No file part', 'danger')
        return redirect(request.url)

    file = request.files['service-prof-govt-id-file']
    if file.filename == '':
        flash('No selected file', 'danger')
        return redirect(request.url)

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file_data = file.read()  


        service_id_query = db.session.query(Service.id).filter_by(service_name=service_type).first()
        if not service_id_query:  
            flash('Invalid service type', 'danger')  
            return redirect(request.url)  

        service_id = service_id_query[0] 

    
        hashed_password = generate_password_hash(password)


        # Create a new service professional instance
        new_service_professional = ServiceProfessional(
            govt_id=govt_id,
            name=name,
            email=email,
            password=hashed_password,
            phone=phone,
            description=description,
            service_type=service_type,
            experience=experience,
            address=address,
            service_id=service_id,
            district=district,
            state=state, 
            country=country,
            pincode=pincode,
            govt_id_file=file_data  
        )

        
        db.session.add(new_service_professional)
        db.session.commit()

        return render_template('new_service_prof.html',username=name)
       
    else:
        flash('Invalid file type or file too large.', 'danger')
        return redirect(url_for('login'))
    
@app.route('/profile', methods=['GET'])
@auth_required
def profile():
    user_id = session['user_id']
    role = session['user_role']  
    
    
    if role == 'admin':
        user = Admin.query.get(user_id)
    elif role == 'customer':
        user = Customer.query.get(user_id)
    elif role == 'service_professional':
        user = ServiceProfessional.query.get(user_id)
    else:
        flash('Invalid role.', 'danger')
        return redirect(url_for('dashboard'))  

   
    return render_template('profile.html', user=user, role=role)



@app.route('/about_us')
def about_us():
    if 'user_id' in session:
        user_id = session['user_id']
        role = session['user_role']  
        
      
        if role == 'admin':
            user = Admin.query.get(user_id)
            
        elif role == 'customer':
            user = Customer.query.get(user_id)
            
        elif role == 'service_professional':
            user = ServiceProfessional.query.get(user_id)
            
        else:
            flash('Invalid role.', 'danger')
            return redirect(url_for('about_us.html'))  
        
        return render_template('about_us.html',user=user,role=role)
    return render_template('about_us.html')




@app.route('/services')
def services():

    #search query
    query = request.args.get('query', '').strip()
    if query:
        services_list = Service.query.filter(
            (Service.service_name.ilike(f"%{query}%")) 
        ).all()
    else:
        services_list = Service.query.all()
    
    return render_template('services.html', services=services_list)




@app.route('/service_management', methods=['GET'])
@auth_required
@admin_only
def service_management():
    user_id = session['user_id']
    role = session['user_role']
    user = None
    
    if role == 'admin':
        user = Admin.query.get(user_id)
    elif role == 'customer':
        user = Customer.query.get(user_id)
    elif role == 'service_professional':
        user = ServiceProfessional.query.get(user_id)
    
   
    query = request.args.get('query', '').strip().lower()
    if query:
        
    
        services = Service.query.filter(
            (Service.service_name.ilike(f"%{query}%")) |
            ((Service.service_status == True) if query == "active" else (Service.service_status == False) if query == "inactive" else False)
        ).all()
    else:
        
        services = Service.query.all()
    
    return render_template('service_management.html', services=services, user=user, role=role)


@app.route('/add_service', methods=['GET', 'POST'])
@auth_required
@admin_only
def add_service():
    user_id = session['user_id']
    role = session['user_role']
    
    if role == 'admin':
        user = Admin.query.get(user_id)
        
    elif role == 'customer':
        user = Customer.query.get(user_id)
        
    elif role == 'service_professional':
        user = ServiceProfessional.query.get(user_id)
    if request.method == 'POST':
        service_name = request.form['service_name']
        description = request.form['description']
        price = request.form['price']
        time_required = request.form['time_required']
        
        new_service = Service(service_name=service_name, description=description, price=price, time_required=time_required)
        db.session.add(new_service)
        db.session.commit()
        flash("Service added successfully!",'success')
        return redirect(url_for('service_management'))
    return render_template('add_service.html',user=user,role=role)


@app.route('/toggle_service_status/<int:service_id>')
@auth_required
@admin_only
def toggle_service_status(service_id):
    service = Service.query.get_or_404(service_id)
    service.service_status = not service.service_status
    db.session.commit()
    flash(f"Service {'activated' if service.service_status else 'deactivated'} successfully!",'warning')
    return redirect(url_for('service_management'))


@app.route('/delete_service/<int:service_id>')
@auth_required
@admin_only
def delete_service(service_id):
    service = Service.query.get_or_404(service_id)
    db.session.delete(service)
    db.session.commit()
    flash("Service deleted successfully!",'danger')
    return redirect(url_for('service_management'))
    

@app.route('/edit_service/<int:service_id>', methods=['GET', 'POST'])
@auth_required
@admin_only
def edit_service(service_id):
   
    service = Service.query.get_or_404(service_id)
    user_id = session['user_id']
    role = session['user_role']
   
    if role == 'admin':
        user = Admin.query.get(user_id)
        
    elif role == 'customer':
        user = Customer.query.get(user_id)
        
    elif role == 'service_professional':
        user = ServiceProfessional.query.get(user_id)
    if request.method == 'POST':
        
        service.service_name = request.form['service_name']
        service.description = request.form['description']
        service.price = request.form['price']
        service.time_required = request.form['time_required']

        try:
            db.session.commit()
            flash("Service updated successfully!", "success")
            return redirect(url_for('service_management'))
        except:
            db.session.rollback()
            flash("An error occurred. Try again.", "danger")

    return render_template('edit_service.html', service=service,user=user,role=role)


@app.route('/available-services', methods=['GET'])
@auth_required
@customer_only
def available_services():
    user_id = session['user_id']
    role = session['user_role']
    user = None
    
   
    if role == 'admin':
        user = Admin.query.get(user_id)
    elif role == 'customer':
        user = Customer.query.get(user_id)
    elif role == 'service_professional':
        user = ServiceProfessional.query.get(user_id)

   
    customer = Customer.query.get(user.id)
    if not customer:
        flash("Customer not found", "error")
        return redirect(url_for('home'))

    #search query
    query = request.args.get('query', '').strip().lower()

   
    services_query = Service.query.join(ServiceProfessional).filter(
        ServiceProfessional.active_status == True,
        ServiceProfessional.approve_status == True,
        ServiceProfessional.pincode == customer.pincode,
        Service.service_status == True
    )

    
    if query:
        if query == "active":
            services_query = services_query.filter(Service.service_status == True)
        elif query == "inactive":
            services_query = services_query.filter(Service.service_status == False)
        else:
            services_query = services_query.filter(Service.service_name.ilike(f"%{query}%"))

    
    services = services_query.all()

    # Calculate average ratings and retrieve comments for each service
    service_data = []
    for service in services:
        avg_rating = db.session.query(db.func.avg(Booking.rating)).filter(
            Booking.service_id == service.id,
            Booking.rating.isnot(None)
        ).scalar() or 0  

        # Fetch top 2 comments
        top_comments = db.session.query(Booking.comments, Booking.rating).filter(
            Booking.service_id == service.id,
            Booking.comments.isnot(None),
            Booking.status == "Completed"
        ).order_by(Booking.booking_time.desc()).limit(2).all()

        
        service_data.append({
            'service': service,
            'avg_rating': round(avg_rating, 2),
            'top_comments': top_comments
        })

    
    cart = session.get('cart', [])

    return render_template(
        'available_services.html',
        services=service_data,
        cart=cart,
        user=user,
        role=role
    )

@app.route('/add-to-cart/<int:service_id>')
@auth_required
@customer_only
def add_to_cart(service_id):
    
    cart = session.get('cart', [])
    if service_id not in cart:
        cart.append(service_id)
        session['cart'] = cart
        flash("Service added to cart", "success")
    else:
        flash("Service is already in your cart", "warning")
    return redirect(url_for('available_services'))


@app.route('/remove-from-cart/<int:service_id>')
@auth_required
@customer_only
def remove_from_cart(service_id):
    cart = session.get('cart', [])
    if service_id in cart:
        cart.remove(service_id)
        session['cart'] = cart
        flash("Service removed from cart", "success")
    else:
        flash("Service was not in your cart", "info")
    return redirect(url_for('available_services'))

@app.route('/view-cart', methods=['GET'])
@auth_required
@customer_only
def view_cart():
    user_id = session['user_id']
    role = session['user_role']
    
   
    if role == 'admin':
        user = Admin.query.get(user_id)
    elif role == 'customer':
        user = Customer.query.get(user_id)
    elif role == 'service_professional':
        user = ServiceProfessional.query.get(user_id)
    
    
    cart = session.get('cart', [])
    
    #search query
    query = request.args.get('query', '').strip().lower()
    
   
    services_query = Service.query.filter(Service.id.in_(cart))
    if query:
        services_query = services_query.filter(
            Service.service_name.ilike(f"%{query}%")
        )
    
    services = services_query.all()
    
    return render_template('cart.html', services=services, user=user, role=role, query=query)



@app.route('/checkout')
@auth_required
@customer_only
def checkout():
    user_id = session['user_id']
    role = session['user_role']
   
    if role == 'admin':
        user = Admin.query.get(user_id)
        
    elif role == 'customer':
        user = Customer.query.get(user_id)
        
    elif role == 'service_professional':
        user = ServiceProfessional.query.get(user_id)
    
    cart = session.get('cart', [])
    cart_services = Service.query.filter(Service.id.in_(cart)).all()
    total_price = sum(service.price for service in cart_services)
    total_time = sum(float(service.time_required) for service in cart_services)

    
    return render_template('checkout.html', cart_services=cart_services, total_price=total_price, total_time=total_time,user=user,role=role)


@app.route('/confirm_order', methods=['POST'])
@auth_required
@customer_only
def confirm_order():
    user_id = session['user_id']
    role = session['user_role']
    

    if role == 'admin':
        user = Admin.query.get(user_id)
    elif role == 'customer':
        user = Customer.query.get(user_id)
    elif role == 'service_professional':
        user = ServiceProfessional.query.get(user_id)
    
 
    if 'user_id' not in session:
        flash("Please log in to confirm your order.", "error")
        return redirect(url_for('login'))
    
    cart = session.get('cart', [])
    if not cart:
        flash("Your cart is empty.", "error")
        return redirect(url_for('view_cart'))

    # Create a booking entry for each service in the cart
    for service_id in cart:
        booking = Booking(
            customer_id=user_id,
            service_id=service_id,
            booking_time=datetime.now(),
            status='Pending'
        )
        db.session.add(booking)
    

    db.session.commit()


    session.pop('cart', None)
    

    flash("Your order has been successfully placed.", "success")
    return redirect(url_for('view_orders'))

@app.route('/view_orders', methods=['GET', 'POST'])
@auth_required
@customer_only
def view_orders():
    user_id = session.get('user_id')
    role = session.get('user_role')


    user = Customer.query.get(user_id) if role == 'customer' else None
    if not user:
        flash("Please log in to view your orders.", "error")
        return redirect(url_for('login'))

    # search query 
    search_query = request.args.get('query', '').strip()
    query_lower = f"%{search_query.lower()}%" if search_query else None


    pending_orders_query = Booking.query.filter_by(customer_id=user_id).filter(
        Booking.status.in_(['Pending', 'In Progress'])
    )
    
    completed_orders_query = Booking.query.filter_by(customer_id=user_id, status='Completed')
    
    cancelled_orders_query = Booking.query.filter_by(customer_id=user_id, status='Cancelled')


    if search_query:

        pending_orders_query = pending_orders_query.filter(
            (Booking.id.ilike(query_lower)) |
            (Booking.status.ilike(query_lower)) |
            (Booking.service_id.in_(
                Service.query.filter(Service.service_name.ilike(query_lower)).with_entities(Service.id)
            )) |
            (Booking.service_professional_id.in_(
                ServiceProfessional.query.filter(ServiceProfessional.name.ilike(query_lower)).with_entities(ServiceProfessional.id)
            ))
        )


        completed_orders_query = completed_orders_query.filter(
            (Booking.id.ilike(query_lower)) |
            (Booking.status.ilike(query_lower)) |
            (Booking.service_id.in_(
                Service.query.filter(Service.service_name.ilike(query_lower)).with_entities(Service.id)
            )) |
            (Booking.service_professional_id.in_(
                ServiceProfessional.query.filter(ServiceProfessional.name.ilike(query_lower)).with_entities(ServiceProfessional.id)
            ))
        )


        cancelled_orders_query = cancelled_orders_query.filter(
            (Booking.id.ilike(query_lower)) |
            (Booking.status.ilike(query_lower)) |
            (Booking.service_id.in_(
                Service.query.filter(Service.service_name.ilike(query_lower)).with_entities(Service.id)
            )) |
            (Booking.service_professional_id.in_(
                ServiceProfessional.query.filter(ServiceProfessional.name.ilike(query_lower)).with_entities(ServiceProfessional.id)
            ))
        )


    pending_orders = pending_orders_query.order_by(Booking.booking_time.desc()).all()
    completed_orders = completed_orders_query.order_by(Booking.booking_time.desc()).all()
    cancelled_orders = cancelled_orders_query.order_by(Booking.booking_time.desc()).all()


    for order in pending_orders + completed_orders + cancelled_orders:
        order.service_details = Service.query.get(order.service_id)
        order.service_professional_details = ServiceProfessional.query.get(order.service_professional_id)


    if request.method == 'POST':
        booking_id = request.form.get('booking_id')
        order = Booking.query.get(booking_id)
        if order and order.customer_id == user_id:
            order.rating = request.form.get('rating', type=float)
            order.comments = request.form.get('comments')
            order.flag = 'flag' in request.form
            db.session.commit()
            flash("Your feedback has been saved.", "success")
            return redirect(url_for('view_orders'))

    return render_template(
        'view_orders.html',
        pending_orders=pending_orders,
        completed_orders=completed_orders,
        cancelled_orders=cancelled_orders,
        user=user,
        role=role,
    )

@app.route('/complete_order/<int:order_id>', methods=['GET','POST'])
@auth_required
@customer_only
def complete_order(order_id):
    order = Booking.query.get_or_404(order_id)

    # Check if the logged-in user is the customer who placed the order
    if order.customer_id != session['user_id']:
        flash("Unauthorized access to this order.", "error")
        return redirect(url_for('view_orders'))

    # Mark the order as completed
    order.status = 'Completed'
    order.booking_end_time = datetime.utcnow()
    db.session.commit()
    flash("Order marked as completed.", "success")
    return redirect(url_for('view_orders'))


@app.route('/cancel_order/<int:order_id>', methods=['GET','POST'])
@auth_required
@customer_only
def cancel_order(order_id):
    order = Booking.query.get_or_404(order_id)

    # Check if the logged-in user is the customer who placed the order and the status is pending
    if order.customer_id != session['user_id'] or (order.status != 'Pending' and order.status != 'In Progress'):
        flash("You can only cancel pending orders.", "error")
        return redirect(url_for('view_orders'))

    # Cancel the order by updating its status
    order.status = 'Cancelled'
    db.session.commit()
    flash("Order has been cancelled.", "info")
    return redirect(url_for('view_orders'))


@app.route('/add_rating/<int:order_id>', methods=['POST'])
@auth_required
@customer_only
def add_rating(order_id):
    order = Booking.query.get_or_404(order_id)

    # Ensure the order is completed and belongs to the logged-in customer
    if order.customer_id != session['user_id'] or order.status != 'Completed':
        flash("You can only rate completed orders.", "error")
        return redirect(url_for('view_orders'))

    # Capture rating and comments from form data
    rating = request.form.get('rating')
    comments = request.form.get('comments')
    order.rating = float(rating) if rating else None
    order.comments = comments if comments else None

    db.session.commit()
    flash("Thank you for your feedback!", "success")
    return redirect(url_for('view_orders'))



@app.route('/update_flag/<int:order_id>', methods=['POST'])
@auth_required
@customer_only
def update_flag(order_id):
    user_id = session.get('user_id')
    order = Booking.query.get(order_id)

    if order and order.customer_id == user_id:
        # Get the associated service professional
        service_prof = ServiceProfessional.query.get(order.service_professional_id)

        # Retrieve the new flag status from the request data
        data = request.get_json()
        new_flag_status = data.get('flag', False)

        # Update flag status and adjust flag count if necessary
        if service_prof and new_flag_status != order.flag:  
            if new_flag_status:
                service_prof.flag_count = (service_prof.flag_count or 0) + 1  
            else:
                service_prof.flag_count = max((service_prof.flag_count or 1) - 1, 0)  

        # Update the order's flag status and commit changes
        order.flag = new_flag_status
        db.session.commit()

        return redirect(url_for('view_orders'))
    
    return redirect(url_for('view_orders'))

@app.route('/customer_summary')
@auth_required
@customer_only
def customer_summary():
    user_id = session['user_id']
    role = session['user_role']
    
    # Fetch user data based on role
    if role == 'admin':
        user = Admin.query.get(user_id)
    elif role == 'customer':
        user = Customer.query.get(user_id)
    elif role == 'service_professional':
        user = ServiceProfessional.query.get(user_id)
    customer_id = session.get('user_id')
    
    customer_id = session.get('user_id')  # Replace with actual user ID logic
    bookings = Booking.query.filter_by(customer_id=customer_id,status='Completed').all()
    
    service_names = []
    total_cost = 0

    # Monthly and yearly statistics
    monthly_cost = {}
    yearly_cost = {}

    for booking in bookings:
        service = Service.query.get(booking.service_id)
        if service:
            service_names.append(service.service_name)
            total_cost += service.price
            
            # Calculate monthly cost
            month = booking.booking_time.strftime("%Y-%m")
            monthly_cost[month] = monthly_cost.get(month, 0) + service.price
            
            # Calculate yearly cost
            year = booking.booking_time.year
            yearly_cost[year] = yearly_cost.get(year, 0) + service.price

    # Prepare data for rendering
    data = {
        'service_names': service_names,
        'total_cost': total_cost,
        'monthly_cost': monthly_cost,
        'yearly_cost': yearly_cost,
        'bookings': bookings
    }
    
    return render_template('customer_summary.html', data=data,user=user,role=role,Service=Service)

@app.route('/requests')
@auth_required
@service_professional_only
def requests():
    user_id = session['user_id']
    role = session['user_role']
    

    if role == 'admin':
        user = Admin.query.get(user_id)
    elif role == 'customer':
        user = Customer.query.get(user_id)
    elif role == 'service_professional':
        user = ServiceProfessional.query.get(user_id)
    
    service_type = ServiceProfessional.query.filter_by(id=user.id).first().service_type
    service_id = Service.query.filter_by(service_name=service_type).first().id


    in_progress_order = Booking.query.filter_by(
        service_professional_id=user_id, status='In Progress'
    ).first()
    
    # search query
    query = request.args.get('query', '').strip()
    query_lower = f"%{query.lower()}%" if query else None

 
    if query:
        service_ids_subquery = Service.query.filter(Service.service_name.ilike(query_lower)).with_entities(Service.id)
        service_professional_ids_subquery = ServiceProfessional.query.filter(
            (ServiceProfessional.name.ilike(query_lower)) |
            (ServiceProfessional.phone.ilike(query_lower)) |
            (ServiceProfessional.email.ilike(query_lower)) |
            (ServiceProfessional.address.ilike(query_lower)) |
            (cast(ServiceProfessional.pincode, String).ilike(query_lower))
        ).with_entities(ServiceProfessional.id)

        customer_ids_subquery = Customer.query.filter(
            (cast(Customer.pincode, String).ilike(query_lower)) |  
            (Customer.address.ilike(query_lower))  
        ).with_entities(Customer.id)

        available_orders = Booking.query.filter(
            Booking.status == 'Pending',
            (
                Booking.id.ilike(query_lower) |  
                Booking.service_id.in_(service_ids_subquery) |
                Booking.service_professional_id.in_(service_professional_ids_subquery) |
                Booking.customer_id.in_(customer_ids_subquery)  
            )
        ).all()
    else:
        available_orders = Booking.query.filter_by(status='Pending', service_id=service_id).all()


    orders_with_service_details = []
    for order in available_orders:
        service = Service.query.get(order.service_id)
        customer = Customer.query.get(order.customer_id)  
        
        orders_with_service_details.append({
            "order": order,
            "service_name": service.service_name if service else "Service Not Found",
            "service_description": service.description if service else "No Description Available",
            "customer_address": f"{customer.address}, {customer.country}, {customer.state}, {customer.district}, {customer.pincode}" if customer else "N/A"
        })

    # Process in-progress order details
    in_progress_service_details = None
    if in_progress_order:
        service = Service.query.get(in_progress_order.service_id)
        customer = Customer.query.get(in_progress_order.customer_id) 
        in_progress_service_details = {
            "order": in_progress_order,
            "service_name": service.service_name if service else "Service Not Found",
            "service_description": service.description if service else "No Description Available",
            "customer_name": customer.name if customer else "Customer Not Found",
            "customer_phone": customer.phone if customer else "N/A",
            "customer_address": f"{customer.address}, {customer.country}, {customer.state}, {customer.district}, {customer.pincode}" if customer else "N/A"
        }

    return render_template(
        'requests.html',
        available_orders=orders_with_service_details,
        in_progress_order=in_progress_service_details,
        user=user,
        role=role
    )


@app.route('/accept_order/<int:order_id>', methods=['POST'])
@auth_required
@service_professional_only
def accept_order(order_id):
    user_id = session.get('user_id')
    order = Booking.query.get_or_404(order_id)
    
    # Retrieve the service professional and customer information
    service_professional = ServiceProfessional.query.get(user_id)
    customer = Customer.query.get(order.customer_id)
    
    # Check if the service professional and customer are in the same pincode area
    if customer.pincode != service_professional.pincode:
        flash("This order is not available in your area.", "error")
        return redirect(url_for('requests'))
    
    # Check if the order is still pending
    if order.status != 'Pending':
        flash("This order is no longer available.", "error")
        return redirect(url_for('requests'))
    
    # Ensure the service professional has no other ongoing orders
    if Booking.query.filter_by(service_professional_id=user_id, status='Accepted').first():
        flash("Complete your current order before accepting another.", "error")
        return redirect(url_for('requests'))
    
    # Accept the order
    order.status = 'In Progress'
    order.service_professional_id = user_id
    db.session.commit()
    
    flash("Order accepted successfully!", "success")
    return redirect(url_for('requests'))


@app.route('/service_history')
def service_history():
    user_id = session['user_id']
    role = session['user_role']
    service_professional_id = session.get('user_id')
    query_lower = request.args.get('query', '').strip().lower()
    
    
    if role == 'admin':
        user = Admin.query.get(user_id)
    elif role == 'customer':
        user = Customer.query.get(user_id)
    elif role == 'service_professional':
        user = ServiceProfessional.query.get(user_id)

   
    bookings = Booking.query.filter_by(service_professional_id=service_professional_id)
    
   
    if query_lower:
        bookings = bookings.filter(
            (Booking.id.like(f"%{query_lower}%")) |
            (Booking.customer_id.like(f"%{query_lower}%")) |
            (Booking.booking_time.like(f"%{query_lower}%")) |
            (Booking.booking_end_time.like(f"%{query_lower}%"))|
            (Booking.status.like(f"%{query_lower}%"))
        )


    in_progress_bookings = bookings.filter(Booking.status == 'In Progress').order_by(Booking.booking_time.desc()).all()
    history_bookings = bookings.filter(Booking.status.in_(['Completed', 'Cancelled'])).order_by(Booking.booking_time.desc()).all()


    total_completed_count = bookings.filter(Booking.status == 'Completed').count()
    total_cancelled_count = bookings.filter(Booking.status == 'Cancelled').count()

    return render_template(
        'service_history.html',
        in_progress_bookings=in_progress_bookings,
        history_bookings=history_bookings,
        total_cancelled_count=total_cancelled_count,
        total_completed_count=total_completed_count,
        user=user,
        role=role,
        search_query=query_lower
    )


@app.route('/update_flag_service/<int:booking_id>', methods=['GET','POST'])
@auth_required
def update_flag_service(booking_id):
    

    user_id = session.get('user_id')
    order = Booking.query.get(booking_id)
   
    
    if order and order.service_professional_id == user_id:
        
        customer = Customer.query.get(order.customer_id)
        if not customer:
            flash('Customer not found.', 'error')
            return redirect(url_for('service_history'))

        data = request.get_json()
        new_flag_status = data.get('flag', False)
        
        # Adjust the flag count based on the change in flag status
        if new_flag_status != order.flag_customer: 
            if new_flag_status:
                customer.flag_count += 1 
            else:
                customer.flag_count -= 1  

        # Update the order flag status
        order.flag_customer = new_flag_status
        db.session.commit()
        return redirect(url_for('service_history'))
    return redirect(url_for('service_history'))

@app.route('/service_professional_summary')
@auth_required
@service_professional_only
def service_professional_summary():
    user_id = session['user_id']
    role = session['user_role']
    
    # Fetch user data based on role
    if role == 'admin':
        user = Admin.query.get(user_id)
    elif role == 'customer':
        user = Customer.query.get(user_id)
    elif role == 'service_professional':
        user = ServiceProfessional.query.get(user_id)

    # Fetch bookings for the service professional
    bookings = Booking.query.filter_by(service_professional_id=user_id).all()
    
    # Initialize statistics
    total_completed_count = 0
    total_cancelled_count = 0
    total_earnings = 0

    monthly_earnings = {}
    yearly_earnings = {}
    yearly_orders = {}

    # Calculate statistics
    for booking in bookings:
        service = Service.query.get(booking.service_id)
        year = booking.booking_time.year
        
        # Initialize yearly orders if not present
        if year not in yearly_orders:
            yearly_orders[year] = {'confirmed': 0, 'cancelled': 0}
        
        if booking.status == 'Completed':
            total_completed_count += 1
            yearly_orders[year]['confirmed'] += 1  # Count confirmed orders
            
            if service:
                total_earnings += service.price

                # Calculate monthly earnings
                month = booking.booking_time.strftime("%Y-%m")
                monthly_earnings[month] = monthly_earnings.get(month, 0) + service.price

                # Calculate yearly earnings
                yearly_earnings[year] = yearly_earnings.get(year, 0) + service.price

        elif booking.status == 'Cancelled':
            total_cancelled_count += 1
            yearly_orders[year]['cancelled'] += 1  # Count cancelled orders

    # Prepare data for rendering
    data = {
        'total_completed_count': total_completed_count,
        'total_cancelled_count': total_cancelled_count,
        'total_earnings': total_earnings,
        'monthly_earnings': monthly_earnings,
        'yearly_earnings': yearly_earnings,
        'yearly_orders': yearly_orders,  
    }



    return render_template('service_professional_summary.html', data=data, user=user, role=role)






@app.route('/service_professionals')
@auth_required
@admin_only
def service_professionals():
    user_id = session['user_id']
    role = session['user_role']

  
    if role == 'admin':
        user = Admin.query.get(user_id)
    elif role == 'customer':
        user = Customer.query.get(user_id)
    elif role == 'service_professional':
        user = ServiceProfessional.query.get(user_id)

    # search query
    query = request.args.get('query', '').strip()
    query_lower = f"%{query.lower()}%" if query else None

    if query:

        active_profs = ServiceProfessional.query.filter(
            ServiceProfessional.active_status == True,
            ServiceProfessional.name.ilike(query_lower) |
            ServiceProfessional.phone.ilike(query_lower) |
            ServiceProfessional.email.ilike(query_lower) |
            ServiceProfessional.address.ilike(query_lower) |
            cast(ServiceProfessional.pincode, String).ilike(query_lower) |
            cast(ServiceProfessional.flag_count, String).ilike(query_lower)
        ).all()

        blocked_profs = ServiceProfessional.query.filter(
            ServiceProfessional.active_status == False,
            ServiceProfessional.approve_status == True,
            ServiceProfessional.name.ilike(query_lower) |
            ServiceProfessional.phone.ilike(query_lower) |
            ServiceProfessional.email.ilike(query_lower) |
            ServiceProfessional.address.ilike(query_lower) |
            cast(ServiceProfessional.pincode, String).ilike(query_lower) |
            cast(ServiceProfessional.flag_count, String).ilike(query_lower)
        ).all()

        suspicious_profs = ServiceProfessional.query.filter(
            ServiceProfessional.flag_count >= 5,
            ServiceProfessional.name.ilike(query_lower) |
            ServiceProfessional.phone.ilike(query_lower) |
            ServiceProfessional.email.ilike(query_lower) |
            ServiceProfessional.address.ilike(query_lower) |
            cast(ServiceProfessional.pincode, String).ilike(query_lower) |
            cast(ServiceProfessional.flag_count, String).ilike(query_lower)
        ).all()

        new_reg_profs = ServiceProfessional.query.filter(
            ServiceProfessional.approve_status == False,
            ServiceProfessional.name.ilike(query_lower) |
            ServiceProfessional.phone.ilike(query_lower) |
            ServiceProfessional.email.ilike(query_lower) |
            ServiceProfessional.address.ilike(query_lower) |
            cast(ServiceProfessional.pincode, String).ilike(query_lower) |
            cast(ServiceProfessional.flag_count, String).ilike(query_lower)
        ).all()
    else:
 
        active_profs = ServiceProfessional.query.filter_by(active_status=True).all()
        blocked_profs = ServiceProfessional.query.filter(ServiceProfessional.active_status == False, ServiceProfessional.approve_status == True).all()
        suspicious_profs = ServiceProfessional.query.filter(ServiceProfessional.flag_count >= 5).all()
        new_reg_profs = ServiceProfessional.query.filter_by(approve_status=False).all()

    return render_template('service_professionals.html', active_profs=active_profs,
                           blocked_profs=blocked_profs, suspicious_profs=suspicious_profs,
                           new_reg_profs=new_reg_profs, user=user, role=role)



@app.route('/service_professional/<int:id>/view')
@auth_required
@admin_only
def service_professional_view(id):
    user_id = session['user_id']
    role = session['user_role']
    
    # Fetch user data
    user = (
        Admin.query.get(user_id) if role == 'admin' 
        else Customer.query.get(user_id) if role == 'customer' 
        else ServiceProfessional.query.get(user_id)
    )

    # Retrieve service professional data
    prof = ServiceProfessional.query.get_or_404(id)
    
    # Calculate total flags on bookings flagged for this service professional
    total_flags = Booking.query.filter_by(service_professional_id=id, flag=True).count()

    # Calculate average rating using SQL function
    avg_rating = db.session.query(func.avg(Booking.rating)).filter(
        Booking.service_professional_id == id,
        Booking.rating.isnot(None)
    ).scalar() or 0 

    # Fetch top 2 comments and ratings
    top_comments = (
        db.session.query(Booking.comments, Booking.rating)
        .filter(
            Booking.service_professional_id == id,
            Booking.comments.isnot(None),
            Booking.status == "Completed"
        )
        .order_by(Booking.booking_time.desc())
        .limit(2)
        .all()
    )

    return render_template(
        'service_professional_view.html', 
        prof=prof, 
        total_flags=total_flags, 
        avg_rating=round(avg_rating, 2), 
        top_comments=top_comments,
        user=user, 
        role=role
    )

@app.route('/service_professional/<int:id>/approve', methods=['POST'])
@auth_required
@admin_only
def approve_professional(id):
    prof = ServiceProfessional.query.get_or_404(id)
    prof.approve_status = True
    prof.active_status = True
    db.session.commit()
    flash("Service professional approved and activated.", "success")
    return redirect(url_for('service_professionals'))

@app.route('/service_professional/<int:id>/activate', methods=['POST'])
@auth_required
@admin_only
def activate_professional(id):
    prof = ServiceProfessional.query.get_or_404(id)
    prof.active_status = True
    db.session.commit()
    flash("Service professional activated.", "success")
    return redirect(url_for('service_professionals'))

@app.route('/service_professional/<int:id>/deactivate', methods=['POST'])
@auth_required
@admin_only
def deactivate_professional(id):
    prof = ServiceProfessional.query.get_or_404(id)
    prof.active_status = False
    db.session.commit()
    flash("Service professional deactivated.", "success")
    return redirect(url_for('service_professionals'))

@app.route('/service_professional/<int:id>/delete', methods=['POST'])
@auth_required
@admin_only
def delete_professional(id):
    prof = ServiceProfessional.query.get_or_404(id)
    db.session.delete(prof)
    db.session.commit()
    flash("Service professional deleted.", "success")
    return redirect(url_for('service_professionals'))

@app.route('/service_professional/<int:id>/download_govt_id', methods=['GET'])
@auth_required
@admin_only
def download_govt_id(id):
    prof = ServiceProfessional.query.get_or_404(id)
    if prof.govt_id_file:
        return send_file(BytesIO(prof.govt_id_file), as_attachment=True, download_name=f"{prof.name}_govt_id.pdf")
    flash("No government ID file available.", "error")
    return redirect(url_for('service_professional_view', id=id))

@app.route('/customers')
@auth_required
@admin_only
def customers():
    user_id = session['user_id']
    role = session['user_role']
    

    user = (
        Admin.query.get(user_id) if role == 'admin' 
        else Customer.query.get(user_id) if role == 'customer' 
        else ServiceProfessional.query.get(user_id)
    )

    # search query 
    query = request.args.get('query', '').strip()
    query_lower = f"%{query.lower()}%" if query else None

  
    if query:
     
        active_customers = Customer.query.filter(
            Customer.active_status == True,
            (Customer.name.ilike(query_lower) |
             cast(Customer.id, String).ilike(query_lower) |
             Customer.phone.ilike(query_lower) |
             Customer.email.ilike(query_lower) |
             Customer.address.ilike(query_lower) |
             cast(Customer.pincode, String).ilike(query_lower) |
             cast(Customer.flag_count, String).ilike(query_lower))
        ).all()


        blocked_customers = Customer.query.filter(
            Customer.active_status == False,
            (Customer.name.ilike(query_lower) |
             cast(Customer.id, String).ilike(query_lower) |
             Customer.phone.ilike(query_lower) |
             Customer.email.ilike(query_lower) |
             Customer.address.ilike(query_lower) |
             cast(Customer.pincode, String).ilike(query_lower) |
             cast(Customer.flag_count, String).ilike(query_lower))
        ).all()

     
        suspicious_customers = Customer.query.filter(
            Customer.flag_count > 5,
            (Customer.name.ilike(query_lower) |
             cast(Customer.id, String).ilike(query_lower) |
             Customer.phone.ilike(query_lower) |
             Customer.email.ilike(query_lower) |
             Customer.address.ilike(query_lower) |
             cast(Customer.pincode, String).ilike(query_lower) |
             cast(Customer.flag_count, String).ilike(query_lower))
        ).all()
    else:
    
        active_customers = Customer.query.filter(Customer.active_status == True).all()
        blocked_customers = Customer.query.filter(Customer.active_status == False).all()
        suspicious_customers = Customer.query.filter(Customer.flag_count > 5).all()

    return render_template(
        'customers.html', 
        active_customers=active_customers, 
        blocked_customers=blocked_customers, 
        suspicious_customers=suspicious_customers,
        role=role,
        user=user
    )


@app.route('/customer/<int:id>/view')
@auth_required
@admin_only
def customer_view(id):
    user_id = session['user_id']
    role = session['user_role']
    customer = Customer.query.get_or_404(id)
     # Calculate total flags on bookings flagged by the customer
    total_flags = Booking.query.filter_by(customer_id=id, flag_customer=True).count()

    user = (
        Admin.query.get(user_id) if role == 'admin' 
        else Customer.query.get(user_id) if role == 'customer' 
        else ServiceProfessional.query.get(user_id)
    )
    customer = Customer.query.get_or_404(id)
    return render_template('customer_view.html', customer=customer,user=user,total_flags=total_flags,role=role)

@app.route('/customer/<int:id>/activate', methods=['POST'])
@auth_required
@admin_only
def activate_customer(id):
    customer = Customer.query.get_or_404(id)
    customer.active_status = True
    customer.flag_count = 0  # Reset flag count on activation
    db.session.commit()
    flash(f"Customer activated successfully!",'success')
    return redirect(url_for('customers'))

@app.route('/customer/<int:id>/deactivate', methods=['POST'])
@auth_required
@admin_only
def deactivate_customer(id):
    customer = Customer.query.get_or_404(id)
    customer.active_status = False
    db.session.commit()
    flash(f"Customer deactivated successfully!",'danger')
    return redirect(url_for('customers'))

@app.route('/customer/<int:id>/delete', methods=['POST'])
@auth_required
@admin_only
def delete_customer(id):
    customer = Customer.query.get_or_404(id)
    db.session.delete(customer)
    db.session.commit()
    flash("Customer deleted successfully!",'danger')
    return redirect(url_for('customers'))


@app.route('/orders')
@auth_required
@admin_only
def orders():
    user_id = session['user_id']
    role = session['user_role']
    
  
    user = (
        Admin.query.get(user_id) if role == 'admin' 
        else Customer.query.get(user_id) if role == 'customer' 
        else ServiceProfessional.query.get(user_id)
    )
    
    # search query
    query = request.args.get('query', '').strip()
    query_lower = f"%{query.lower()}%" if query else None
    

    if query:

        pending_orders = Booking.query.join(Customer).join(ServiceProfessional).join(Service).filter(
            Booking.status == 'Pending',
            (cast(Booking.id, String).ilike(query_lower) |
             Customer.name.ilike(query_lower) |
             cast(Booking.customer_id, String).ilike(query_lower) |
             ServiceProfessional.name.ilike(query_lower) |
             cast(Booking.service_professional_id, String).ilike(query_lower) |
             Service.service_name.ilike(query_lower) |
             cast(Booking.booking_time, String).ilike(query_lower) |
             Customer.address.ilike(query_lower) |
             cast(Customer.pincode, String).ilike(query_lower))
        ).order_by(Booking.booking_time.desc()).all()


        inprogress_orders = Booking.query.join(Customer).join(ServiceProfessional).join(Service).filter(
            Booking.status == 'In Progress',
            (cast(Booking.id, String).ilike(query_lower) |
             Customer.name.ilike(query_lower) |
             cast(Booking.customer_id, String).ilike(query_lower) |
             ServiceProfessional.name.ilike(query_lower) |
             cast(Booking.service_professional_id, String).ilike(query_lower) |
             Service.service_name.ilike(query_lower) |
             cast(Booking.booking_time, String).ilike(query_lower) |
             Customer.address.ilike(query_lower) |
             cast(Customer.pincode, String).ilike(query_lower))
        ).order_by(Booking.booking_time.desc()).all()


        completed_orders = Booking.query.join(Customer).join(ServiceProfessional).join(Service).filter(
            Booking.status == 'Completed',
            (cast(Booking.id, String).ilike(query_lower) |
             Customer.name.ilike(query_lower) |
             cast(Booking.customer_id, String).ilike(query_lower) |
             ServiceProfessional.name.ilike(query_lower) |
             cast(Booking.service_professional_id, String).ilike(query_lower) |
             Service.service_name.ilike(query_lower) |
             cast(Booking.booking_time, String).ilike(query_lower) |
             Customer.address.ilike(query_lower) |
             cast(Customer.pincode, String).ilike(query_lower))
        ).order_by(Booking.booking_time.desc()).all()


        cancelled_orders = Booking.query.join(Customer).join(ServiceProfessional).join(Service).filter(
            Booking.status == 'Cancelled',
            (cast(Booking.id, String).ilike(query_lower) |
             Customer.name.ilike(query_lower) |
             cast(Booking.customer_id, String).ilike(query_lower) |
             ServiceProfessional.name.ilike(query_lower) |
             cast(Booking.service_professional_id, String).ilike(query_lower) |
             Service.service_name.ilike(query_lower) |
             cast(Booking.booking_time, String).ilike(query_lower) |
             Customer.address.ilike(query_lower) |
             cast(Customer.pincode, String).ilike(query_lower))
        ).order_by(Booking.booking_time.desc()).all()
    else:

        pending_orders = Booking.query.filter_by(status='Pending').order_by(
            Booking.booking_time.desc()
        ).all()
        inprogress_orders = Booking.query.filter_by(status='In Progress').order_by(
            Booking.booking_time.desc()
        ).all()
        completed_orders = Booking.query.filter_by(status='Completed').order_by(
            Booking.booking_time.desc()
        ).all()
        cancelled_orders = Booking.query.filter_by(status='Cancelled').order_by(
            Booking.booking_time.desc()
        ).all()
    
    return render_template(
        'orders.html', 
        pending_orders=pending_orders,
        cancelled_orders=cancelled_orders,
        inprogress_orders=inprogress_orders,
        completed_orders=completed_orders,
        role=role, user=user
    )

@app.route('/order/<int:id>/view')
@auth_required
@admin_only
def order_view(id):
    user_id = session['user_id']
    role = session['user_role']
    

    order = Booking.query.get_or_404(id)
    
   
    user = (
        Admin.query.get(user_id) if role == 'admin' 
        else Customer.query.get(user_id) if role == 'customer' 
        else ServiceProfessional.query.get(user_id)
    )
    
    return render_template(
        'order_view.html',
        order=order,
        user=user,
        role=role
    )


@app.route('/order/<int:id>/delete', methods=['POST'])
@auth_required
@admin_only
def delete_order_admin(id):
    booking = Booking.query.get_or_404(id)
    
    
    
    db.session.delete(booking)
    db.session.commit()
    flash(f"Order deleted successfully!",'danger')
    return redirect(url_for('orders')) 

@app.route('/order/<int:id>/cancel', methods=['POST'])
@auth_required
@admin_only
def cancel_order_admin(id):
    booking = Booking.query.get_or_404(id)
    
   
    booking.status = 'Cancelled'
    db.session.commit()
    flash("Order Cancelled successfully!",'danger')
    return redirect(url_for('orders')) 

@app.route('/admin_summary')
@auth_required
@admin_only
def admin_summary():

    user_id = session['user_id']
    role = session['user_role']
    
  
    

    user = (
        Admin.query.get(user_id) if role == 'admin' 
        else Customer.query.get(user_id) if role == 'customer' 
        else ServiceProfessional.query.get(user_id)
    )

    # Calculate total revenue from completed bookings for the current year
    total_revenue = (
        db.session.query(db.func.sum(Service.price))
        .join(Booking)
        .filter(Booking.status == 'Completed')
        .scalar() or 0
    )

    # Calculate total yearly revenue for the current year from completed bookings
    current_year = datetime.now().year
    total_yearly_revenue = (
        db.session.query(db.func.sum(Service.price))
        .join(Booking)
        .filter(
            db.extract('year', Booking.booking_time) == current_year,
            Booking.status == 'Completed'
        )
        .scalar() or 0
    )

    # Calculate monthly revenue for the current year
    monthly_revenue = []
    for month in range(1, 13):  
        revenue = (
            db.session.query(db.func.sum(Service.price))
            .join(Booking)
            .filter(
                db.extract('year', Booking.booking_time) == current_year,
                db.extract('month', Booking.booking_time) == month,
                Booking.status == 'Completed'
            )
            .scalar() or 0
        )
        monthly_revenue.append(revenue)

    # Revenue per service from completed bookings
    service_revenue = (
        db.session.query(Service.service_name, db.func.sum(Service.price))
        .join(Booking)
        .filter(Booking.status == 'Completed')
        .group_by(Service.id)
        .all()
    )

    # New Joinees - Service professionals who joined in the last 30 days
    thirty_days_ago = datetime.now() - timedelta(days=30)
    new_joinees = (
        db.session.query(ServiceProfessional)
        .filter(ServiceProfessional.date_created >= thirty_days_ago)
        .all()
    )

    # New Services - Services added in the last 30 days
    new_services = (
        db.session.query(Service)
        .filter(Service.date_created >= thirty_days_ago)
        .all()
    )

    new_customers = (
        db.session.query(Customer)
        .filter(Customer.date_created >= thirty_days_ago)
        .all()
    )

    return render_template(
        'admin_summary.html',
        total_revenue=total_revenue,
        total_yearly_revenue=total_yearly_revenue,
        monthly_revenue=monthly_revenue,
        service_revenue=service_revenue,
        new_joinees=new_joinees,
        new_services=new_services,
        new_customers=new_customers,role=role,user=user
    )

@app.route('/change_password', methods=['GET', 'POST'])
@auth_required  
def change_password():
    user_id = session['user_id']
    role = session['user_role']
    
    user = (
        Admin.query.get(user_id) if role == 'admin' 
        else Customer.query.get(user_id) if role == 'customer' 
        else ServiceProfessional.query.get(user_id)
    )

    if request.method == 'POST':
        new_password = request.form['new_password']
        confirm_password = request.form['confirm_new_password']

        if new_password != confirm_password:
            flash('New password and confirm password do not match.', 'danger')
            return redirect(url_for('change_password'))

        if role == 'admin':
            secret_key = request.form.get('secret_key')
            if not secret_key or not check_password_hash(user.secret_key, secret_key):
                flash('Invalid secret key or user not authorized.', 'danger')
                return redirect(url_for('change_password'))
        
      
        hashed_password = generate_password_hash(new_password)
        user.password = hashed_password
        db.session.commit()
        flash('Password changed successfully.', 'success')
        return redirect(url_for('profile', role=role)) 

    return render_template('change_password.html', role=role, user=user) 



@app.route('/edit_profile', methods=['GET', 'POST'])
@auth_required
def edit_profile():
    user_id = session.get('user_id')
    role = session.get('user_role')
    
    if role == 'admin':
        user = Admin.query.get(user_id)
    elif role == 'customer':
        user = Customer.query.get(user_id)
    elif role == 'service_professional':
        user = ServiceProfessional.query.get(user_id)
    else:
        flash("Invalid user role.", "danger")
        return redirect(url_for('profile'))
    
    if request.method == 'POST':
        new_email = request.form.get('email')
        new_phone = request.form.get('phone') if role in ['customer', 'service_professional'] else None
        
        existing_user_email = (
            Customer.query.filter_by(email=new_email).first() or 
            ServiceProfessional.query.filter_by(email=new_email).first() or 
            Admin.query.filter_by(email=new_email).first()
        )
        
        if existing_user_email and existing_user_email.id != user.id:
            flash('Email already in use. Please choose a different one.', 'danger')
            return redirect(url_for('edit_profile'))

        if new_phone:
            existing_user_phone = (
                Customer.query.filter_by(phone=new_phone).first() or 
                ServiceProfessional.query.filter_by(phone=new_phone).first()
            )
            
            if existing_user_phone and existing_user_phone.id != user.id:
                flash('Phone number already in use. Please choose a different one.', 'danger')
                return redirect(url_for('edit_profile'))

        user.name = request.form.get('name')
        user.email = new_email

        if role in ['customer', 'service_professional']:
            user.address = request.form.get('address')
            user.phone = new_phone

        if role == 'service_professional':
            user.experience = request.form.get('experience')
            user.description = request.form.get('description')

        db.session.commit()
        flash('Profile updated successfully!', 'success')
        return redirect(url_for('profile'))

    return render_template('edit_profile.html', user=user, role=role)


#Service Prof can download govt id file which he uploaded
@app.route('/<int:id>/download_govt_id', methods=['GET','POST'])
@auth_required
@service_professional_only
def download_service_professional_govt_id(id):
    prof = ServiceProfessional.query.get_or_404(id)
    
    #Download the govt id file
    if prof.govt_id_file:
        return send_file(BytesIO(prof.govt_id_file), as_attachment=True, download_name=f"{prof.name}_govt_id.pdf")
    

    flash("No government ID file available.", "error")
    return redirect(url_for('edit_profile'))
