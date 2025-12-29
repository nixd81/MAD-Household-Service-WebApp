
from flask_sqlalchemy import SQLAlchemy
from flask import Flask, render_template, request, redirect, send_from_directory, url_for, flash, session
from datetime import datetime
import os
from werkzeug.security import check_password_hash, generate_password_hash
from flask_login import LoginManager, UserMixin, login_user, login_required, current_user, logout_user
from sqlalchemy import Column, Integer, String, Float
from datetime import datetime, timezone
from werkzeug.utils import secure_filename
import pytz

UPLOAD_FOLDER = os.path.join(os.getcwd(), 'resumes')  

app = Flask(__name__)

base_dir = os.path.abspath(os.path.dirname(__file__)) 
app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{os.path.join(base_dir, 'app.db')}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'NirmitD'  
db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Admin model
class Admin(db.Model):
    __tablename__ = 'admin'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True)
    password = db.Column(db.String(50))

# Customer model
class Customer(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True)
    password = db.Column(db.String(150))
    location = db.Column(db.String(150))
    phone_number=db.Column(db.String(10))

# ServiceProfessional model
class ServiceProfessional(UserMixin,db.Model):
    __tablename__ = 'service_professional'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50))
    password = db.Column(db.String(150))
    service_type = db.Column(db.String(50))
    experience = db.Column(db.Integer)
   
    service_requests = db.relationship('ServiceRequest', backref='professional', lazy=True)
    phone_number=db.Column(db.String(10))
    pdf = db.Column(db.String(120))
    remark = db.Column(db.String(500), nullable=True)  
    rating = db.Column(db.Float, nullable=True)  

# Service model
class Service(db.Model):
    __tablename__ = 'service'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50))
    description = db.Column(db.String(200))
    price = db.Column(db.Integer)  
  
# ServiceRequest model
class ServiceRequest(db.Model):
    __tablename__ = 'service_request'
    id = db.Column(db.Integer, primary_key=True)
    service_id = db.Column(db.Integer, db.ForeignKey('service.id'))
    customer_id = db.Column(db.Integer, db.ForeignKey('customer.id'))
    professional_id = db.Column(db.Integer, db.ForeignKey('service_professional.id'))
    date_of_request = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    date_of_completion = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    service_status = db.Column(db.String(20),  default='requested')
    remarks = db.Column(db.String(200))
   
    customer = db.relationship('Customer', backref='service_requests')
    service = db.relationship('Service', backref='service_requests')
 

#Model to store accepted request
class AcceptedRequest(db.Model):
    __tablename__ = 'accepted_request'
    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('customer.id'))
    professional_id = db.Column(db.Integer, db.ForeignKey('service_professional.id'))
    service_id = db.Column(db.Integer, db.ForeignKey('service.id'))
    date_accepted = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

#Model to store remark and ratings
class Rating(db.Model):
    __tablename__ = 'rating'
    id = db.Column(db.Integer, primary_key=True)
    professional_username = db.Column(db.String(50), nullable=False)
    professional_id = db.Column(db.Integer, db.ForeignKey('service_professional.id'), nullable=False)
    service_request_id = db.Column(db.Integer, db.ForeignKey('service_request.id'), nullable=False)
    rating = db.Column(db.Integer, nullable=True)  
    remark = db.Column(db.String(500), nullable=True)
    date_of_rating = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships
    professional = db.relationship('ServiceProfessional', backref='ratings', lazy=True)
    service_request = db.relationship('ServiceRequest', backref='ratings', lazy=True)


@app.route('/')
def index():
    return render_template('index.html')


@login_manager.user_loader
def load_user(user_id):
    
    role = session.get('role')

    if role == 'customer':
        return Customer.query.get(int(user_id))
    elif role == 'professional':
        return ServiceProfessional.query.get(int(user_id))

    return None  




#CUSTOMERS

