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
    features = db.Column(db.Text)  # JSON string of features
    image_urls = db.Column(db.Text)  # JSON string of image URLs
    description = db.Column(db.Text)
    contact_info = db.Column(db.String(200))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Review(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    listing_id = db.Column(db.Integer, db.ForeignKey('listing.id'), nullable=False)
    reviewer_name = db.Column(db.String(100), nullable=False)
    rating = db.Column(db.Integer, nullable=False)  # 1-5
    comment = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

# Routes
@app.route('/')
def index():
    # Get recent listings for homepage
    recent_listings = Listing.query.filter_by(is_available=True).order_by(Listing.created_at.desc()).limit(6).all()
    return render_template('index.html', listings=recent_listings)

@app.route('/search')
def search():
    # Get search parameters
    category = request.args.get('category', '')
    location = request.args.get('location', '')
    min_price = request.args.get('min_price', type=float)
    max_price = request.args.get('max_price', type=float)
    
    # Build query
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

# Admin Routes
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
    return render_template('admin/dashboard.html', listings=listings)

@app.route('/admin/logout')
def admin_logout():
    session.pop('admin_id', None)
    flash('Logged out successfully!', 'success')
    return redirect(url_for('index'))

# Initialize database and create admin user
def create_tables():
    with app.app_context():
        db.create_all()
        
        # Create admin user if doesn't exist
        admin = User.query.filter_by(email='admin@rentalink.com').first()
        if not admin:
            admin = User(
                email='admin@rentalink.com',
                first_name='Admin',
                last_name='User',
                user_role='admin'
            )
            admin.set_password('admin123')  # Change this password!
            db.session.add(admin)
            db.session.commit()


if __name__ == '__main__':
    create_tables()
    app.run(debug=True)