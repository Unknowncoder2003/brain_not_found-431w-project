import email
import hashlib
import secrets
from string import hexdigits
from unittest import result

from flask import Flask, render_template, request,redirect, url_for,session
import sqlite3 as sql

from passwordHasher import hashed_password

app = Flask(__name__)
app.secret_key = 'super_secret_nittany_key_that_nobody_will_know' #for the session (the memory) to work

host = 'http://127.0.0.1:5000/'
@app.route('/')
def index():
    return render_template('index.html')



'''
def valid_name(first_name, last_name):
    connection = sql.connect('database.db')
    connection.execute('CREATE TABLE IF NOT EXISTS users(firstname TEXT, lastname TEXT);')
    connection.execute('INSERT INTO users (firstname, lastname) VALUES (?,?);', (first_name, last_name))
    connection.commit()
    cursor = connection.execute('SELECT * FROM users;')
    return cursor.fetchall()
'''

def valid_email_password(email, password):
    connection = sql.connect('database.db')
    Email = connection.execute('SELECT email FROM Users;')
    Password = connection.execute('SELECT password FROM Users;')
    return None


@app.route('/login', methods=['POST', 'GET'])
def authenticate():
    error = None
    # Look for 'error' in the URL parameters
    error = request.args.get('error')

    #when click the login button the authenticate stuff occur
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        result = password_to_hash_checker(email, password)
        if result:
            # if result is true go to the user front page
            session['email'] = email
            return redirect(url_for(find_user_html(email)))
        # if not match stay in the same page and have error message or go to another html?
        else:
            error = 'Invalid username or password.'
            return render_template('login.html', error=error)

    return render_template('login.html', error=error)

def password_to_hash_checker(email, password):
    """Helper function for checking the user entered password and verify it against the database"""
    connection = sql.connect('database.db')
    cursor = connection.cursor()
    cursor.execute('SELECT password, salt FROM Users WHERE email = ?', (email,)) #finds the hashed password for the provided username
    result = cursor.fetchone()
    connection.close()
    if result is None:
        #the username is incorrect or not in the database
            print("No matching user.")
            return False
    stored_hash, salt = result
    salt = salt
    stored_hash = stored_hash
    password_and_salt = (password.strip() + salt).encode('utf-8')
    user_input_hash = hashlib.sha256(password_and_salt).hexdigest()
    return user_input_hash == stored_hash
def find_user_html(email):
    connection = sql.connect('database.db')
    cursor = connection.cursor()
    #Check if the user is Helpdesk staff
    cursor.execute("SELECT 1 FROM Helpdesk WHERE email = ?", (email,))
    if cursor.fetchone():
        connection.close()
        return "helpdesk"
    #Check if the user is a Seller
    cursor.execute("SELECT 1 FROM Sellers WHERE email = ?", (email,))
    if cursor.fetchone():
        connection.close()
        return "seller"
    #Check if the user is a Bidder
    cursor.execute("SELECT 1 FROM Bidders WHERE email = ?", (email,))
    if cursor.fetchone():
        connection.close()
        return "bidder"
    # Default fallback if email is not found in any role table
    connection.close()
    return "index"

@app.route('/seller', methods=['POST', 'GET'])
def seller():
    # Get the email of the person who just logged in
    user_email = session.get('email')
    if not user_email:
        user_email = 'place_holder@lsu.edu'  # not returning to authenticate for debugging purpose
        # return redirect(url_for('authenticate'))  # Redirect to login if they aren't logged in

    return render_template('seller.html',email = user_email)
@app.route('/bidder')
def bidder():
    # Get the email of the person who just logged in
    user_email = session.get('email')
    if not user_email:
        pass  # not showing for debugging purpose
        # return redirect(url_for('authenticate'))  # Redirect to login if they aren't logged in
    # Connect to DB and get the First Name
    connection = sql.connect('database.db')
    cursor = connection.cursor()
    cursor.execute('SELECT first_name FROM Bidders WHERE email = ?', (user_email,))
    result = cursor.fetchone()
    connection.close()
    # Handle the result
    if result:
        fname = result[0]
    else:
        fname = "Bidder"  # Fallback name
    # SEND THE DATA TO HTML
    return render_template('bidder.html', first_name=fname)