#customer login(shown by login.html...leads to customer_homepage.html)
@app.route('/login/customer', methods=['GET', 'POST'])
def customer_login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        user = Customer.query.filter_by(username=username).first()

        if user and check_password_hash(user.password, password):  # Verify the password
            login_user(user)
            session['role'] = 'customer'  
            
            return redirect(url_for('customer_homepage'))  
        

    return render_template('login.html', role='customer')

#Customer Registration page
@app.route('/register/customer', methods=['GET', 'POST'])
def customer_register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        location = request.form['location']
        phone_number = request.form['phone_number']
        existing_user = Customer.query.filter_by(username=username).first()
        if existing_user:
            flash('Username already exists. Please choose a different one.', 'danger')
            return redirect(url_for('customer_register'))

        hashed_password = generate_password_hash(password, method='pbkdf2:sha256')
        new_customer = Customer(username=username, password=hashed_password, location=location, phone_number=phone_number)
        db.session.add(new_customer)
        db.session.commit()
        flash('Registration successful! Please log in.', 'success')
        return redirect(url_for('customer_login'))

    return render_template('customer_registration.html')



#shown by custommer_hompage.html
# Customer Homepage Route
@app.route('/customer_homepage', methods=['GET', 'POST'])
@login_required
def customer_homepage():
        
        distinct_service_names = db.session.query(Service.name).distinct().all()
        services = [service[0] for service in distinct_service_names]  
        search_query = request.args.get('search', '').strip().lower()
        
        if search_query:
            services = [service for service in services if search_query in service.lower()]
        return render_template('customer_homepage.html', customer=current_user, services=services)


#leads to index.html
@app.route('/logout/customer')
@login_required
def customer_logout():
    session.pop('role', None)  
    logout_user()
    flash("Logged out successfully.", "success")
    return redirect(url_for('index'))

    

@app.route('/home')
@login_required
def home():
    return render_template('customer_homepage.html', customer=current_user)

@app.route('/chat_with_professional')
@login_required
def chat_with_professional():
    return render_template('chat_with_professional.html', customer=current_user)



@app.route('/customer_summary/<int:customer_id>')
@login_required
def customer_summary(customer_id):
    
    service_requests = (
        db.session.query(ServiceRequest)
        .filter_by(customer_id=customer_id)
        .join(ServiceProfessional, ServiceRequest.professional_id == ServiceProfessional.id)
        .join(Service, ServiceRequest.service_id == Service.id)
        .add_columns(
            Service.name.label("service_name"),
            Service.description.label("service_description"),
            ServiceProfessional.username.label("professional_name"),
            ServiceProfessional.phone_number.label("professional_phone"),
            ServiceRequest.service_status.label("status"),
            ServiceRequest.date_of_request.label("request_date"),
            ServiceRequest.date_of_completion.label("completion_date"),
        )
        .all()
    )

    customer = Customer.query.get(customer_id)  

    return render_template(
        'customer_summary.html',
        customer=customer,
        service_requests=service_requests
    )


@app.route('/search_services')
@login_required
def customer_search():
    return render_template('customer_search.html', customer=current_user)


