## Rentalink
A Unified web platform for Houses, Cars, and mortorcycles Rental in Rwanda.
This platform allows users to list properties, make reservations, manage listings, and handle inquiries.
These are the issues and current problems that Rentalink as a Company intends to solve:
 1. The Fragmented rental market in Rwanda with multiple platforms.
 2. inconsistent interfaces, and security risks.

## 📌 **Features**

- > Public-facing website to view and reserve properties.
- > Admin panel to:
  - Manage listings (add, edit, delete, search).
  - Manage reservations.
  - Manage reviews.
- > Reservation system with automatic receipt generation.
- > Print-friendly receipts.
- > User-friendly design with Bootstrap.


## 🛠️ **Tech Stack**

- **Backend:** Flask (Python)
- **Database:** SQLite (default, can be swapped for PostgreSQL/MySQL)
- **Frontend:** HTML, CSS (Bootstrap), Jinja2 templates
- **Deployment:** Local run with Flask’s dev server (can be containerized for production)

## 🧱 Database Models Summary

| Model       | Description                            |
|-------------|----------------------------------------|
| **User**        | Stores user login credentials and roles |
| **Listing**     | Rental properties with description, price, and type |
| **Reservation** | Booking record with user and time details |
| **Inquiry**     | Messages sent by users about a listing |

WORKFLOW AND PROCESS. (Run Locally)

## 🚀 **How to run it locally**

### 📦 Prerequisites

- Python 3.10+
- Virtualenv (recommended)

 **1 Clone the repository**

git clone https://github.com/mahlet-tilahun/rentalink.git
cd rentalink
## 📁 **Project Structure**
rentalink/
│
├── instance/
            ├── rentalink.db
├── static/
          ├── css
          ├── images
          ├── js
├── templates/
    ├── admin/
        ├── add_listing.html
        ├── dashboard.html
        ├── edit_listing.html
        ├── inquiries.html
        ├── login.html
        ├── manage_listings.html
        ├── reservations.html
|   ├── index.html
|   ├── base.html
│   ├── listing.html
│   ├── search.html
│   └── receipt.html
├── app.py                      
├── requirements.txt            
└── README.md   

**2 Create and activate a virtual environment**

python3 -m venv venv
source venv/bin/activate

**3 Install dependencies**
pip install -r requirements.txt

**4 Set up your environment**
By default, it uses SQLite (instance/rentalink.db).

**5 Run the app**
flask run
or 
python app.py

**Note: depending on the python version you're using, you may need to add the version. For example if you're using python 3, the command should be python3 app.py**
Open your browser and go to http://127.0.0.1:5000

As it's important to not push the database for public by GitHub, we did not push the database. Therefore, you will not see any listing on the home page. 

**Access Admin Dashboard**
http://127.0.0.1:5000/admin/login

Enter the Demo credentials on the bottom of the page.

On the Admin Dashboard, you can add and manage the listing as well. 
## 📬 **Contributing**
Pull requests are welcome! For major changes, please open an issue first to discuss what you would like to change.

##👥 **Contact**
**Africoders**

GitHub: @mahlet-tilahu
Email: admin@rentalink.rw

**Africoders | RentaLink | 2025**
