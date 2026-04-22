# brain_not_found-431w-project
NittanyAuction project for Cmpsc431w

Team Members:
- Nicholas Russo
- Kevin Yu
- Anon Tongngam
- Chentian Zhu

# Project Description 
NittanyAuction is a full-stack web application that simulates an online auction platform for bidder, sellers, and helpdesk staff.
This project includes:
 - Database design and poplulation from raw CSV data
 - A Flask-based web application
 - Dynamic querying and real-time interaction with the database
The system follows the Phase II requirements provided in the project description. 

# Technologies Used 
Technologies:
- Backend: Python (Flask)
- Database: SQLite (database.db)
- Frontend: HTML, CSS, Bootstrap
- Security: SHA256 password hashing with salt
- IDE: PyCharm
- Version Control: GitHub

# Project Structure
 
**/templates**
- bidder.html  
- contact-helpdesk.html  
- edit-listing.html
- helpdesk.html
- index.html
- listing-details.html
- listing-details-bidder.html
- login.html
- my-bids.html
- my-listings.html
- pay.html
- post-item.html
- profile.html
- rate_seller.html
- register.html  
- seller.html
- seller_account.html
- seller_profile.html
- watchlist.html  

**Files**
- app.py  
- CleanAuction_Listing.py  
- database.db  
- passwordHasher.py  
- README.md  

# Database Setup 

The project uses SQLite as the database management system.
The database file is named `database.db`.

The database is populated using the provided CSV dataset from Canvas,
specifically the `users.csv` file for login functionality.

Instead of using a Python script, the data was imported manually using
PyCharm’s built-in “Import Data” feature. The CSV file was mapped to the
Users table, and the records were inserted directly into the database.

Before insertion, passwords were securely processed:
- Passwords are NOT stored in plain text
- A unique salt is associated with each user
- The password is combined with the salt and hashed using SHA256
- The hashed password and salt are stored in the Users table

The Users table includes the following attributes:
- email (PRIMARY KEY)
- password (hashed password)
- salt

To verify that the database has been populated correctly, the following
SQL query can be used:

SELECT * FROM Users;
# Password Hashing
Passwords are NOT stored in plain text.

We use SHA256 hashing with a salt:
- When storing passwords, we generate a salt
- The password is combined with the salt
- The result is hashed and stored in the database

During login:
- The entered password is hashed with the stored salt
- The hash is compared with the stored value

# User Login
- Role-based login using:
   - Users table
   - Bidders / Sellers / Helpdesk tables
- Session-based authentication
- Automatic role detection

# Category Hierarchy (Dynamic)
- Categories stored in Categories table
- Traversal uses:
  - get_subcategories()
  - get_all_subcategories() (BFS)
  - get_category_path() (breadcrumbs)

# Auction Listing Management (Seller)
Sellers can: 
 - Create listings
 - View listings
 - Edit listings
 - Deactivate listings
Rules Enforced:
 - Cannot edit if:
   - It has bids
   - It is inactive or sold
- Deactivation stores:
   - remaining bids
   - removal reason (audit table)
# Auction Bidding (Bidder) 
Bidding Rules:
 - Must be at least $1 higher
 - Cannot bid on own listing
 - Cannot bid consecutively
System Features:
 - Displays:
   - current highest bid
   - remaining bids
- Automatically updates listing status when:
  - Max bids reached
  - Reserve met or not met

# User Registration
- Supports:
  - Bidder registration
  - Seller registration
- Dynamically inserts:
  - Users
  - Role-specific tables
  - Address and vendor info

# User Profile Update
Users can update: 
 - Basic info
 - Address
 - Credit card
 - Password (with verification)
Constraints:
 - Email cannot be changed
 - Passwords always hashed

# Product Search
- Keyword search:
  - Title
  - Description
  - Category
  - Seller
- Price filtering:
  - min/max price
- Pagination implemented

# Rating System 
- Bidders can rate sellers after winning
- Ratings stored in:
  - Rating
  - seller_ratings
- Displays:
  - average rating
  - rating count
 
# Watchlist (Optional Feature) 
- Add/remove items
- Persistent in database
- Cannot add own listings

# Payment System 
- Winning bidder proceeds to payment
- Transaction recorded
- Listing marked as "Sold"

# HelpDesk System (Optional Feature) 
- Users can submit requests:
  - Add category
  - General support
- Helpdesk can:
  - Claim requests
  - Complete requests
Special Feature:
- Completeing "AddCategory" dynamically updates database

# Account Deletion
- Seperate flows for:
  - Seller
  - Bidder
Features:
- Requires password confirmation
- Deletes:
  - Role-specific data
  - Address / credit card info 
# How to Run the Application 
1. Open the project in PyCharm (or any IDE)
2. Make sure all dependencies are installed
3. Run the Flask application:

   python app.py

4. Open a browser and go to:
   http://127.0.0.1:5000/

# Login Instructions
Use the following test accounts:

Bidder:
email: arubertelli0@lsu.edu
password: TbIF16hoUqGl

Seller:
email: nrideoutmi@lsu.edu
password: CBCA4zXar

Seller (Local Vendor) 
email: mlempertz10@yandex.ru
password: rrFKu7T

HelpDesk:
email: cantonacci6p@lsu.edu
password: vKQmcc1y

# Final Notes 
This project demonstrates: 
- Full-stack web development
- Secure authentication
- Dynamic SQL querying
- Database-driven design
- Role-based architecture 