#Page for editing customer details
@app.route('/edit_profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
   # Fetch current customer details
    customer = Customer.query.filter_by(id=current_user.id).first()

    if request.method == 'POST':
        
        
        new_username = request.form.get('username')
        new_location = request.form.get('location')
        new_phone = request.form.get('phone_number')
        new_password = request.form.get('password')

        try:
            
            if new_username and new_username != customer.username:
                customer.username = new_username
                print("Updated Username:", new_username)

            if new_location and new_location != customer.location:
                customer.location = new_location
                print("Updated location:", new_location)

            if new_phone and new_phone != customer.phone_number:
                customer.phone_number = new_phone
                print("Updated Phone:", new_phone)

            if new_password:  
                hashed_password = generate_password_hash(new_password, method='pbkdf2:sha256')
                customer.password = hashed_password
                print("Password Updated")

            db.session.commit()
            flash('Profile updated successfully!', 'success')

        except Exception as e:
            print("Error updating profile:", e)
            db.session.rollback()
            flash('Error updating profile. Please try again.', 'danger')

       
        return redirect(url_for('customer_homepage'))

    
    return render_template('customeredit_profile.html', customer=customer)



#CUSTOMER END

#admin

#shown by admin_login.html leads to admin_homapage
@app.route('/login/admin', methods=['GET', 'POST'])
def admin_login():
    if request.method == "POST":
        username = request.form['username']
        password = request.form['password']

        
        if username == "N" and password == "D":
            session['admin_logged_in'] = True  
            flash("Admin login successful!", "success")
            return redirect(url_for('admin_homepage'))
        else:
            flash("Invalid credentials. Please try again.", "danger")

    return render_template('admin_login.html', role='admin')

#shown by admin_homepage.html...shows details of top 3 customers, services and professional
@app.route('/admin_homepage')
def admin_homepage():
    customers = Customer.query.order_by(Customer.id.desc()).limit(3).all()  
    services=Service.query.order_by(Service.id.desc()).limit(3).all()
    prof=ServiceProfessional.query.order_by(ServiceProfessional.id.desc()).limit(3).all()
    return render_template('admin_homepage.html', customers=customers,services=services,prof=prof)

#takes prof_id from admin_homepage.html and deletes them from the database sericeProfessional
@app.route('/delete_professional/<int:prof_id>', methods=['POST'])
def delete_professional(prof_id):
    
    professional_to_delete = ServiceProfessional.query.get(prof_id)
    
    if professional_to_delete:
       
        db.session.delete(professional_to_delete)
        db.session.commit()
        flash('Professional deleted successfully!', 'success')
    else:
        flash('Professional not found.', 'danger')
    
    return redirect(url_for('admin_homepage'))

#adding new services to services database 
@app.route('/add_service', methods=['POST'])
def add_service():
    
    service_name = request.form.get('name')
    service_description = request.form.get('description')
    service_price = request.form.get('price')
    
   
    new_service = Service(name=service_name, description=service_description, price=service_price)

    db.session.add(new_service)
    db.session.commit()
    
    return redirect(url_for('admin_homepage'))



#leads to index.html
@app.route('/logout/admin')
def admin_logout():
    session.pop('admin_logged_in', None) 
    flash("Logged out successfully.", "success")
    return redirect(url_for('index'))


@app.route('/summary/admin')
def admin_summary():
   
    return render_template('admin_summary.html')

@app.route('/search/admin', methods=['GET', 'POST'])
def admin_search():
    search_type = request.args.get('search_type', 'service_professional')  
    query = request.args.get('query', '')
    search_results = []

    if search_type == 'service_professional':
        search_results = ServiceProfessional.query.filter(ServiceProfessional.username.like(f'%{query}%')).all()
    elif search_type == 'customer':
        search_results = Customer.query.filter(Customer.username.like(f'%{query}%')).all()
    elif search_type == 'service':
        search_results = Service.query.filter(Service.name.like(f'%{query}%')).all()

    return render_template('admin_search.html', search_type=search_type, query=query, search_results=search_results)


    return render_template('admin_search.html', search_type=search_type, query=query, search_results=search_results)

@app.route('/professional/<int:professional_id>/ratings', methods=['GET'])
def professional_ratings(professional_id):
 
    professional = ServiceProfessional.query.get_or_404(professional_id)

   
    ratings = Rating.query.filter(
        Rating.professional_id == professional_id,
        Rating.rating.isnot(None),
        Rating.remark.isnot(None)
    ).all()

    return render_template('professional_ratings.html', professional=professional, ratings=ratings)


#admin end


#professional 


#shown by professional_login.html leads to professional_homepage.html
@app.route('/login/professional', methods=['GET', 'POST'])
def professional_login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = ServiceProfessional.query.filter_by(username=username).first()

        if user and check_password_hash(user.password, password):
            login_user(user)
            session['role'] = 'professional'  
            flash('Login successful!', 'success')
            return redirect(url_for('professional_homepage'))
        else:
            flash('Invalid login details. Please try again.', 'danger')

    return render_template('professional_login.html', role='professional')


# Service Professional Registration shown by professional_registration.html adds new registered professional to professional database and leads to professional_login.html
@app.route('/register/professional', methods=['GET', 'POST'])
def professional_register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        service_type = request.form['service_type']
        experience = request.form.get('experience', 0)
        phone_number = request.form['phone_number']
        pdf = request.files['pdf']

        if not pdf or not pdf.filename.endswith('.pdf'):
            flash('Please upload a valid PDF file.', 'danger')
            return redirect(url_for('professional_register'))

       
        pdf_filename = secure_filename(pdf.filename)
        pdf_path = os.path.join(app.config['UPLOAD_FOLDER'], pdf_filename)
        pdf.save(pdf_path)

       
        existing_user = ServiceProfessional.query.filter_by(username=username).first()
        if existing_user:
            flash('Username already exists. Please choose a different one.', 'danger')
            return redirect(url_for('professional_register'))

   
        hashed_password = generate_password_hash(password, method='pbkdf2:sha256')
        new_professional = ServiceProfessional(username=username, password=hashed_password,
                                               service_type=service_type,
                                               experience=int(experience),
                                               phone_number=phone_number, pdf=pdf_filename)
        db.session.add(new_professional)
        db.session.commit()

        flash('Registration successful! Please log in.', 'success')
        return redirect(url_for('professional_login'))

    return render_template('professional_registration.html')
@app.route('/resumes/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)


#shown by professional_homepage.html shows service requests from serviceRequest database
@app.route('/professional_homepage')
@login_required
def professional_homepage():
    if not isinstance(current_user, ServiceProfessional):
        flash("Access restricted to professionals only.", "danger")
        return redirect(url_for('index'))
    
  
    matching_requests = db.session.query(ServiceRequest).join(Customer).join(Service).filter(
        ServiceRequest.professional_id == None, 
        Service.name == current_user.service_type
    ).all()

    return render_template('professional_homepage.html', professional=current_user, requests=matching_requests)






#displays services with same name  on servuce.html and when customer clicks on a service it is added to servicerequest.html
@app.route('/services/<service_name>', methods=['GET', 'POST'])
@login_required
def view_services_by_name(service_name):
    services = Service.query.filter_by(name=service_name).all()

    if request.method == 'POST':
        service_id = request.form.get('service_id')
        service_request = ServiceRequest(
            service_id=service_id,
            customer_id=current_user.id,
            service_status='requested'
        )
        db.session.add(service_request)
        db.session.commit()
        flash("Service request submitted successfully.", "success")
        return redirect(url_for('view_services_by_name', service_name=service_name))
    
    # Get the accepted request for each service
    accepted_requests = {}
    for service in services:
        accepted_request = AcceptedRequest.query.filter_by(
            customer_id=current_user.id,
            service_id=service.id
        ).first()
        if accepted_request:
            accepted_requests[service.id] = accepted_request

    return render_template(
        'services.html', services=services, accepted_requests=accepted_requests
    )

#shown on professional homepage...gets request_id from prof_homepage.html
@app.route('/service_request/<int:request_id>/action', methods=['POST'])
@login_required
def handle_service_request(request_id):
    action = request.form.get('action')
    service_request = ServiceRequest.query.get(request_id)

    if action == 'approve':
        service_request.service_status = 'approved'
        service_request.professional_id = current_user.id
        utc_now = datetime.now(timezone.utc)  # Current UTC time
        ist_now = utc_now.astimezone(pytz.timezone('Asia/Kolkata'))  # Convert to IST
            
        service_request.date_of_request = ist_now 

        db.session.commit()

        accepted_request = AcceptedRequest(
        customer_id=service_request.customer_id,
        professional_id=current_user.id,
        service_id=service_request.service_id,

    )
        db.session.add(accepted_request)
        db.session.commit()

       
    elif action == 'reject':
        db.session.delete(service_request)
        db.session.commit()
    flash(f"Request {action}ed successfully.", "success")
    return redirect(url_for('professional_homepage'))

# shown by accepted_service.html and displays details of professionalwho accpeted request and service request
@app.route('/accepted_service/<int:service_id>', methods=['GET', 'POST'])
def accepted_service(service_id):
    service_request = ServiceRequest.query.get(service_id)
    professional = ServiceProfessional.query.get(service_request.professional_id)
    return render_template(
        'accepted_service.html',
        service_request=service_request,
        professional=professional,
        thank_you=False,
    )
@app.route('/rate/<int:service_id>', methods=['GET', 'POST'])
def rate(service_id):
    service_request = ServiceRequest.query.get(service_id)
    professional = ServiceProfessional.query.get(service_request.professional_id)
    if request.method == 'POST':
       
        if 'close_service' in request.form:
            service_request.service_status = 'closed'
            utc_now = datetime.now(timezone.utc)  # Current UTC time
            ist_now = utc_now.astimezone(pytz.timezone('Asia/Kolkata'))  # Convert to IST
            service_request.date_of_completion = ist_now
            db.session.commit()
            flash("Service closed successfully.", "success")

       
        remark = request.form.get('remark')
        rating = request.form.get('rating')

       
        rating_entry = Rating(
            professional_username=professional.username,
            professional_id=professional.id,
            service_request_id=service_request.id,
            rating=rating,
            remark=remark
        )
        db.session.add(rating_entry)
        db.session.commit()

    completion_date = service_request.date_of_completion.strftime('%Y-%m-%d %H:%M:%S') if service_request.date_of_completion else None

    return render_template(
        'rate.html',
        service_request=service_request,
        professional=professional,
        completion_date=completion_date
    )



@app.route('/view_customer_details/<int:customer_id>')
@login_required
def view_customer_details(customer_id):
    
    if not isinstance(current_user, ServiceProfessional):
        flash("Access restricted to professionals only.", "danger")
        return redirect(url_for('index'))
    
  
    customer = Customer.query.get(customer_id)
    
    if not customer:
        flash("Customer not found.", "danger")
        return redirect(url_for('professional_homepage'))
    
    
    return render_template('view_customer_details.html', customer=customer)



#leads to index.html
@app.route('/logout/professional')
@login_required
def professional_logout():
    session.pop('role', None)  # Remove role from session
    logout_user()
    flash("Logged out successfully.", "success")
    return redirect(url_for('index'))

    
    #return render_template('index.html', customer=current_user)



@app.route('/chat_with_customer')
@login_required
def chat_with_customer():
    return render_template('chat_with_customer.html', professional=current_user)
@app.route('/professional_summary/<int:professional_id>')
@login_required
def professional_summary(professional_id):
    
       
        professional = ServiceProfessional.query.get_or_404(professional_id)

      
        completed_services = ServiceRequest.query.filter_by(
            professional_id=professional_id,
            service_status='closed' 
        ).all()

       
        total_earnings = sum(req.service.price for req in completed_services if req.service.price)

       
        ratings_and_remarks = Rating.query.filter(
            Rating.professional_id == professional_id,
            Rating.rating.isnot(None),
            Rating.remark.isnot(None)
        ).all()

        
        if ratings_and_remarks:
            average_rating = round(sum(rating.rating for rating in ratings_and_remarks) / len(ratings_and_remarks), 2)
        else:
            average_rating = "No ratings yet"

       
        service_details = []
        for service in completed_services:
            service_info = {
                'service_name': service.service.name,
                'service_price': service.service.price,
                'date_of_request': service.date_of_request,
                'date_of_completion': service.date_of_completion,
                'customer_name': service.customer.username,  
                'customer_phone': service.customer.phone_number  
            }
            service_details.append(service_info)

        
        return render_template(
            'professional_summary.html',
            professional=professional,
            completed_services=completed_services,
            total_earnings=total_earnings,
            average_rating=average_rating,
            ratings_and_remarks=ratings_and_remarks,
            service_details=service_details
        )
  





@app.route('/edit_profile_professional', methods=['GET', 'POST'])
@login_required
def professional_edit_profile():
  
    prof = ServiceProfessional.query.filter_by(id=current_user.id).first()

    if request.method == 'POST':
       
        print("Current User ID:", current_user.id)
        print("Professiol Before Update:", prof.username, prof.experience, prof.phone_number)

       
        new_username = request.form.get('username')
        
        new_experience = request.form.get('experience')
        new_phone = request.form.get('phone_number')
        new_password = request.form.get('password')

        try:
            
            if new_username and new_username != prof.username:
                prof.username = new_username
                print("Updated Username:", new_username)

            if new_experience and new_experience != prof.experience:
                prof.experience = new_experience
                print("Updated experience:", new_experience)

            if new_phone and new_phone != prof.phone_number:
                prof.phone_number = new_phone
                print("Updated Phone:", new_phone)

            if new_password:  
                hashed_password = generate_password_hash(new_password, method='pbkdf2:sha256')
                prof.password = hashed_password
                print("Password Updated")

           
            db.session.commit()
            flash('Profile updated successfully!', 'success')

        except Exception as e:
            print("Error updating profile:", e)
            db.session.rollback()
            flash('Error updating profile. Please try again.', 'danger')

        
        return redirect(url_for('professional_homepage'))

    
    return render_template('professionaledit_profile.html', prof=prof)



#displays record of current professionals from professional database
@app.route('/view_professional')
def view_professional():
 
    professional = ServiceProfessional.query.all()
    
  
    prof_details = []
    for prof in professional:
        prof_details.append(f"ID: {prof.id}, Username: {prof.username}, service_type:{prof.service_type},  experience:{prof.experience},phone_number:{prof.phone_number},rating:{prof.rating},remark:{prof.remark}")

   
    return '<br>'.join(prof_details)

@app.route('/view_ratings')
def view_ratings():
    
    ratings = Rating.query.all()


    rating_details = []
    for rating in ratings:
        rating_details.append(
            f"ID: {rating.id}, Professional Username: {rating.professional_username}, Professional ID: {rating.professional_id}, "
            f"Service Request ID: {rating.service_request_id}, Rating: {rating.rating}, Remark: {rating.remark}, "
            f"Date of Rating: {rating.date_of_rating.strftime('%Y-%m-%d %H:%M:%S')}"
        )

    return '<br>'.join(rating_details)



#cheking the records of the accepted service database
@app.route('/view_accepted_services')
def view_accepted_services():
    
    accepted_services = AcceptedRequest.query.all()
    
    
    accepted_services_details = []
    for service in accepted_services:
        accepted_services_details.append(
            f"ID: {service.id}, Customer ID: {service.customer_id}, Professional ID: {service.professional_id}, Service ID: {service.service_id}"
            
        )

   
    return '<br>'.join(accepted_services_details)

#cheking the records of the servicerequest database
@app.route('/view_service_requests')
def view_service_requests():
    
    service_requests = ServiceRequest.query.all()
    
    
    service_request_details = []
    for request in service_requests:
        service_request_details.append(
            f"ID: {request.id}, Service ID: {request.service_id}, Customer ID: {request.customer_id}, Professional ID: {request.professional_id}, "
            f"Date of Request: {request.date_of_request},Date of Completion: {request.date_of_completion}, Status: {request.service_status}, Remarks: {request.remarks}"
        )

    
    return '<br>'.join(service_request_details)

#cheking the records of the customer database
@app.route('/view_customers')
def view_customers():
   
    customers = Customer.query.all()
    
    
    customer_details = []
    for customer in customers:
        customer_details.append(f"ID: {customer.id}, Username: {customer.username}, Location: {customer.location}, phone_number:{customer.phone_number}")

   
    return '<br>'.join(customer_details)

#used for showing all the records in services database
@app.route('/view_services')
def view_services():
    
    services = Service.query.all()
    
    
    services_details = []
    for service in services:
        services_details.append(f"ID: {service.id}, Name: {service.name}, description: {service.description}, price:{service.price}")

    return '<br>'.join(services_details)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()  
    app.run(port=5000,debug=True)