@app.route('/helpdesk', methods=['POST', 'GET'])
def helpdesk():
    #security check: if a user is not a helpdesk, they will get aborted to the login page.
    # Get the email of the person who just logged in
    user_email = session.get('email')
    if not user_email:
        pass  # not showing for debugging purpose
        # return redirect(url_for('authenticate'))  # Redirect to login if they aren't logged in
    connection = sql.connect('database.db')
    cursor = connection.cursor()
    cursor.execute('SELECT email FROM Helpdesk WHERE email = ?', (user_email,))
    result = cursor.fetchone()
    connection.close()
    if not result:
        #the user is not a helpdesk staff, abort
        return redirect(url_for('authenticate', error = 'You do not have access to the help desk'))
    return render_template('helpdesk.html', email=user_email)

@app.route('/profile', methods=['GET','POST'])
def profile():

    user_email = session.get('email')

    if not user_email:
        return redirect(url_for('authenticate'))

    connection = sql.connect('database.db')
    cursor = connection.cursor()

    # 获取用户信息
    cursor.execute("SELECT * FROM Users WHERE email = ?", (user_email,))
    user = cursor.fetchone()

    connection.close()

    return render_template('profile.html', user=user)
@app.route('/register', methods=['GET', 'POST'])
def register_page():
    error = None
    success = None

    if request.method == 'POST':
        email = request.form['email']
        role = request.form['role']
        password = request.form['password']
        confirm_password = request.form['confirm_password']

        if password != confirm_password:
            error = "Passwords do not match"
            return render_template('register.html', error=error)

        connection = sql.connect('database.db')
        cursor = connection.cursor()

        cursor.execute('SELECT email FROM Users WHERE email = ?', (email,))
        if cursor.fetchone():
            connection.close()
            error = "Email already exists."
            return render_template('register.html', error=error)

        salt = secrets.token_urlsafe(16)
        hashed_password = hashlib.sha256((password.strip() + salt).encode('utf-8')).hexdigest()

        cursor.execute(
            "INSERT INTO Users (email, password, salt) VALUES (?, ?, ?)",
            (email, hashed_password, salt)
        )

        if role == "bidder":
            cursor.execute("""
                INSERT INTO Bidders (email, first_name, last_name, age, home_address_id, major)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                email,
                request.form['first_name'],
                request.form['last_name'],
                request.form['age'],
                request.form['home_address_id'],
                request.form['major']
            ))

        elif role == "seller":
            cursor.execute("""
                INSERT INTO Sellers (email, bank_routing_number, bank_account_number, balance)
                VALUES (?, ?, ?, ?)
            """, (
                email,
                request.form['bank_routing_number'],
                request.form['bank_account_number'],
                0
            ))

        connection.commit()
        connection.close()

        success = "Account created! You can now log in."
        return render_template('register.html', success=success)

    return render_template('register.html')

@app.route('/my-listings', methods=['POST', 'GET'])
def my_listing():
    user_email = session.get('email')
    if not user_email:
        pass  # not showing for debugging purpose
        # return redirect(url_for('authenticate'))  # Redirect to login if they aren't logged in
    connection = sql.connect('database.db')
    cursor = connection.cursor()
    cursor.execute('SELECT A.Listing_ID, A.Auction_Title, A.Category, A.Reserve_Price, A.Max_bids, A.Status FROM Auction_Listings A WHERE A.Seller_Email = ?', (user_email,))
    result = cursor.fetchall()
    connection.close()
    return render_template('my-listings.html', email=user_email, listings=result)


@app.route('/listing-details/<seller_email>/<int:listing_id>')
def listing_details(seller_email, listing_id):
    connection = sql.connect('database.db')
    cursor = connection.cursor()
    #Get the Auction Listing details
    cursor.execute('''SELECT Seller_Email,
                             Listing_ID,
                             Category,
                             Auction_Title,
                             Product_Name,
                             Product_Description,
                             Quantity,
                             Reserve_Price,
                             Max_bids,
                             Status
                      FROM Auction_Listings
                      WHERE Seller_Email = ?
                        AND Listing_ID = ?''', (seller_email, listing_id))
    item = cursor.fetchone()
    #Get the count of current bids for this specific listing
    cursor.execute('''SELECT COUNT(*)
                      FROM Bids
                      WHERE listing_id = ?''', (listing_id,))
    current_bid_count = cursor.fetchone()[0]
    #Get the highest bid price to show current price vs reserve
    cursor.execute('''SELECT MAX(Bid_price)
                      FROM Bids
                      WHERE listing_id = ?''', (listing_id,))
    highest_bid = cursor.fetchone()[0] or 0  # Default to 0 if no bids yet
    connection.close()
    print(current_bid_count)
    return render_template('listing-details.html',
                           item=item,
                           bid_count=current_bid_count,
                           current_price=highest_bid)


@app.route('/deactivate-listing/<seller_email>/<int:listing_id>', methods=['POST'])
def deactivate_listing(seller_email, listing_id):
    #making sure the user is logged in
    user_email = session.get('email')
    if not user_email:
        return redirect(url_for('login'))
    #making sure the user owns this product
    if user_email != seller_email:
        return redirect(url_for('my_listing', error = 'You do not have access to the deactivate listing'))
    try:
        connection = sql.connect('database.db')
        cursor = connection.cursor()

        # 3. Execute the Update: Set status to 0 (Inactive)
        cursor.execute('''
                       UPDATE Auction_Listings
                       SET Status = 0
                       WHERE Seller_Email = ?
                         AND Listing_ID = ?
                       ''', (seller_email, listing_id))
        connection.commit()
        connection.close()
    except Exception as e:
        print(f"Error updating status: {e}")
    #redirect back to the previous page
    return redirect(request.referrer)


@app.route('/edit-listing/<seller_email>/<int:listing_id>', methods=['GET', 'POST'])
def edit_listing(seller_email, listing_id):
    user_email = session.get('email')

    #Security Check
    if not user_email or user_email != seller_email:
        return redirect(url_for('login'))

    connection = sql.connect('database.db')
    cursor = connection.cursor()
    #Handle the Form Submission
    if request.method == 'POST':
        #Retrieve data from form fields
        title = request.form['auction_title']
        prod_name = request.form['product_name']
        cat = request.form['category']
        desc = request.form['description']
        qty = request.form['quantity']
        reserve = request.form['reserve']
        max_b = request.form['max_bids']

        cursor.execute('''
                       UPDATE Auction_Listings
                       SET Auction_Title       = ?,
                           Product_Name        = ?,
                           Category            = ?,
                           Product_Description = ?,
                           Quantity            = ?,
                           Reserve_Price       = ?,
                           Max_bids            = ?
                       WHERE Seller_Email = ?
                         AND Listing_ID = ?
                       ''', (title, prod_name, cat, desc, qty, reserve, max_b, seller_email, listing_id))
        connection.commit()
        connection.close()
        #Go back to the details page
        return redirect(url_for('listing_details', seller_email=seller_email, listing_id=listing_id))
    #Handle the Initial Load
    cursor.execute('SELECT * FROM Auction_Listings WHERE Seller_Email = ? AND Listing_ID = ?',
                   (seller_email, listing_id))
    item = cursor.fetchone()
    connection.close()
    if not item:
        return "Listing not found", 404
    return render_template('edit-listing.html', item=item)
if __name__ == "__main__":
    app.run()



#the categories that are apart of root
def categories():
    connection = sql.connect('database.db')
    top_category = connection.execute('SELECT category_name FROM Categories WHERE parent_category = "Root"')

    #sub_category = connection.execute('SELECT category_name FROM Categories WHERE parent_category in top_category')
    #sub_categories =
    print(top_category.fetchall())
    #print(sub_category.fetchall())
    return None

def get_items(category_name):
    connection = sql.connect('database.db')
    cursor = connection.cursor()
    #get the items
    #check for subcategories first
    #then select all of the items
    items = cursor.execute('SELECT Auction_Title FROM Auction_Listings WHERE category_name = ?', (category_name,))
    return cursor.fetchall()

categories()
