from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import os
from datetime import datetime

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-change-this-in-production'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///rentalink.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'static/images/listings'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Initialize database
db = SQLAlchemy(app)

# Database Models
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(120), nullable=False)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    user_role = db.Column(db.String(20), default='renter')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Listing(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    type = db.Column(db.String(20), nullable=False)  # house, car, motorcycle
    title = db.Column(db.String(200), nullable=False)
    location = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Float, nullable=False)
    is_available = db.Column(db.Boolean, default=True)
    features = db.Column(db.Text)
    image_urls = db.Column(db.Text)
    description = db.Column(db.Text)
    contact_info = db.Column(db.String(200))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Review(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    listing_id = db.Column(db.Integer, db.ForeignKey('listing.id'), nullable=False)
    reviewer_name = db.Column(db.String(100), nullable=False)
    rating = db.Column(db.Integer, nullable=False)
    comment = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

class Reservation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    listing_id = db.Column(db.Integer, db.ForeignKey('listing.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(20))
    start_date = db.Column(db.Date)
    end_date = db.Column(db.Date)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), default='Pending')

    listing = db.relationship('Listing', backref=db.backref('reservations', lazy=True))

class Inquiry(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    listing_id = db.Column(db.Integer, db.ForeignKey('listing.id'))
    name = db.Column(db.String(100))
    email = db.Column(db.String(120))
    message = db.Column(db.Text)
    responded = db.Column(db.Boolean, default=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    responded = db.Column(db.Boolean, default=False)

    listing = db.relationship('Listing', backref=db.backref('inquiries', lazy=True))

# Routes
@app.route('/')
def index():
    recent_listings = Listing.query.filter_by(is_available=True).order_by(Listing.created_at.desc()).limit(6).all()
    return render_template('index.html', listings=recent_listings)

@app.route('/search')
def search():
    category = request.args.get('category', '')
    location = request.args.get('location', '')
    min_price = request.args.get('min_price', type=float)
    max_price = request.args.get('max_price', type=float)

    query = Listing.query.filter_by(is_available=True)

    if category:
        query = query.filter(Listing.type == category)
    if location:
        query = query.filter(Listing.location.contains(location))
    if min_price:
        query = query.filter(Listing.price >= min_price)
    if max_price:
        query = query.filter(Listing.price <= max_price)

    listings = query.all()

    return render_template('search.html', listings=listings,
                           category=category, location=location,
                           min_price=min_price, max_price=max_price)

@app.route('/listing/<int:id>')
def listing_detail(id):
    listing = Listing.query.get_or_404(id)
    reviews = Review.query.filter_by(listing_id=id).order_by(Review.timestamp.desc()).all()
    return render_template('listing.html', listing=listing, reviews=reviews)

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = User.query.filter_by(email=email, user_role='admin').first()
        if user and user.check_password(password):
            session['admin_id'] = user.id
            flash('Login successful!', 'success')
            return redirect(url_for('admin_dashboard'))
        else:
            flash('Invalid credentials!', 'error')
    return render_template('admin/login.html')

@app.route('/admin/dashboard')
def admin_dashboard():
    if 'admin_id' not in session:
        return redirect(url_for('admin_login'))
    listings = Listing.query.all()
    reviews = Review.query.order_by(Review.timestamp.desc()).all()
    return render_template('admin/dashboard.html', listings=listings, reviews=reviews)

@app.route('/admin/logout')
def admin_logout():
    session.pop('admin_id', None)
    flash('Logged out successfully!', 'success')
    return redirect(url_for('index'))

@app.route('/admin/manage-listings')
def manage_listings():
    if 'admin_id' not in session:
        return redirect(url_for('admin_login'))

    search_query = request.args.get('search', '')
    type_filter = request.args.get('type_filter', '')
    availability_filter = request.args.get('availability_filter', '')

    query = Listing.query

    if search_query:
        query = query.filter(
            Listing.title.ilike(f'%{search_query}%') |
            Listing.location.ilike(f'%{search_query}%')
        )
    if type_filter:
        query = query.filter(Listing.type == type_filter)
    if availability_filter == 'available':
        query = query.filter(Listing.is_available.is_(True))
    elif availability_filter == 'unavailable':
        query = query.filter(Listing.is_available.is_(False))

    listings = query.order_by(Listing.created_at.desc()).all()
    return render_template('admin/manage_listings.html', listings=listings)

@app.route('/admin/edit-listing/<int:listing_id>', methods=['GET', 'POST'])
def edit_listing(listing_id):
    if 'admin_id' not in session:
        return redirect(url_for('admin_login'))

    listing = Listing.query.get_or_404(listing_id)

    if request.method == 'POST':
        listing.type = request.form['type']
        listing.title = request.form['title']
        listing.location = request.form['location']
        listing.price = float(request.form['price'])
        listing.is_available = True if request.form.get('is_available') == 'on' else False
        listing.features = request.form['features']
        listing.description = request.form['description']
        listing.contact_info = request.form['contact_info']

        image_urls = []
        if 'images' in request.files:
            for image in request.files.getlist('images'):
                if image.filename != '':
                    filename = secure_filename(image.filename)
                    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                    image.save(filepath)
                    image_urls.append(filename)

        if image_urls:
            listing.image_urls = ','.join(image_urls)

        db.session.commit()
        flash('Listing updated successfully!', 'success')
        return redirect(url_for('admin_dashboard'))

    return render_template('admin/edit_listing.html', listing=listing)

@app.route('/admin/delete-listing/<int:id>', methods=['POST'])
def delete_listing(id):
    if 'admin_id' not in session:
        return redirect(url_for('admin_login'))
    listing = Listing.query.get_or_404(id)
    db.session.delete(listing)
    db.session.commit()
    flash('Listing deleted successfully!', 'success')
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/add-listing', methods=['GET', 'POST'])
def add_listing():
    if 'admin_id' not in session:
        return redirect(url_for('admin_login'))

    if request.method == 'POST':
        type = request.form['type']
        title = request.form['title']
        location = request.form['location']
        price = float(request.form['price'])
        is_available = True if request.form.get('is_available') == 'on' else False
        features = request.form['features']
        description = request.form['description']
        contact_info = request.form['contact_info']

        image_urls = []
        if 'images' in request.files:
            images = request.files.getlist('images')
            for image in images:
                if image and image.filename != '':
                    filename = secure_filename(image.filename)
                    save_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                    image.save(save_path)
                    image_urls.append(filename)

        image_urls_str = ','.join(image_urls) if image_urls else ''

        new_listing = Listing(
            type=type,
            title=title,
            location=location,
            price=price,
            is_available=is_available,
            features=features,
            description=description,
            contact_info=contact_info,
            image_urls=image_urls_str
        )

        db.session.add(new_listing)
        db.session.commit()

        flash('Listing added successfully!', 'success')
        return redirect(url_for('admin_dashboard'))

    return render_template('admin/add_listing.html')

@app.route('/admin/inquiries')
def admin_inquiries():
    if 'admin_id' not in session:
        return redirect(url_for('admin_login'))

    search = request.args.get('search', '')
    response_filter = request.args.get('response_filter', '')

    query = Inquiry.query

    if search:
        query = query.filter(
            Inquiry.name.ilike(f'%{search}%') |
            Inquiry.email.ilike(f'%{search}%')
        )

    if response_filter == 'responded':
        query = query.filter(Inquiry.responded.is_(True))
    elif response_filter == 'unresponded':
        query = query.filter(Inquiry.responded.is_(False))

    inquiries = query.order_by(Inquiry.timestamp.desc()).all()
    new_inquiry_count = Inquiry.query.filter_by(responded=False).count()

    return render_template('admin/inquiries.html', inquiries=inquiries, new_inquiry_count=new_inquiry_count)

@app.route('/admin/inquiries/<int:inquiry_id>/update', methods=['POST'])
def update_inquiry_status(inquiry_id):
    inquiry = Inquiry.query.get_or_404(inquiry_id)
    responded_value = request.form.get('responded', 'false')
    inquiry.responded = responded_value.lower() == 'true'
    db.session.commit()
    return redirect(url_for('admin_inquiries'))

@app.route('/listing/<int:listing_id>/add_review', methods=['POST'])
def add_review(listing_id):
    try:
        listing = Listing.query.get_or_404(listing_id)
        reviewer_name = request.form.get('reviewer_name')
        reviewer_email = request.form.get('reviewer_email')
        rating = int(request.form.get('rating'))
        comment = request.form.get('comment', '')

        if not reviewer_name or not reviewer_email or not rating:
            flash('Please fill in all required fields.', 'error')
            return redirect(url_for('listing_detail', id=listing_id))
        if rating < 1 or rating > 5:
            flash('Rating must be between 1 and 5 stars.', 'error')
            return redirect(url_for('listing_detail', id=listing_id))

        new_review = Review(
            listing_id=listing_id,
            reviewer_name=reviewer_name,
            rating=rating,
            comment=comment
        )
        db.session.add(new_review)
        db.session.commit()
        flash('Thank you for your review!', 'success')

    except ValueError:
        flash('Invalid rating value. Please try again.', 'error')
    except Exception:
        flash('An error occurred while submitting your review. Please try again.', 'error')
        db.session.rollback()

    return redirect(url_for('listing_detail', id=listing_id))

@app.route('/admin/reservations')
def admin_reservations():
    if 'admin_id' not in session:
        return redirect(url_for('admin_login'))

    search = request.args.get('search', '')
    status_filter = request.args.get('status_filter', '')
    category_filter = request.args.get('category_filter', '')

    query = Reservation.query.join(Listing)

    if search:
        query = query.filter(
            Reservation.name.ilike(f'%{search}%') |
            Reservation.email.ilike(f'%{search}%')
        )

    if status_filter:
        query = query.filter(Reservation.status == status_filter)

    if category_filter:
        query = query.filter(Listing.type == category_filter)

    reservations = query.order_by(Reservation.timestamp.desc()).all()

    return render_template('admin/reservations.html', reservations=reservations)

@app.route('/admin/reservations/<int:reservation_id>/update', methods=['POST'])
def update_reservation_status(reservation_id):
    reservation = Reservation.query.get_or_404(reservation_id)
    new_status = request.form.get('status', 'Pending')
    reservation.status = new_status
    db.session.commit()
    return redirect(url_for('admin_reservations'))

@app.context_processor
def inject_counts():
    new_reservations = Reservation.query.filter_by(status="Pending").count()
    return dict(new_reservations=new_reservations)

@app.route('/listing/<int:listing_id>/contact', methods=['POST'])
def contact_owner(listing_id):
    try:
        listing = Listing.query.get_or_404(listing_id)
        name = request.form.get('name')
        email = request.form.get('email')
        message = request.form.get('message', '')
        if not name or not email:
            flash('Please fill in all required fields.', 'error')
            return redirect(url_for('listing_detail', id=listing_id))

        new_inquiry = Inquiry(
            listing_id=listing_id,
            name=name,
            email=email,
            message=message
        )
        db.session.add(new_inquiry)
        db.session.commit()
        flash('Your inquiry has been sent!', 'success')

    except Exception:
        flash('An error occurred while sending your inquiry. Please try again.', 'error')
        db.session.rollback()

    return redirect(url_for('listing_detail', id=listing_id))

@app.route('/reserve/<int:listing_id>', methods=['POST'])
def reserve(listing_id):
    listing = Listing.query.get_or_404(listing_id)
    name = request.form['name']
    email = request.form['email']
    phone = request.form['phone']
    start_date = request.form['start_date']
    end_date = request.form['end_date']

    if request.method == 'POST':
        reservation = Reservation(
            listing_id=listing_id,
            name=name,
            email=email,
            phone=phone,
            start_date=datetime.strptime(start_date, '%Y-%m-%d').date(),
            end_date=datetime.strptime(end_date, '%Y-%m-%d').date()
        )
        listing.is_available = False
        db.session.add(reservation)
        db.session.commit()
        flash('Reservation successful! We will contact you soon.', 'success')
        return redirect(url_for('receipt', reservation_id=reservation.id))

    return redirect(url_for('listing_detail', id=listing_id))

@app.route('/receipt/<int:reservation_id>')
def receipt(reservation_id):
    reservation = Reservation.query.get_or_404(reservation_id)
    return render_template('receipt.html', reservation=reservation)

@app.route('/inquiry/<int:listing_id>', methods=['POST'])
def submit_inquiry(listing_id):
    name = request.form['name']
    email = request.form['email']
    message = request.form['message']

    inquiry = Inquiry(
        listing_id=listing_id,
        name=name,
        email=email,
        message=message
    )
    db.session.add(inquiry)
    db.session.commit()
    flash('Your inquiry has been sent! The admin will get back to you.', 'success')
    return redirect(url_for('listing_detail', id=listing_id))

# Create tables and ensure 'responded' column exists
def create_tables():
    with app.app_context():
        db.create_all()

        # Add 'responded' column if not already in the inquiry table
        try:
            db.engine.execute('ALTER TABLE inquiry ADD COLUMN responded BOOLEAN DEFAULT 0')
        except Exception:
            pass  # Column likely exists or can't be altered in SQLite
        try:
            db.engine.execute('ALTER TABLE reservation ADD COLUMN status VARCHAR(20) DEFAULT "Pending"')
        except Exception:
            pass

        # Create admin user if it doesn't exist
        admin = User.query.filter_by(email='admin@rentalink.com').first()
        if not admin:
            admin = User(
                email='admin@rentalink.com',
                first_name='Admin',
                last_name='User',
                user_role='admin'
            )
            admin.set_password('admin123')
            db.session.add(admin)
            db.session.commit()

# Only runs when executing app.py directly
if __name__ == '__main__':
    create_tables()
    app.run(debug=True)
