# brain_not_found-431w-project
NittanyAuction project for Cmpsc431w

Team Members:
- Nicholas Russo
- Kevin Yu
- Anon Tongngam
- Chentian Zhu

# Project Description 
This project is a prototype of NittanyAuction, an online auction platform
designed for university students and local vendors. In Phase 2, we implemented
user login functionality with secure password hashing and role-based access
for bidders, sellers, and helpdesk users.

# Technologies Used 
Technologies:
- Python (Flask)
- SQLite
- PyCharm
- HTML/CSS (Bootstrap)

# Database Setup 

# Password Hashing
Passwords are NOT stored in plain text.

We use SHA256 hashing with a salt:
- When storing passwords, we generate a salt
- The password is combined with the salt
- The result is hashed and stored in the database

During login:
- The entered password is hashed with the stored salt
- The hash is compared with the stored value

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

HelpDesk:
email: cantonacci6p@lsu.edu
password: vKQmcc1y

# Features Implemented for Progress Review
Implemented Features:

- User Login System
- Secure password hashing (SHA256 + salt)
- Database population from CSV / script
- Role-based login:
  - Bidder → bidder.html
  - Seller → seller.html
  - HelpDesk → helpdesk.html
- Error handling for invalid login

# Known Limitations 
Limitations:

- Search functionality is not fully implemented
- Listings are currently static (not database-driven yet)
- UI is still under development

# File Structure 
/dataset\
   -Address.csv\
   -Auction_Listings.csv\
   -Bidders.csv\
   -Bids.csv\
   -Categories.csv\
   -Clean_Action_listining.csv\
   -Credit_Cards.csv\
   -HashedUsers.csv\
   -Helpdesk.csv\
   -Local_Venders.csv\
   -Ratings.csv\
   -Requests.csv\
   -Sellers.csv\
   -Transactions.csv\
   -Users.csv\
   -Zipcoe_Info.csv\
/temples\
   -bidder.html\
   -helpdesk.html\
   -index.html\
   -login.html\
   -seller.html\
app.py\
CleanAuction_Listing.py\
database.db\
passwordHasher.py\
README.md\
-test.py

