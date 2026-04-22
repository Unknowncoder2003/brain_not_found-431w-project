import email
import hashlib
import secrets
from string import hexdigits
from unittest import result

from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3
import uuid
import datetime

from passwordHasher import hashed_password

sql = sqlite3

app = Flask(__name__)
# This secret key is super important. It lets us securely track who is logged in via cookies.
app.secret_key = 'super_secret_nittany_key_that_nobody_will_know'  # for the session (the memory) to work

DB_NAME = 'database.db'
host = 'http://127.0.0.1:5000/'

@app.before_request
def ensure_roles_loaded():
    """Ensure that the session['roles'] list is always available for logged-in users."""
    if 'email' in session and 'roles' not in session:
        connection = get_connection()
        cursor = connection.cursor()
        roles = []
        cursor.execute("SELECT 1 FROM Helpdesk WHERE email = ?", (session['email'],))
        if cursor.fetchone(): roles.append('helpdesk')
        cursor.execute("SELECT 1 FROM Sellers WHERE email = ?", (session['email'],))
        if cursor.fetchone(): roles.append('seller')
        cursor.execute("SELECT 1 FROM Bidders WHERE email = ?", (session['email'],))
        if cursor.fetchone(): roles.append('bidder')
        connection.close()
        session['roles'] = roles


def get_connection():
    """
    Grabs a fresh connection to our SQLite database. 
    We call this anytime we want to read or write data.
    """
    conn = sql.connect(DB_NAME)
    return conn


@app.route('/')
def home():
    """
    Landing page. If logged in, redirects to the appropriate dashboard.
    Otherwise, redirects to the login page.
    """
    user_email = session.get('email')
    if user_email:
        # Use find_user_html logic to find the highest priority dashboard
        return redirect(url_for(find_user_html(user_email)))
    return redirect(url_for('authenticate'))


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
    connection = get_connection()
    Email = connection.execute('SELECT email FROM Users;')
    Password = connection.execute('SELECT password FROM Users;')
    connection.close()
    return None


@app.route('/login', methods=['POST', 'GET'])
def authenticate():
    """
    The bouncer of our app. Handles the login process for users.
    If it's a GET request, we just show them the login form.
    If it's a POST request, they submitted the form and we need to check their credentials.
    """
    error = None
    error = request.args.get('error')

    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        result = password_to_hash_checker(email, password)
        if result:
            session['email'] = email
            return redirect(url_for(find_user_html(email)))
        else:
            error = 'Invalid username or password.'
            return render_template('login.html', error=error)

    return render_template('login.html', error=error)


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('authenticate'))


def password_to_hash_checker(email, password):
    """Helper function for checking the user entered password and verify it against the database"""
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute('SELECT password, salt FROM Users WHERE email = ?', (email,))
    result = cursor.fetchone()
    connection.close()

    if result is None:
        print("No matching user.")
        return False

    stored_hash, salt = result
    password_and_salt = (password.strip() + salt).encode('utf-8')
    user_input_hash = hashlib.sha256(password_and_salt).hexdigest()
    return user_input_hash == stored_hash


def find_user_html(email):
    """Find the landing page the user should go to
    If a user has multiple roles the priority is: Helpdesk, Seller, Bidder"""
    connection = get_connection()
    cursor = connection.cursor()

    roles = []
    
    cursor.execute("SELECT 1 FROM Helpdesk WHERE email = ?", (email,))
    if cursor.fetchone():
        roles.append('helpdesk')

    cursor.execute("SELECT 1 FROM Sellers WHERE email = ?", (email,))
    if cursor.fetchone():
        roles.append('seller')

    cursor.execute("SELECT 1 FROM Bidders WHERE email = ?", (email,))
    if cursor.fetchone():
        roles.append('bidder')

    connection.close()
    
    session['roles'] = roles

    if 'helpdesk' in roles:
        return "helpdesk"
    if 'seller' in roles:
        return "seller"
    if 'bidder' in roles:
        return "bidder"
        
    return "index"


@app.route('/seller', methods=['POST', 'GET'])
def seller():
    """
    The main Dashboard for Sellers.
    This fetches their profile, active listings, and processes new item creations.
    """
    user_email = session.get('email')
    roles = session.get('roles', [])
    if not user_email or 'seller' not in roles:
        return redirect(url_for('authenticate', error='Access denied. Seller account required.'))
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute('SELECT first_name FROM Bidders WHERE email = ?', (user_email,))
    result = cursor.fetchone()
    connection.close()
    conn = get_connection()
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    # seller balanceinfo
    cur.execute("""
                SELECT email, bank_routing_number, bank_account_number, balance
                FROM Sellers
                WHERE email = ?
                """, (user_email,))
    seller_row = cur.fetchone()
    if seller_row:
        balance = seller_row['balance']
    else:
        balance = 0
    if result:
        first_name = result[0]
    else:
        first_name = 'Seller'
    avg_rating = None
    rating_count = 0

    try:
        conn = get_connection()
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()

        cur.execute("""
            SELECT AVG(Rating) AS avg_rating, COUNT(*) AS rating_count
            FROM Rating
            WHERE Seller_Email = ?
        """, (user_email,))
        result = cur.fetchone()

        if result:
            avg_rating = result['avg_rating']
            rating_count = result['rating_count']

            if avg_rating is not None:
                avg_rating = round(avg_rating, 2)

        conn.close()

    except Exception as e:
        print("ERROR in /seller:", e)

    return render_template(
        'seller.html',
        first_name=first_name,
        email=user_email,
        avg_rating=avg_rating,
        rating_count=rating_count,
        balance = balance
    )
"""The main Dashboard for Sellers."""
@app.route('/seller-account', methods=['GET', 'POST'])
def seller_account():
    user_email = session.get('email')
    roles = session.get('roles', [])
    if not user_email or 'seller' not in roles:
        return redirect(url_for('authenticate', error='Access denied. Seller account required.'))

    connection = sql.connect('database.db')
    cursor = connection.cursor()

    error = None
    success = None

    if request.method == 'POST':
        current_password = request.form.get('current_password', '').strip()
        new_password = request.form.get('new_password', '').strip()
        confirm_password = request.form.get('confirm_password', '').strip()
        bank_routing_number = request.form.get('bank_routing_number', '').strip()
        bank_account_number = request.form.get('bank_account_number', '').strip()

        routing_digits = ''.join(ch for ch in bank_routing_number if ch.isdigit())

        if len(routing_digits) != 9:
            error = "Routing number must contain exactly 9 digits."
        elif not bank_account_number.isdigit() or len(bank_account_number) != 8:
            error = "Bank account number must contain exactly 8 digits."
        elif new_password or confirm_password:
            if not current_password:
                error = "You must enter your current password to change your password."
            elif new_password != confirm_password:
                error = "New passwords do not match."
            else:
                cursor.execute("""
                    SELECT password, salt
                    FROM Users
                    WHERE email = ?
                """, (user_email,))
                result = cursor.fetchone()

                if not result:
                    error = "User account not found."
                else:
                    stored_hash, salt = result
                    current_hash = hashlib.sha256((current_password + salt).encode('utf-8')).hexdigest()

                    if current_hash != stored_hash:
                        error = "Current password is incorrect."

        if not error:
            # Update password only if user entered a new one
            if new_password:
                cursor.execute("""
                    SELECT salt
                    FROM Users
                    WHERE email = ?
                """, (user_email,))
                result = cursor.fetchone()

                if result:
                    salt = result[0]
                    new_hash = hashlib.sha256((new_password + salt).encode('utf-8')).hexdigest()
                    cursor.execute("""
                        UPDATE Users
                        SET password = ?
                        WHERE email = ?
                    """, (new_hash, user_email))

            # Update seller info
            cursor.execute("""
                UPDATE Sellers
                SET bank_routing_number = ?, bank_account_number = ?
                WHERE email = ?
            """, (bank_routing_number, bank_account_number, user_email))

            is_local_vendor = 'is_local_vendor' in request.form

            cursor.execute("""
                SELECT business_address_id
                FROM Local_Vendors
                WHERE email = ?
            """, (user_email,))
            local_vendor_row = cursor.fetchone()

            if is_local_vendor:
                business_name = request.form.get('business_name', '').strip()
                business_zipcode = request.form.get('business_zipcode', '').strip()
                business_street_num = request.form.get('business_street_num', '').strip()
                business_street_name = request.form.get('business_street_name', '').strip()
                customer_service_phone_number = request.form.get('customer_service_phone_number', '').strip()

                if not all([business_name, business_zipcode, business_street_num, business_street_name, customer_service_phone_number]):
                    error = "All local vendor fields are required."
                else:
                    if local_vendor_row:
                        business_address_id = local_vendor_row[0]

                        cursor.execute("""
                            UPDATE Address
                            SET zipcode = ?, street_num = ?, street_name = ?
                            WHERE address_id = ?
                        """, (business_zipcode, business_street_num, business_street_name, business_address_id))

                        cursor.execute("""
                            UPDATE Local_Vendors
                            SET business_name = ?, customer_service_phone_number = ?
                            WHERE email = ?
                        """, (business_name, customer_service_phone_number, user_email))
                    else:
                        import uuid
                        business_address_id = uuid.uuid4().hex[:24]

                        cursor.execute("""
                            INSERT INTO Address (address_id, zipcode, street_num, street_name)
                            VALUES (?, ?, ?, ?)
                        """, (business_address_id, business_zipcode, business_street_num, business_street_name))

                        cursor.execute("""
                            INSERT INTO Local_Vendors (email, business_name, business_address_id, customer_service_phone_number)
                            VALUES (?, ?, ?, ?)
                        """, (user_email, business_name, business_address_id, customer_service_phone_number))

            else:
                if local_vendor_row:
                    business_address_id = local_vendor_row[0]

                    cursor.execute("""
                        DELETE FROM Local_Vendors
                        WHERE email = ?
                    """, (user_email,))

                    cursor.execute("""
                        DELETE FROM Address
                        WHERE address_id = ?
                    """, (business_address_id,))

            if not error:
                connection.commit()
                success = "Account information updated successfully."

    cursor.execute("""
        SELECT email, bank_routing_number, bank_account_number, balance
        FROM Sellers
        WHERE email = ?
    """, (user_email,))
    seller_row = cursor.fetchone()

    seller = None
    if seller_row:
        seller = {
            'email': seller_row[0],
            'bank_routing_number': seller_row[1],
            'bank_account_number': seller_row[2],
            'balance': seller_row[3]
        }

    cursor.execute("""
        SELECT email, business_name, business_address_id, customer_service_phone_number
        FROM Local_Vendors
        WHERE email = ?
    """, (user_email,))
    vendor_row = cursor.fetchone()

    local_vendor = None
    business_address = None

    if vendor_row:
        local_vendor = {
            'email': vendor_row[0],
            'business_name': vendor_row[1],
            'business_address_id': vendor_row[2],
            'customer_service_phone_number': vendor_row[3]
        }

        cursor.execute("""
            SELECT zipcode, street_num, street_name
            FROM Address
            WHERE address_id = ?
        """, (vendor_row[2],))
        address_row = cursor.fetchone()

        if address_row:
            business_address = {
                'zipcode': address_row[0],
                'street_num': address_row[1],
                'street_name': address_row[2]
            }

    connection.close()

    return render_template(
        'seller_account.html',
        email=user_email,
        seller=seller,
        local_vendor=local_vendor,
        business_address=business_address,
        error=error,
        success=success,
        delete_error=None
    )

@app.route('/seller-account/delete', methods=['POST'])
def delete_seller_account():
    user_email = session.get('email')
    if not user_email:
        return redirect(url_for('authenticate'))

    delete_password = request.form.get('delete_password', '').strip()

    connection = get_connection()
    cursor = connection.cursor()

    try:
        # Verify current password first
        cursor.execute("""
            SELECT password, salt
            FROM Users
            WHERE email = ?
        """, (user_email,))
        user_row = cursor.fetchone()

        if not user_row:
            connection.close()
            session.clear()
            return redirect(url_for('authenticate'))

        stored_hash, salt = user_row
        entered_hash = hashlib.sha256((delete_password + salt).encode('utf-8')).hexdigest()

        if entered_hash != stored_hash:
            # Reload seller account page with delete-specific error
            cursor.execute("""
                SELECT email, bank_routing_number, bank_account_number, balance
                FROM Sellers
                WHERE email = ?
            """, (user_email,))
            seller_row = cursor.fetchone()

            seller = None
            if seller_row:
                seller = {
                    'email': seller_row[0],
                    'bank_routing_number': seller_row[1],
                    'bank_account_number': seller_row[2],
                    'balance': seller_row[3]
                }

            cursor.execute("""
                SELECT email, business_name, business_address_id, customer_service_phone_number
                FROM Local_Vendors
                WHERE email = ?
            """, (user_email,))
            vendor_row = cursor.fetchone()

            local_vendor = None
            business_address = None

            if vendor_row:
                local_vendor = {
                    'email': vendor_row[0],
                    'business_name': vendor_row[1],
                    'business_address_id': vendor_row[2],
                    'customer_service_phone_number': vendor_row[3]
                }

                cursor.execute("""
                    SELECT zipcode, street_num, street_name
                    FROM Address
                    WHERE address_id = ?
                """, (vendor_row[2],))
                address_row = cursor.fetchone()

                if address_row:
                    business_address = {
                        'zipcode': address_row[0],
                        'street_num': address_row[1],
                        'street_name': address_row[2]
                    }

            connection.close()
            return render_template(
                'seller_account.html',
                email=user_email,
                seller=seller,
                local_vendor=local_vendor,
                business_address=business_address,
                error=None,
                success=None,
                delete_error="Current password is incorrect."
            )

        # Delete local vendor info if it exists
        cursor.execute("""
            SELECT business_address_id
            FROM Local_Vendors
            WHERE email = ?
        """, (user_email,))
        local_vendor_row = cursor.fetchone()

        if local_vendor_row:
            business_address_id = local_vendor_row[0]

            cursor.execute("""
                DELETE FROM Local_Vendors
                WHERE email = ?
            """, (user_email,))

            cursor.execute("""
                DELETE FROM Address
                WHERE address_id = ?
            """, (business_address_id,))

        # Delete seller role
        cursor.execute("""
            DELETE FROM Sellers
            WHERE email = ?
        """, (user_email,))

        # Only delete from Users if no other roles remain
        cursor.execute("SELECT 1 FROM Bidders WHERE email = ?", (user_email,))
        is_bidder = cursor.fetchone()

        cursor.execute("SELECT 1 FROM Helpdesk WHERE email = ?", (user_email,))
        is_helpdesk = cursor.fetchone()

        if not is_bidder and not is_helpdesk:
            cursor.execute("""
                DELETE FROM Users
                WHERE email = ?
            """, (user_email,))
            connection.commit()
            connection.close()
            session.clear()
            return redirect(url_for('home'))

        connection.commit()
        connection.close()
        session.clear()
        return redirect(url_for('authenticate'))

    except Exception as e:
        connection.rollback()
        connection.close()
        print("Error deleting seller account:", e)
        return redirect(url_for('seller_account'))

@app.route('/seller-profile', methods=['GET'])
def seller_profile():
    user_email = session.get('email')
    roles = session.get('roles', [])
    if not user_email or 'seller' not in roles:
        return redirect(url_for('authenticate', error='Access denied. Seller account required.'))

    avg_rating = None
    rating_count = 0
    balance = None
    bank_routing_number = None
    bank_account_number = None
    business_name = None
    customer_service_phone_number = None

    active_count = 0
    inactive_count = 0
    sold_count = 0

    try:
        conn = get_connection()
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()

        # seller basic info
        cur.execute("""
            SELECT email, bank_routing_number, bank_account_number, balance
            FROM Sellers
            WHERE email = ?
        """, (user_email,))
        seller_row = cur.fetchone()

        if seller_row:
            balance = seller_row['balance']
            bank_routing_number = seller_row['bank_routing_number']
            bank_account_number = seller_row['bank_account_number']

        # local vendor info
        cur.execute("""
            SELECT business_name, customer_service_phone_number
            FROM Local_Vendors
            WHERE email = ?
        """, (user_email,))
        vendor_row = cur.fetchone()

        if vendor_row:
            business_name = vendor_row['business_name']
            customer_service_phone_number = vendor_row['customer_service_phone_number']

        # rating info from Rating table
        cur.execute("""
            SELECT AVG(Rating) AS avg_rating, COUNT(*) AS rating_count
            FROM Rating
            WHERE Seller_Email = ?
        """, (user_email,))
        rating_row = cur.fetchone()

        if rating_row:
            avg_rating = rating_row['avg_rating']
            rating_count = rating_row['rating_count']
            if avg_rating is not None:
                avg_rating = round(avg_rating, 2)

        # listing counts
        cur.execute("""
            SELECT
                SUM(CASE WHEN Status = 1 THEN 1 ELSE 0 END) AS active_count,
                SUM(CASE WHEN Status = 0 THEN 1 ELSE 0 END) AS inactive_count,
                SUM(CASE WHEN Status = 2 THEN 1 ELSE 0 END) AS sold_count
            FROM Auction_Listings
            WHERE Seller_Email = ?
        """, (user_email,))
        listing_row = cur.fetchone()

        if listing_row:
            active_count = listing_row['active_count'] or 0
            inactive_count = listing_row['inactive_count'] or 0
            sold_count = listing_row['sold_count'] or 0

        conn.close()

    except Exception as e:
        print("ERROR in /seller-profile:", e)

    masked_routing = None
    masked_account = None

    if bank_routing_number:
        bank_routing_number = str(bank_routing_number)
        masked_routing = '*' * max(0, len(bank_routing_number) - 4) + bank_routing_number[-4:]

    if bank_account_number:
        bank_account_number = str(bank_account_number)
        masked_account = '*' * max(0, len(bank_account_number) - 4) + bank_account_number[-4:]

    return render_template(
        'seller_profile.html',
        email=user_email,
        avg_rating=avg_rating,
        rating_count=rating_count,
        balance=balance,
        active_count=active_count,
        inactive_count=inactive_count,
        sold_count=sold_count,
        business_name=business_name,
        customer_service_phone_number=customer_service_phone_number,
        masked_routing=masked_routing,
        masked_account=masked_account
    )
@app.route('/bidder', methods=['GET'])
def bidder():
    sync_listing_statuses()
    """
    Main Dashboard for Bidders.
    Implements dynamic category traversal, advanced keyword/price search,
    and server-side pagination to maintain high performance.
    """
    user_email = session.get('email')
    roles = session.get('roles', [])
    if not user_email or 'bidder' not in roles:
        return redirect(url_for('authenticate', error='Access denied. Bidder account required.'))

    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute('SELECT first_name FROM Bidders WHERE email = ?', (user_email,))
    result = cursor.fetchone()


    if result:
        fname = result[0]
    else:
        fname = "Bidder"

    cate = get_category_tree()

    category = request.args.get('category')
    # Extract and clean search parameters
    search_term = request.args.get('search', '').strip()
    min_price = request.args.get('min_price', '').strip()
    max_price = request.args.get('max_price', '').strip()

    page = request.args.get('page', 1, type=int)
    per_page = 30
    offset = (page - 1) * per_page

    # Trigger search if ANY keyword or price filter is provided
    if search_term or min_price or max_price:
        items, total_items = search_items(search_term, min_price=min_price, max_price=max_price, limit=per_page, offset=offset)
    elif category:
        items, total_items = get_items(category, limit=per_page, offset=offset)
    else:
        items, total_items = get_all_items(limit=per_page, offset=offset)

    total_pages = (total_items + per_page - 1) // per_page
    
    pagination_pages = []
    if total_pages <= 7:
        pagination_pages = list(range(1, total_pages + 1))
    else:
        if page <= 4:
            pagination_pages = [1, 2, 3, 4, 5, None, total_pages]
        elif page >= total_pages - 3:
            pagination_pages = [1, None, total_pages - 4, total_pages - 3, total_pages - 2, total_pages - 1, total_pages]
        else:
            pagination_pages = [1, None, page - 1, page, page + 1, None, total_pages]
    
    current_category = category if category else 'All'
    subcategories = get_subcategories(current_category)
    breadcrumbs = get_category_path(current_category)

    connection.close()
    return render_template(
        'bidder.html',
        first_name=fname,
        categories=get_category_tree(), # Keeping for legacy dropdown if needed
        subcategories=subcategories,
        breadcrumbs=breadcrumbs,
        current_category=current_category,
        items=items,
        search_term=search_term if search_term else "",
        page=page,
        total_pages=total_pages,
        pagination_pages=pagination_pages
    )

def categories():
    connection = get_connection()
    top_category = connection.execute('SELECT category_name FROM Categories WHERE parent_category = "Root"')
    top_categories = top_category.fetchall()
    connection.close()
    return top_categories


def get_all_subcategories(target_category):
    """
    Finds the target category and all its children/grandchildren
    to create a full list of category names for filtering.
    """
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute('SELECT category_name, parent_category FROM Categories')
    rows = cursor.fetchall()
    connection.close()
    # Build a simple mapping of Parent -> [Children]
    adj_list = {}
    for name, parent in rows:
        if parent not in adj_list:
            adj_list[parent] = []
        adj_list[parent].append(name)
    # BFS to find all subcategories
    all_names = [target_category]
    queue = [target_category]
    while queue:
        current = queue.pop(0)
        if current in adj_list:
            for child in adj_list[current]:
                all_names.append(child)
                queue.append(child)
    print(f"debug {all_names}")
    return all_names


def get_items(category_name, limit, offset):
    """
    Fetches active listings for a specific category AND all its subcategories.
    Implements SQL-level pagination (LIMIT/OFFSET) and returns total count for UI pagination logic.
    """
    # Get the full list of related categories
    category_list = get_all_subcategories(category_name)
    connection = get_connection()
    cursor = connection.cursor()
    placeholders = ', '.join(['?'] * len(category_list))

    count_query = f'SELECT COUNT(*) FROM Auction_Listings WHERE Category IN ({placeholders}) AND Status = 1'
    cursor.execute(count_query, category_list)
    total_count = cursor.fetchone()[0]

    query = f'''
        SELECT A.Seller_Email, A.Listing_ID, A.Auction_Title, A.Product_Name,
               (SELECT MAX(bid_price) FROM Bids WHERE listing_id = A.Listing_ID AND seller_email = A.Seller_Email) AS Current_Price,
               A.Status
        FROM Auction_Listings A
        WHERE A.Category IN ({placeholders}) AND A.Status = 1
        LIMIT ? OFFSET ?
    '''
    cursor.execute(query, category_list + [limit, offset])
    data = cursor.fetchall()
    connection.close()
    return data, total_count

def get_all_items(limit, offset):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute('SELECT COUNT(*) FROM Auction_Listings WHERE Status = 1')
    total_count = cursor.fetchone()[0]

    cursor.execute('''
        SELECT A.Seller_Email, A.Listing_ID, A.Auction_Title, A.Product_Name,
               (SELECT MAX(bid_price) FROM Bids WHERE listing_id = A.Listing_ID AND seller_email = A.Seller_Email) AS Current_Price,
               A.Status
        FROM Auction_Listings A
        WHERE A.Status = 1
        LIMIT ? OFFSET ?
    ''', (limit, offset))
    data = cursor.fetchall()
    connection.close()
    return data, total_count

def search_items(search_term, min_price=None, max_price=None, limit=30, offset=0):
    """
    Comprehensive search engine.
    Matches keyword against Title, Description, Category, and Seller Email.
    Applies optional price filters based on current highest bid (treating no-bids as satisfying the filter).
    """
    connection = get_connection()
    cursor = connection.cursor()

    keyword = f"%{search_term}%"

    where_clause = "WHERE (A.Auction_Title LIKE ? OR A.Product_Name LIKE ? OR A.Product_Description LIKE ? OR A.Category LIKE ? OR A.Seller_Email LIKE ?) AND A.Status = 1"
    params = [keyword, keyword, keyword, keyword, keyword]

    if min_price:
        where_clause += " AND ((SELECT MAX(bid_price) FROM Bids WHERE listing_id = A.Listing_ID AND seller_email = A.Seller_Email) >= ? OR (SELECT MAX(bid_price) FROM Bids WHERE listing_id = A.Listing_ID AND seller_email = A.Seller_Email) IS NULL)"
        params.append(float(min_price))
    if max_price:
        where_clause += " AND ((SELECT MAX(bid_price) FROM Bids WHERE listing_id = A.Listing_ID AND seller_email = A.Seller_Email) <= ? OR (SELECT MAX(bid_price) FROM Bids WHERE listing_id = A.Listing_ID AND seller_email = A.Seller_Email) IS NULL)"
        params.append(float(max_price))

    count_query = f"SELECT COUNT(*) FROM Auction_Listings A {where_clause}"
    cursor.execute(count_query, params)
    total_count = cursor.fetchone()[0]

    query = f"""
        SELECT A.Seller_Email, A.Listing_ID, A.Auction_Title, A.Product_Name,
               (SELECT MAX(bid_price) FROM Bids WHERE listing_id = A.Listing_ID AND seller_email = A.Seller_Email) AS Current_Price,
               A.Status
        FROM Auction_Listings A
        {where_clause}
        LIMIT ? OFFSET ?
    """
    params.extend([limit, offset])

    cursor.execute(query, params)
    data = cursor.fetchall()
    connection.close()
    return data, total_count

@app.route('/item-details', methods=['POST', 'GET'])
def item_bid():
    user_email = session.get('email')
    roles = session.get('roles', [])
    if not user_email or ('bidder' not in roles and 'seller' not in roles):
        return redirect(url_for('authenticate', error='Access denied. Bidder or Seller account required.'))
    listing_id = request.args.get('item') or request.form.get('item')
    seller_email = request.args.get('seller') or request.form.get('seller')
    source = request.args.get('source') or request.form.get('source') or 'bidder'
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute('''
                   SELECT Seller_Email,
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
                   WHERE Listing_ID = ? AND Seller_Email = ?
            
                   ''', (listing_id, seller_email))
    item = cursor.fetchone()
    listing_id = item[1]
    seller_email = item[0]

    cursor.execute('''
                   SELECT COUNT(*)
                   FROM Bids
                   WHERE listing_id = ? AND seller_email = ?
                   ''', (listing_id, seller_email))
    current_bid_count = cursor.fetchone()[0]

    # Auto-repair: If max bids reached but status is still Active (1), mark as Sold (2)
    if current_bid_count >= item[8] and item[9] == 1:
        cursor.execute('UPDATE Auction_Listings SET Status = 2 WHERE Listing_ID = ? AND Seller_Email = ?', (listing_id, seller_email))
        connection.commit()
        # Refresh the item object after update
        cursor.execute('SELECT * FROM Auction_Listings WHERE Seller_Email = ? AND Listing_ID = ?', (seller_email, listing_id))
        item = cursor.fetchone()

    cursor.execute('''
                   SELECT MAX(Bid_price)
                   FROM Bids
                   WHERE listing_id = ? AND seller_email = ?
                   ''', (listing_id, seller_email))
    highest_bid = cursor.fetchone()[0] or 0

    cursor.execute("""
                   SELECT AVG(rating), COUNT(*)
                   FROM seller_ratings
                   WHERE seller_email = ?
                   """, (seller_email,))
    rating_row = cursor.fetchone()

    avg_rating = None
    rating_count = 0
    if rating_row:
        avg_rating = rating_row[0]
        rating_count = rating_row[1]
        if avg_rating is not None:
            avg_rating = round(avg_rating, 2)

    # Fetch seller reviews from the Rating table
    cursor.execute("""
        SELECT Bidder_Email, Rating, Rating_Desc, Date
        FROM Rating
        WHERE Seller_Email = ?
        ORDER BY Date DESC
    """, (seller_email,))
    seller_reviews = [{'bidder': row[0], 'rating': row[1], 'comment': row[2], 'date': row[3]} for row in cursor.fetchall()]

    #getting the max bid_id
    cursor.execute('''
                   SELECT MAX(bid_id)
                   FROM Bids
                   ''')
    highest_bid_id = cursor.fetchone()[0]

    user_email = session.get('email')
    in_watchlist = False
    if user_email:
        cursor.execute('''
            SELECT 1 FROM Watchlist
            WHERE Bidder_Email = ? AND Seller_Email = ? AND Listing_ID = ?
        ''', (user_email, seller_email, listing_id))
        if cursor.fetchone():
            in_watchlist = True

    #---check for consecutive bidding
    #getting the email for highest bidder

    #for adding a price to the bids, when clicking the button
    if request.method == 'POST':
        error = None

        # Prevent seller from bidding on their own item
        if user_email == seller_email:
            error = "You cannot bid on your own item."
            connection.close()
            return render_template(
                'listing-details-bidder.html',
                item=item,
                bid_count=current_bid_count,
                current_price=highest_bid,
                avg_rating=avg_rating,
                rating_count=rating_count,
                error=error,
                in_watchlist=in_watchlist,
                seller_reviews=seller_reviews
            )

        # Prevent consecutive self-bidding
        if current_bid_count > 0:
            cursor.execute('''
                           SELECT MAX(bid_id)
                           FROM Bids
                           WHERE listing_id = ? AND seller_email = ?
                           ''', (listing_id, seller_email))
            latest_bidder = cursor.fetchone()[0]

            cursor.execute('''
                           SELECT bidder_email
                           FROM Bids
                           WHERE listing_id = ? AND seller_email = ?
                             and bid_id = ?
                           ''', (listing_id, seller_email, latest_bidder))
            latest_bidder_email = cursor.fetchone()[0]
            if user_email == latest_bidder_email:
                error = "You recently bid this item, wait for another bidder"
                connection.close()
                return render_template(
                    'listing-details-bidder.html',
                    item=item,
                    bid_count=current_bid_count,
                    current_price=highest_bid,
                    avg_rating=avg_rating,
                    rating_count=rating_count,
                    error=error,
                    in_watchlist=in_watchlist,
                    seller_reviews=seller_reviews
                )
        bid_price = request.form.get('bid_price')
        if float(bid_price) >= highest_bid + 1:
            connection = get_connection()
            cursor = connection.cursor()
            current_bid_count += 1
            highest_bid = float(bid_price)
            highest_bid_id = highest_bid_id + 1
            #Insert a new bid
            cursor.execute('''
                           INSERT INTO Bids (bid_id, bidder_email, listing_id, seller_email, bid_price)
                           VALUES (?,?,?,?,?);
                           ''', (highest_bid_id,user_email,listing_id,seller_email,highest_bid))
            connection.commit()
            cursor.execute('''
                           SELECT COUNT(*)
                           FROM Bids
                           WHERE listing_id = ? AND seller_email = ?
                           ''', (listing_id, seller_email))
            current_bid_count = cursor.fetchone()[0]
            
            # Check if max bids reached, if so, close the auction
            if current_bid_count >= item[8]:
                cursor.execute('''
                    UPDATE Auction_Listings
                    SET Status = 2
                    WHERE Listing_ID = ? AND Seller_Email = ?
                ''', (listing_id, seller_email))
                connection.commit()
            
            cursor.execute('''
                           SELECT Status
                           FROM Auction_Listings
                           WHERE Listing_ID = ? AND Seller_Email = ?
                           ''', (listing_id, seller_email))
            new_status = cursor.fetchone()[0]
            item = list(item)
            item[9] = new_status
            item = tuple(item)
        else:
            print("our price is less than or equal to the current bidding limit put in another one")
            error = "Your price is less than or equal to the current bid put in another one"


        print("Bid:", bid_price)
        connection.close()
        # after clicking the bid button on modal then reload the page with new information
        return render_template(
            'listing-details-bidder.html',
            item=item,
            bid_count=current_bid_count,
            current_price=highest_bid,
            avg_rating=avg_rating,
            rating_count=rating_count,
            error=error,
            in_watchlist=in_watchlist,
            source=source,
            seller_reviews=seller_reviews
        )
    connection.close()
    return render_template(
        'listing-details-bidder.html',
        item=item,
        bid_count=current_bid_count,
        current_price=highest_bid,
        avg_rating=avg_rating,
        rating_count=rating_count,
        error=None,
        in_watchlist=in_watchlist,
        source=source,
        seller_reviews=seller_reviews
    )

@app.route('/contact-helpdesk', methods=['GET', 'POST'])
def contact_helpdesk():
    user_email = session.get('email')
    if not user_email:
        return redirect(url_for('authenticate'))

    roles = session.get('roles', [])
    if 'bidder' not in roles and 'seller' not in roles:
        return redirect(url_for('authenticate', error='Only bidders or sellers can submit helpdesk requests.'))

    connection = get_connection()
    cursor = connection.cursor()

    if request.method == 'POST':
        request_type = request.form.get('request_type', '').strip()
        reason = request.form.get('reason', '').strip()

        # Enforce seller-only constraint for AddCategory and MarketAnalysis
        if request_type in ['AddCategory', 'MarketAnalysis'] and 'seller' not in roles:
            return render_template(
                'contact-helpdesk.html',
                email=user_email,
                is_seller=('seller' in roles),
                error='Only sellers can request Market Analysis or Add New Category.'
            )

        if request_type == 'AddCategory':
            category_name = request.form.get('category_name', '').strip()
            parent_category = request.form.get('parent_category', '').strip()

            if not category_name or not parent_category:
                cursor.execute("SELECT category_name FROM Categories ORDER BY category_name")
                categories = cursor.fetchall()
                connection.close()
                return render_template(
                    'contact-helpdesk.html',
                    email=user_email,
                    is_seller=('seller' in roles),
                    categories=categories,
                    error='Category name and parent category are required for AddCategory requests.'
                )
            request_desc = f"Please add a new category {category_name} under {parent_category}. {reason}"
        else:
            request_desc = reason

        cursor.execute("""
            INSERT INTO Requests (
                sender_email,
                helpdesk_staff_email,
                request_type,
                request_desc,
                request_status
            )
            VALUES (?, ?, ?, ?, ?)
        """, (
            user_email,
            'helpdeskteam@lsu.edu',
            request_type,
            request_desc,
            0
        ))

        connection.commit()
        connection.close()

        return render_template(
            'contact-helpdesk.html',
            email=user_email,
            is_seller=('seller' in roles),
            success='Your request has been submitted successfully.'
        )

    return render_template(
        'contact-helpdesk.html',
        email=user_email,
        is_seller=('seller' in roles)
    )





@app.route('/helpdesk', methods=['GET'])
def helpdesk():
    user_email = session.get('email')
    if not user_email:
        return redirect(url_for('authenticate'))

    connection = get_connection()
    connection.row_factory = sqlite3.Row
    cursor = connection.cursor()

    cursor.execute('SELECT email FROM Helpdesk WHERE email = ?', (user_email,))
    result = cursor.fetchone()

    if not result:
        connection.close()
        return redirect(url_for('authenticate', error='You do not have access to the help desk'))

    cursor.execute("""
        SELECT *
        FROM Requests
        WHERE request_status = 0
          AND helpdesk_staff_email = 'helpdeskteam@lsu.edu'
        ORDER BY request_id DESC
    """)
    unassigned_requests = cursor.fetchall()

    cursor.execute("""
        SELECT *
        FROM Requests
        WHERE helpdesk_staff_email = ?
          AND request_status IN (1, 2)
        ORDER BY request_id DESC
    """, (user_email,))
    my_requests = cursor.fetchall()

    connection.close()

    return render_template(
        'helpdesk.html',
        email=user_email,
        unassigned_requests=unassigned_requests,
        my_requests=my_requests
    )

@app.route('/helpdesk/claim/<int:request_id>', methods=['POST'])
def claim_request(request_id):
    user_email = session.get('email')
    if not user_email:
        return redirect(url_for('authenticate'))

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute('SELECT email FROM Helpdesk WHERE email = ?', (user_email,))
    if not cursor.fetchone():
        connection.close()
        return redirect(url_for('authenticate', error='You do not have access to the help desk'))

    cursor.execute("""
        UPDATE Requests
        SET helpdesk_staff_email = ?, request_status = 1
        WHERE request_id = ?
          AND request_status = 0
          AND helpdesk_staff_email = 'helpdeskteam@lsu.edu'
    """, (user_email, request_id))

    connection.commit()
    connection.close()

    return redirect(url_for('helpdesk'))

@app.route('/helpdesk/complete/<int:request_id>', methods=['POST'])
def complete_request(request_id):
    user_email = session.get('email')
    if not user_email:
        return redirect(url_for('authenticate'))

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute('SELECT email FROM Helpdesk WHERE email = ?', (user_email,))
    if not cursor.fetchone():
        connection.close()
        return redirect(url_for('authenticate', error='You do not have access to the help desk'))

    cursor.execute("""
        SELECT request_desc
        FROM Requests
        WHERE request_id = ?
          AND request_type = 'AddCategory'
          AND helpdesk_staff_email = ?
          AND request_status = 1
    """, (request_id, user_email))

    row = cursor.fetchone()
    if not row:
        connection.close()
        return redirect(url_for('helpdesk'))

    request_desc = row[0]

    try:
        normalized_desc = request_desc.strip()

        if "Please add a new category " in normalized_desc:
            first_part = normalized_desc.split("Please add a new category ", 1)[1]
        elif "Please ad a new category " in normalized_desc:
            first_part = normalized_desc.split("Please ad a new category ", 1)[1]
        else:
            connection.close()
            return redirect(url_for('helpdesk'))

        category_name = first_part.split(" under ", 1)[0].strip()
        parent_category = first_part.split(" under ", 1)[1].split(".", 1)[0].strip()

    except Exception:
        connection.close()
        return redirect(url_for('helpdesk'))

    cursor.execute("""
        SELECT 1
        FROM Categories
        WHERE category_name = ?
    """, (parent_category,))
    parent_exists = cursor.fetchone()

    if not parent_exists:
        cursor.execute("""
            INSERT INTO Categories (category_name, parent_category)
            VALUES (?, ?)
        """, (parent_category, 'Root'))

    cursor.execute("""
        SELECT 1
        FROM Categories
        WHERE category_name = ?
    """, (category_name,))
    child_exists = cursor.fetchone()

    if child_exists:
        cursor.execute("""
            UPDATE Categories
            SET parent_category = ?
            WHERE category_name = ?
        """, (parent_category, category_name))
    else:
        cursor.execute("""
            INSERT INTO Categories (category_name, parent_category)
            VALUES (?, ?)
        """, (category_name, parent_category))

    cursor.execute("""
        UPDATE Requests
        SET request_status = 2
        WHERE request_id = ?
    """, (request_id,))

    connection.commit()
    connection.close()

    return redirect(url_for('helpdesk'))

@app.route('/profile', methods=['GET'])
def profile():
    user_email = session.get('email')
    roles = session.get('roles', [])
    if not user_email or ('bidder' not in roles and 'seller' not in roles):
        return redirect(url_for('authenticate', error='Access denied. Bidder or Seller account required.'))

    edit = request.args.get("edit")
    message = request.args.get("message")

    edit_basic = edit == "basic"
    edit_address = edit == "address"
    edit_card = edit == "card"
    edit_password = edit == "password"

    connection = get_connection()
    connection.row_factory = sql.Row
    cursor = connection.cursor()

    cursor.execute("""
        SELECT
            B.email,
            B.first_name,
            B.last_name,
            B.age,
            B.major,
            (A.street_num || ' ' || A.street_name) AS street,
            A.zipcode AS zipcode,
            C.card_type AS card_type,
            C.credit_card_num AS card_number,
            (C.expire_month || '/' || C.expire_year) AS card_exp,
            C.security_code AS security_code
        FROM Bidders B
        LEFT JOIN Address A
            ON B.home_address_id = A.address_id
        LEFT JOIN Credit_Cards C
            ON B.email = C.Owner_email
        WHERE B.email = ?
    """, (user_email,))

    user = cursor.fetchone()

    if user:
        user = dict(user)

        card_number = user.get('card_number')
        if card_number:
            card_number = str(card_number)
            if len(card_number) > 4:
                user['masked_card_number'] = '*' * (len(card_number) - 4) + card_number[-4:]
            else:
                user['masked_card_number'] = card_number
        else:
            user['masked_card_number'] = None

        security_code = user.get('security_code')
        if security_code:
            security_code = str(security_code)
            user['masked_security_code'] = '*' * len(security_code)
        else:
            user['masked_security_code'] = None

    print("DEBUG user =", dict(user) if user else None)
    connection.close()

    return render_template(
        'profile.html',
        user=user,
        edit_basic=edit_basic,
        edit_address=edit_address,
        edit_card=edit_card,
        edit_password=edit_password,
        message=message,
        delete_error=None
    )

@app.route('/profile/delete', methods=['POST'])
def delete_bidder_account():
    user_email = session.get('email')
    if not user_email:
        return redirect(url_for('authenticate'))

    delete_password = request.form.get('delete_password', '').strip()

    connection = get_connection()
    connection.row_factory = sqlite3.Row
    cursor = connection.cursor()

    try:
        # Verify password first
        cursor.execute("""
            SELECT password, salt
            FROM Users
            WHERE email = ?
        """, (user_email,))
        user_row = cursor.fetchone()

        if not user_row:
            connection.close()
            session.clear()
            return redirect(url_for('authenticate'))

        stored_hash = user_row['password']
        salt = user_row['salt']
        entered_hash = hashlib.sha256((delete_password + salt).encode('utf-8')).hexdigest()

        if entered_hash != stored_hash:
            # Reload profile data with delete_error so modal reopens
            cursor.execute("""
                SELECT
                    B.email,
                    B.first_name,
                    B.last_name,
                    B.age,
                    B.major,
                    (A.street_num || ' ' || A.street_name) AS street,
                    A.zipcode AS zipcode,
                    C.card_type AS card_type,
                    C.credit_card_num AS card_number,
                    (C.expire_month || '/' || C.expire_year) AS card_exp,
                    C.security_code AS security_code
                FROM Bidders B
                LEFT JOIN Address A
                    ON B.home_address_id = A.address_id
                LEFT JOIN Credit_Cards C
                    ON B.email = C.Owner_email
                WHERE B.email = ?
            """, (user_email,))
            user = cursor.fetchone()

            if user:
                user = dict(user)

                card_number = user.get('card_number')
                if card_number:
                    card_number = str(card_number)
                    if len(card_number) > 4:
                        user['masked_card_number'] = '*' * (len(card_number) - 4) + card_number[-4:]
                    else:
                        user['masked_card_number'] = card_number
                else:
                    user['masked_card_number'] = None

                security_code = user.get('security_code')
                if security_code:
                    security_code = str(security_code)
                    user['masked_security_code'] = '*' * len(security_code)
                else:
                    user['masked_security_code'] = None

            connection.close()

            return render_template(
                'profile.html',
                user=user,
                edit_basic=False,
                edit_address=False,
                edit_card=False,
                edit_password=False,
                message=None,
                delete_error='Current password is incorrect.'
            )

        # Delete bidder-related credit cards
        cursor.execute("""
            DELETE FROM Credit_Cards
            WHERE Owner_email = ?
        """, (user_email,))

        # Delete bidder home address if it exists
        cursor.execute("""
            SELECT home_address_id
            FROM Bidders
            WHERE email = ?
        """, (user_email,))
        bidder_row = cursor.fetchone()

        if bidder_row and bidder_row['home_address_id']:
            home_address_id = bidder_row['home_address_id']
            cursor.execute("""
                DELETE FROM Address
                WHERE address_id = ?
            """, (home_address_id,))

        # Delete bidder role
        cursor.execute("""
            DELETE FROM Bidders
            WHERE email = ?
        """, (user_email,))

        # Only delete Users row if no other roles remain
        cursor.execute("SELECT 1 FROM Sellers WHERE email = ?", (user_email,))
        is_seller = cursor.fetchone()

        cursor.execute("SELECT 1 FROM Helpdesk WHERE email = ?", (user_email,))
        is_helpdesk = cursor.fetchone()

        if not is_seller and not is_helpdesk:
            cursor.execute("""
                DELETE FROM Users
                WHERE email = ?
            """, (user_email,))
            connection.commit()
            connection.close()
            session.clear()
            return redirect(url_for('home'))

        connection.commit()
        connection.close()
        session.clear()
        return redirect(url_for('authenticate'))

    except Exception as e:
        connection.rollback()
        connection.close()
        print("Error deleting bidder account:", e)
        return redirect(url_for('profile'))

@app.route('/profile/update_basic', methods=['POST'])
def update_basic():
    user_email = session.get('email')
    roles = session.get('roles', [])
    if not user_email or ('bidder' not in roles and 'seller' not in roles):
        return redirect(url_for('authenticate', error='Access denied. Bidder or Seller account required.'))

    first_name = request.form.get('first_name')
    last_name = request.form.get('last_name')
    age = request.form.get('age')
    major = request.form.get('major')

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        UPDATE Bidders
        SET first_name = ?, last_name = ?, age = ?, major = ?
        WHERE email = ?
    """, (first_name, last_name, age, major, user_email))

    connection.commit()
    connection.close()

    return redirect('/profile')


@app.route('/profile/update_address', methods=['POST'])
def update_address():
    user_email = session.get('email')
    roles = session.get('roles', [])
    if not user_email or ('bidder' not in roles and 'seller' not in roles):
        return redirect(url_for('authenticate', error='Access denied. Bidder or Seller account required.'))

    street = request.form.get('street', '').strip()
    zipcode = request.form.get('zipcode', '').strip()

    street_num = ''
    street_name = street

    if street:
        parts = street.split(' ', 1)
        if len(parts) == 2:
            street_num = parts[0]
            street_name = parts[1]
        else:
            street_name = parts[0]

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("SELECT home_address_id FROM Bidders WHERE email = ?", (user_email,))
    result = cursor.fetchone()

    if result and result[0]:
        address_id = result[0]
        cursor.execute("""
            UPDATE Address
            SET street_num = ?, street_name = ?, zipcode = ?
            WHERE address_id = ?
        """, (street_num, street_name, zipcode, address_id))
    else:
        address_id = generate_address_id()
        cursor.execute("""
            INSERT INTO Address (address_id, zipcode, street_num, street_name)
            VALUES (?, ?, ?, ?)
        """, (address_id, zipcode, street_num, street_name))

        cursor.execute("""
            UPDATE Bidders
            SET home_address_id = ?
            WHERE email = ?
        """, (address_id, user_email))

    connection.commit()
    connection.close()

    return redirect('/profile')


@app.route('/profile/update_card', methods=['POST'])
def update_card():
    user_email = session.get('email')
    roles = session.get('roles', [])
    if not user_email or ('bidder' not in roles and 'seller' not in roles):
        return redirect(url_for('authenticate', error='Access denied. Bidder or Seller account required.'))

    card_type = request.form.get('card_type')
    card_number = request.form.get('card_number')
    card_exp = request.form.get('card_exp', '').strip()
    security_code = request.form.get('security_code')

    expire_month = None
    expire_year = None

    if '/' in card_exp:
        parts = card_exp.split('/')
        if len(parts) == 2:
            expire_month = parts[0].strip()
            expire_year = parts[1].strip()

    connection = get_connection()
    cursor = connection.cursor()

    if True: # Always delete existing cards first to prevent UNIQUE constraint collisions on primary key update
        cursor.execute("DELETE FROM Credit_Cards WHERE Owner_email = ?", (user_email,))
        cursor.execute("""
                       INSERT INTO Credit_Cards (Owner_email, credit_card_num, card_type, expire_month, expire_year,
                                                 security_code)
                       VALUES (?, ?, ?, ?, ?, ?)
                       """, (user_email, card_number, card_type, expire_month, expire_year, security_code))

    connection.commit()
    connection.close()

    return redirect('/profile')

@app.route('/profile/update_password', methods=['POST'])
def update_password():
    user_email = session.get('email')
    roles = session.get('roles', [])
    if not user_email or ('bidder' not in roles and 'seller' not in roles):
        return redirect(url_for('authenticate', error='Access denied. Bidder or Seller account required.'))

    old_password = request.form.get('old_password', '').strip()
    new_password = request.form.get('new_password', '').strip()
    confirm_new_password = request.form.get('confirm_new_password', '').strip()

    if not old_password or not new_password or not confirm_new_password:
        return redirect(url_for(
            'profile',
            edit='password',
            message='Please fill in all password fields.'
        ))

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT password, salt
        FROM Users
        WHERE email = ?
    """, (user_email,))
    result = cursor.fetchone()

    if not result:
        connection.close()
        return redirect(url_for('authenticate'))

    stored_hash = result[0]
    stored_salt = result[1]

    old_password_hash = hashlib.sha256(
        (old_password + stored_salt).encode('utf-8')
    ).hexdigest()

    if old_password_hash != stored_hash:
        connection.close()
        return redirect(url_for(
            'profile',
            edit='password',
            message='Old password is incorrect.'
        ))

    if new_password != confirm_new_password:
        connection.close()
        return redirect(url_for(
            'profile',
            edit='password',
            message='New passwords do not match.'
        ))

    new_salt = secrets.token_urlsafe(16)
    new_password_hash = hashlib.sha256(
        (new_password + new_salt).encode('utf-8')
    ).hexdigest()

    cursor.execute("""
        UPDATE Users
        SET password = ?, salt = ?
        WHERE email = ?
    """, (new_password_hash, new_salt, user_email))

    connection.commit()
    connection.close()

    return redirect(url_for(
        'profile',
        message='Password updated successfully.'
    ))

def generate_address_id():
    return uuid.uuid4().hex[:24]



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

        connection = get_connection()
        cursor = connection.cursor()

        cursor.execute('SELECT email FROM Users WHERE email = ?', (email,))
        if cursor.fetchone():
            connection.close()
            error = "Email already exists."
            return render_template('register.html', error=error)

        salt = secrets.token_urlsafe(16)
        hashed_pw = hashlib.sha256((password.strip() + salt).encode('utf-8')).hexdigest()

        cursor.execute(
            "INSERT INTO Users (email, password, salt) VALUES (?, ?, ?)",
            (email, hashed_pw, salt)
        )

        if role == "bidder":

            home_address_id = generate_address_id()

            cursor.execute("""
                           INSERT INTO Address (address_id, zipcode, street_num, street_name)
                           VALUES (?, ?, ?, ?)
                           """, (
                               home_address_id,
                               request.form['home_zipcode'],
                               request.form['home_street_num'],
                               request.form['home_street_name']
                           ))

            cursor.execute("""
                INSERT INTO Bidders (email, first_name, last_name, age, home_address_id, major)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                email,
                request.form['first_name'],
                request.form['last_name'],
                request.form['age'],
                home_address_id,
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
                #request.form['balance']
                0
            ))

            if 'is_local_vendor' in request.form:
                business_address_id = generate_address_id()

                cursor.execute("""
                               INSERT INTO Address (address_id, zipcode, street_num, street_name)
                               VALUES (?, ?, ?, ?)
                               """, (
                                   business_address_id,
                                   request.form['business_zipcode'],
                                   request.form['business_street_num'],
                                   request.form['business_street_name']
                               ))

                cursor.execute("""
                    INSERT INTO Local_Vendors (email, business_name, business_address_id, customer_service_phone_number)
                    VALUES (?, ?, ?, ?)
                """, (
                    email,
                    request.form['business_name'],
                    business_address_id,
                    request.form['customer_service_phone_number']
                ))

        connection.commit()
        connection.close()

        success = "Account created! You can now log in."
        return render_template('register.html', success=success)

    return render_template('register.html')


@app.route('/my-bids', methods=['GET','POST'])
def my_bids():
    user_email = session.get('email')
    roles = session.get('roles', [])
    if not user_email or 'bidder' not in roles:
        return redirect(url_for('authenticate', error='Access denied. Bidder account required.'))

    connection = get_connection()
    # Use sqlite3.Row to access columns by their database names
    connection.row_factory = sqlite3.Row
    cursor = connection.cursor()
    sort = request.args.get('sort', 'id')
    order_clause = "B.bid_id DESC"
    if sort == 'status':
        order_clause = "A.Status ASC, B.bid_id DESC"

    # This query retrieves the user's bid alongside the current highest bid for that item
    cursor.execute(f'''
                   SELECT A.Seller_Email,
                          A.Listing_ID,
                          A.Auction_Title,
                          A.Product_Name,
                          B.Bid_price AS bid_price,
                          A.Status AS Auction_Status,
                          (SELECT MAX(Bid_price)
                           FROM Bids
                           WHERE Listing_ID = B.Listing_ID AND Seller_Email = B.Seller_Email) AS Current_High_Bid,
                          CASE WHEN T.Transaction_ID IS NOT NULL THEN 1 ELSE 0 END AS is_paid
                   FROM Bids B 
                   JOIN Auction_Listings A ON B.Listing_ID = A.Listing_ID AND B.Seller_Email = A.Seller_Email
                   LEFT JOIN Transactions T ON T.Listing_ID = A.Listing_ID AND T.Buyer_Email = B.Bidder_email
                   WHERE B.Bidder_email = ?
                     AND B.Bid_ID = (
                         SELECT MAX(Bid_ID) 
                         FROM Bids B2 
                         WHERE B2.Listing_ID = B.Listing_ID 
                           AND B2.Seller_Email = B.Seller_Email
                           AND B2.Bidder_email = B.Bidder_email
                     )
                   ORDER BY {order_clause}
                   ''', (user_email,))

    raw_results = cursor.fetchall()
    connection.close()
    # Determine the status label for each bid
    processed_bids = []
    for row in raw_results:
        bid = dict(row)
        user_price = bid['bid_price']
        max_price = bid['Current_High_Bid']
        auction_status = bid['Auction_Status']
        bid['is_paid'] = (bid['is_paid'] == 1)
        if user_price < max_price:
            bid['display_status'] = "Outbid"
            bid['status_color'] = "text-danger"
        elif user_price == max_price:
            if auction_status == 1:
                bid['display_status'] = "Leading"
                bid['status_color'] = "text-success"
            elif auction_status == 2:
                bid['display_status'] = "Won"
                bid['status_color'] = "text-primary"
            elif auction_status == 3:
                bid['display_status'] = "Reserve Not Met"
                bid['status_color'] = "text-warning"
            else:
                bid['display_status'] = "Auction Ended"
                bid['status_color'] = "text-muted"

        processed_bids.append(bid)

    #rating mechanics for bidders to sellers
    if request.method == 'POST':
        rating = request.form.get('rate')
        description = request.form.get('description')
        listing_id = request.form.get('listing_id')
        seller_email = request.form.get('seller')
        print("Rating:", rating)
        print("Description:", description)
        print("Listing ID:", listing_id)
        print("Seller Email:", seller_email)

        connection = get_connection()
        cursor = connection.cursor()

        # Check if this bidder has already rated this seller today (PK constraint)
        cursor.execute('''
            SELECT 1 FROM Rating
            WHERE Bidder_Email = ? AND Seller_Email = ? AND Date = DATE('now')
        ''', (user_email, seller_email))
        if cursor.fetchone():
            connection.close()
            return redirect(url_for('my_bids'))

        # Insert stuff into the ratings table
        cursor.execute('''INSERT INTO Rating(Bidder_Email, Seller_Email, Date, Rating, Rating_Desc)
                          VALUES (?, ?, CURRENT_DATE, ?, ?)
                       ''', (user_email, seller_email, rating, description))

        connection.commit()
        # mechanics for checking if listing id is in or not
        cursor.execute('''INSERT INTO seller_ratings(auction_id, bidder_email, seller_email, rating, created_at)
                          VALUES (?, ?, ?, ?, CURRENT_DATE)
                       ''', (listing_id, user_email, seller_email, rating))
        connection.commit()

        connection.close()
        return redirect(url_for('my_bids'))

    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute('''SELECT auction_id, seller_email 
                      FROM seller_ratings
                      WHERE bidder_email = ?
                   ''', (user_email,))
    rating_rows = cursor.fetchall()
    rated_listings = {(row[0], row[1]) for row in rating_rows}

    # Check which sellers the bidder has already rated TODAY (Rating PK: Bidder_Email, Seller_Email, Date)
    cursor.execute('''
        SELECT Seller_Email FROM Rating
        WHERE Bidder_Email = ? AND Date = DATE('now')
    ''', (user_email,))
    sellers_rated_today = {row[0] for row in cursor.fetchall()}

    connection.close()
    return render_template('my-bids.html', email=user_email, listings=processed_bids,
                           rated_listings=rated_listings, sellers_rated_today=sellers_rated_today)



"""The dashboard for sellers to view their listings"""
@app.route('/my-listings', methods=['POST', 'GET'])
def my_listing():
    user_email = session.get('email')
    roles = session.get('roles', [])
    if not user_email or 'seller' not in roles:
        return redirect(url_for('authenticate', error='Access denied. Seller account required.'))

    connection = get_connection()
    cursor = connection.cursor()
    sort = request.args.get('sort', 'id')
    order_clause = "A.Listing_ID DESC"
    if sort == 'status':
        order_clause = "A.Status ASC, A.Listing_ID DESC"

    cursor.execute(f'''
        SELECT A.Listing_ID, 
               A.Auction_Title, 
               A.Category, 
               A.Reserve_Price, 
               A.Max_bids, 
               A.Status,
               (SELECT COUNT(*) FROM Bids b WHERE b.listing_id = A.Listing_ID AND b.seller_email = A.Seller_Email) as bid_count
        FROM Auction_Listings A
        WHERE A.Seller_Email = ?
        ORDER BY {order_clause}
    ''', (user_email,))
    result = cursor.fetchall()
    connection.close()
    return render_template('my-listings.html', email=user_email, listings=result)


@app.route('/listing-details/<seller_email>/<int:listing_id>')
def listing_details(seller_email, listing_id):
    user_email = session.get('email')
    roles = session.get('roles', [])
    if not user_email or ('bidder' not in roles and 'seller' not in roles):
        return redirect(url_for('authenticate', error='Access denied. Bidder or Seller account required.'))
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute('''
        SELECT Seller_Email,
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
          AND Listing_ID = ?
    ''', (seller_email, listing_id))
    item = cursor.fetchone()

    cursor.execute('''
        SELECT COUNT(*)
        FROM Bids
        WHERE listing_id = ? AND seller_email = ?
    ''', (listing_id, seller_email))
    current_bid_count = cursor.fetchone()[0]

    cursor.execute('''
        SELECT MAX(Bid_price)
        FROM Bids
        WHERE listing_id = ? AND seller_email = ?
    ''', (listing_id, seller_email))
    highest_bid = cursor.fetchone()[0] or 0

    cursor.execute("""
        SELECT AVG(rating), COUNT(*)
        FROM seller_ratings
        WHERE seller_email = ?
    """, (seller_email,))
    rating_row = cursor.fetchone()

    avg_rating = None
    rating_count = 0
    if rating_row:
        avg_rating = rating_row[0]
        rating_count = rating_row[1]
        if avg_rating is not None:
            avg_rating = round(avg_rating, 2)

    connection.close()

    return render_template(
        'listing-details.html',
        item=item,
        bid_count=current_bid_count,
        current_price=highest_bid,
        avg_rating=avg_rating,
        rating_count=rating_count
    )

"""The endpoint for deactivating a listing"""
@app.route('/deactivate-listing/<seller_email>/<int:listing_id>', methods=['POST'])
def deactivate_listing(seller_email, listing_id):
    """
    Handles the removal of a listing from the market.
    Enforces audit logging by requiring a removal reason and calculating remaining bid capacity.
    """
    user_email = session.get('email')
    roles = session.get('roles', [])
    if not user_email or 'seller' not in roles:
        return redirect(url_for('authenticate', error='Access denied. Seller account required.'))

    if user_email != seller_email:
        return redirect(url_for('my_listing'))

    removal_reason = request.form.get('removal_reason', 'No reason provided')

    try:
        connection = get_connection()
        cursor = connection.cursor()

        cursor.execute('SELECT Max_bids FROM Auction_Listings WHERE Seller_Email = ? AND Listing_ID = ?', (seller_email, listing_id))
        max_bids_row = cursor.fetchone()
        max_bids = max_bids_row[0] if max_bids_row else 0

        cursor.execute('SELECT COUNT(*) FROM Bids WHERE listing_id = ? AND seller_email = ?', (listing_id, seller_email))
        bid_count = cursor.fetchone()[0]

        remaining_bids = max(0, max_bids - bid_count)

        cursor.execute('''
            INSERT INTO Listing_Removals (seller_email, listing_id, remaining_bids, removal_reason)
            VALUES (?, ?, ?, ?)
        ''', (seller_email, listing_id, remaining_bids, removal_reason))

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

    return redirect(request.referrer)


"""Allow sellers to edit their listings"""
@app.route('/edit-listing/<seller_email>/<int:listing_id>', methods=['GET', 'POST'])
def edit_listing(seller_email, listing_id):
    """
    Allows sellers to update listing details.
    SECURITY: blocks edits if the listing has already received bids
    or is no longer in an 'Active' state.
    """
    user_email = session.get('email')
    roles = session.get('roles', [])

    if not user_email or user_email != seller_email or 'seller' not in roles:
        return redirect(url_for('authenticate', error='Access denied. Seller account required.'))

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute('SELECT Status FROM Auction_Listings WHERE Seller_Email = ? AND Listing_ID = ?', (seller_email, listing_id))
    item_status = cursor.fetchone()
    if not item_status or item_status[0] != 1:
        connection.close()
        return "Error: Cannot edit an item that is inactive, sold, or ended.", 400

    cursor.execute('SELECT COUNT(*) FROM Bids WHERE listing_id = ? AND seller_email = ?', (listing_id, seller_email))
    if cursor.fetchone()[0] > 0:
        connection.close()
        return "Error: Cannot edit an active listing that already has bids.", 400
    connection.close()


    if request.method == 'POST':
        connection = get_connection()
        cursor = connection.cursor()

        title = request.form['auction_title']
        prod_name = request.form['product_name']
        cat = request.form['category']
        desc = request.form['description']
        qty = request.form['quantity']
        reserve = request.form['reserve']
        max_b = int(request.form['max_bids'])
        
        if max_b < 1:
            connection.close()
            return "Error: Max Bids must be at least 1.", 400

        cursor.execute('SELECT 1 FROM Categories WHERE category_name = ?', (cat,))
        if not cursor.fetchone():
            connection.close()
            return "Error: Category does not exist.", 400

        cursor.execute('SELECT Status FROM Auction_Listings WHERE Seller_Email = ? AND Listing_ID = ?', (seller_email, listing_id))
        item_status = cursor.fetchone()
        if not item_status or item_status[0] != 1:
            connection.close()
            return "Error: Cannot edit an item that is inactive, sold, or ended.", 400

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

        # Automatically check if the new lowered Max_bids or Reserve_Price causes the auction to end
        cursor.execute('''
            UPDATE Auction_Listings
            SET Status = CASE
                WHEN (SELECT MAX(bid_price) FROM Bids WHERE listing_id = ? AND seller_email = ?) >= Reserve_Price THEN 2
                ELSE 3
            END
            WHERE Listing_ID = ? AND Seller_Email = ?
              AND (SELECT COUNT(*) FROM Bids WHERE listing_id = ? AND seller_email = ?) >= Max_bids
              AND Status = 1
        ''', (listing_id, seller_email, listing_id, seller_email, listing_id, seller_email))

        connection.commit()
        connection.close()

        return redirect(url_for('listing_details', seller_email=seller_email, listing_id=listing_id))

    if request.method == 'GET':
        connection = get_connection()
        cursor = connection.cursor()
        cursor.execute(
            'SELECT * FROM Auction_Listings WHERE Seller_Email = ? AND Listing_ID = ?',
            (seller_email, listing_id)
        )
        item = cursor.fetchone()
        connection.close()

        category_tree = get_category_tree()
        return render_template('edit-listing.html', item=item, category_tree=category_tree)


def get_subcategories(parent_name):
    """
    Dynamically fetches immediate child categories for the given parent.
    Used for level-by-level hierarchy traversal without loading the full tree.
    """
    connection = get_connection()
    cursor = connection.cursor()
    # If parent is None or 'All', we look for 'Root'
    if not parent_name or parent_name == 'All':
        target_parent = 'Root'
    else:
        target_parent = parent_name

    cursor.execute('SELECT category_name FROM Categories WHERE parent_category = ?', (target_parent,))
    rows = cursor.fetchall()
    connection.close()
    return [row[0] for row in rows]

def get_category_path(current_category):
    """
    Recursive path builder to generate breadcrumb navigation trails.
    """
    if not current_category or current_category == 'All':
        return []

    path = []
    curr = current_category
    connection = get_connection()
    cursor = connection.cursor()

    while curr and curr != 'Root':
        path.append(curr)
        cursor.execute('SELECT parent_category FROM Categories WHERE category_name = ?', (curr,))
        row = cursor.fetchone()
        if row:
            curr = row[0]
        else:
            break

    connection.close()
    path.reverse()
    return path

def get_category_tree():
    """Helper function to get the category tree (used for dropdowns)"""
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute('SELECT category_name, parent_category FROM Categories')
    rows = cursor.fetchall()
    connection.close()

    tree = {}
    for name, parent in rows:
        tree[name] = {'name': name, 'children': []}

    roots = []
    for name, parent in rows:
        if parent == 'Root' or parent is None:
            roots.append(tree[name])
        elif parent in tree:
            tree[parent]['children'].append(tree[name])

    return sorted(roots, key=lambda x: x['name'])


@app.route('/post-item', methods=['GET', 'POST'])
def post_item():
    user_email = session.get('email')
    roles = session.get('roles', [])
    if not user_email or 'seller' not in roles:
        return redirect(url_for('authenticate', error='Access denied. Seller account required.'))

    if request.method == 'POST':
        title = request.form.get('auction_title')
        p_name = request.form.get('product_name')
        cat = request.form.get('category')
        desc = request.form.get('description')
        qty = int(request.form.get('quantity'))
        reserve = float(request.form.get('reserve'))
        max_b = int(request.form.get('max_bids'))
        
        if max_b < 1:
            return "Error: Max Bids must be at least 1.", 400

        data = [title, p_name, cat, desc, qty, reserve, max_b]
        if any(v is None or v == "" for v in data):
            return "All fields are required!", 400

        connection = get_connection()
        cursor = connection.cursor()

        cursor.execute('SELECT 1 FROM Categories WHERE category_name = ?', (cat,))
        if not cursor.fetchone():
            connection.close()
            return "Invalid Category selected", 400

        cursor.execute('SELECT MAX(Listing_ID) FROM Auction_Listings WHERE Seller_Email = ?', (user_email,))
        result = cursor.fetchone()[0]
        next_id = 1 if result is None else result + 1

        try:
            cursor.execute('''
                INSERT INTO Auction_Listings (
                    Seller_Email, Listing_ID, Category, Auction_Title,
                    Product_Name, Product_Description, Quantity,
                    Reserve_Price, Max_bids, Status
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 1)
            ''', (user_email, next_id, cat, title, p_name, desc, qty, reserve, max_b))

            connection.commit()
            connection.close()
            return redirect(url_for('my_listing'))

        except sql.Error as e:
            connection.close()
            print(f"Database error: {e}")
            return "An error occurred while posting your item.", 500

    category_tree = get_category_tree()
    return render_template('post-item.html', category_tree=category_tree,email = user_email)
@app.route('/watchlist', methods=['GET'])
def watchlist():
    user_email = session.get('email')
    roles = session.get('roles', [])
    if not user_email or 'bidder' not in roles:
        return redirect(url_for('authenticate', error='Access denied. Bidder account required.'))

    connection = get_connection()
    connection.row_factory = sqlite3.Row
    cursor = connection.cursor()

    sort = request.args.get('sort', 'date')
    order_clause = "W.Added_At DESC"
    if sort == 'status':
        order_clause = "A.Status ASC, W.Added_At DESC"

    cursor.execute(f"""
        SELECT W.Seller_Email, W.Listing_ID, W.Added_At, 
               A.Auction_Title, A.Product_Name, A.Status 
        FROM Watchlist W
        JOIN Auction_Listings A ON W.Listing_ID = A.Listing_ID AND W.Seller_Email = A.Seller_Email
        WHERE W.Bidder_Email = ?
        ORDER BY {order_clause}
    """, (user_email,))
    
    saved_items = cursor.fetchall()
    connection.close()

    processed_items = []
    for row in saved_items:
        item = dict(row)
        
        conn2 = get_connection()
        cur2 = conn2.cursor()
        cur2.execute("SELECT MAX(Bid_price) FROM Bids WHERE listing_id = ? AND seller_email = ?", (item['Listing_ID'], item['Seller_Email']))
        highest = cur2.fetchone()[0]
        item['Current_High_Bid'] = highest if highest else 0
        conn2.close()
        
        processed_items.append(item)

    return render_template('watchlist.html', listings=processed_items, email=user_email)

@app.route('/watchlist/add', methods=['POST'])
def add_to_watchlist():
    user_email = session.get('email')
    roles = session.get('roles', [])
    if not user_email or 'bidder' not in roles:
        return redirect(url_for('authenticate', error='Access denied. Bidder account required.'))

    seller_email = request.form.get('seller_email')
    listing_id = request.form.get('listing_id')

    # Prevent seller from adding their own item to watchlist
    if user_email == seller_email:
        return redirect(url_for('item_bid', item=listing_id))

    if seller_email and listing_id:
        try:
            connection = get_connection()
            cursor = connection.cursor()
            cursor.execute("""
                INSERT INTO Watchlist (Bidder_Email, Seller_Email, Listing_ID)
                VALUES (?, ?, ?)
            """, (user_email, seller_email, listing_id))
            connection.commit()
            connection.close()
        except sqlite3.IntegrityError:
            pass

    return redirect(url_for('watchlist'))

@app.route('/watchlist/remove', methods=['POST'])
def remove_from_watchlist():
    user_email = session.get('email')
    roles = session.get('roles', [])
    if not user_email or 'bidder' not in roles:
        return redirect(url_for('authenticate', error='Access denied. Bidder account required.'))

    seller_email = request.form.get('seller_email')
    listing_id = request.form.get('listing_id')

    if seller_email and listing_id:
        connection = get_connection()
        cursor = connection.cursor()
        cursor.execute("""
            DELETE FROM Watchlist 
            WHERE Bidder_Email = ? AND Seller_Email = ? AND Listing_ID = ?
        """, (user_email, seller_email, listing_id))
        connection.commit()
        connection.close()

    return redirect(url_for('watchlist'))

@app.route('/pay/<int:listing_id>', methods=['GET'])
def pay_item_get(listing_id):
    """
    Displays the secure checkout screen.
    We calculate exactly how much the bidder owes and pre-fill their stored credit card info if they have one.
    """
    user_email = session.get('email')
    roles = session.get('roles', [])
    if not user_email or 'bidder' not in roles:
        return redirect(url_for('authenticate', error='Access denied. Bidder account required.'))

    seller_email = request.args.get('seller')
    if not seller_email:
        return redirect(url_for('my_bids', error='Seller context missing.'))

    connection = get_connection()
    connection.row_factory = sqlite3.Row
    cursor = connection.cursor()

    # Get Auction Info
    cursor.execute('''
        SELECT Seller_Email, Auction_Title, Product_Name
        FROM Auction_Listings
        WHERE Listing_ID = ? AND Seller_Email = ? AND Status = 2
    ''', (listing_id, seller_email))
    item = cursor.fetchone()
    if not item:
        connection.close()
        return redirect(url_for('my_bids'))
    
    # Get Max Bid
    cursor.execute('''
        SELECT MAX(bid_price)
        FROM Bids
        WHERE listing_id = ? AND seller_email = ? AND bidder_email = ?
    ''', (listing_id, seller_email, user_email))
    amount_owed = cursor.fetchone()[0] or 0.0

    # Get user credit card
    cursor.execute('SELECT * FROM Credit_Cards WHERE Owner_email = ?', (user_email,))
    card = cursor.fetchone()

    # Get user address
    cursor.execute('''
        SELECT a.street_num, a.street_name, z.city, z.state, a.zipcode
        FROM Bidders b
        LEFT JOIN Address a ON b.home_address_id = a.address_id
        LEFT JOIN Zipcode_Info z ON a.zipcode = z.zipcode
        WHERE b.email = ?
    ''', (user_email,))
    address = cursor.fetchone()

    connection.close()
    return render_template('pay.html', item=item, amount_owed=amount_owed, card=card, address=address, listing_id=listing_id, email=user_email)

@app.route('/pay/<int:listing_id>', methods=['POST'])
def pay_item_post(listing_id):
    """
    Process the payment. This locks in the transaction so the database knows the item was officially paid for.
    It also saves their credit card details for next time so they don't have to retype it.
    """
    user_email = session.get('email')
    roles = session.get('roles', [])
    if not user_email or 'bidder' not in roles:
        return redirect(url_for('authenticate', error='Access denied. Bidder account required.'))

    cc_num = request.form.get('credit_card_num', '').strip()
    card_type = request.form.get('card_type', '').strip()
    exp_month = request.form.get('expire_month', '').strip()
    exp_year = request.form.get('expire_year', '').strip()
    sec_code = request.form.get('security_code', '').strip()
    amount_paid = request.form.get('amount_paid', '').strip()
    seller_email = request.form.get('seller_email', '').strip()

    street_num = request.form.get('street_num', '').strip()
    street_name = request.form.get('street_name', '').strip()
    city = request.form.get('city', '').strip()
    state = request.form.get('state', '').strip()
    zipcode = request.form.get('zipcode', '').strip()

    # Basic validation
    if not all([cc_num, card_type, exp_month, exp_year, sec_code, amount_paid, seller_email]):
        return "Missing payment or credit card information.", 400

    try:
        amount_paid = float(amount_paid)
    except ValueError:
        return "Invalid payment amount.", 400

    connection = get_connection()
    cursor = connection.cursor()

    try:
        # Replace saved credit card
        cursor.execute("DELETE FROM Credit_Cards WHERE Owner_email = ?", (user_email,))
        cursor.execute('''
            INSERT INTO Credit_Cards
            (credit_card_num, card_type, expire_month, expire_year, security_code, Owner_email)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (cc_num, card_type, exp_month, exp_year, sec_code, user_email))

        # Optional address update if all address fields are provided
        if street_num and street_name and city and state and zipcode:
            cursor.execute('''
                INSERT OR IGNORE INTO Zipcode_Info (zipcode, city, state)
                VALUES (?, ?, ?)
            ''', (zipcode, city, state))

            cursor.execute('SELECT home_address_id FROM Bidders WHERE email = ?', (user_email,))
            bidder_record = cursor.fetchone()
            home_address_id = bidder_record[0] if bidder_record else None

            if home_address_id:
                cursor.execute('''
                    UPDATE Address
                    SET street_num = ?, street_name = ?, zipcode = ?
                    WHERE address_id = ?
                ''', (street_num, street_name, zipcode, home_address_id))
            else:
                new_address_id = generate_address_id()
                cursor.execute('''
                    INSERT INTO Address (address_id, street_num, street_name, zipcode)
                    VALUES (?, ?, ?, ?)
                ''', (new_address_id, street_num, street_name, zipcode))
                cursor.execute('''
                    UPDATE Bidders
                    SET home_address_id = ?
                    WHERE email = ?
                ''', (new_address_id, user_email))

        cursor.execute("SELECT MAX(Transaction_ID) FROM Transactions")
        highest_tx = cursor.fetchone()[0]
        next_tx_id = (highest_tx or 0) + 1

        current_date = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        cursor.execute('''
            INSERT INTO Transactions (Transaction_ID, Seller_Email, Listing_ID, Buyer_Email, Date, Payment)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (next_tx_id, seller_email, listing_id, user_email, current_date, amount_paid))

        # Credit the seller's balance
        cursor.execute('''
            UPDATE Sellers
            SET balance = balance + ?
            WHERE email = ?
        ''', (amount_paid, seller_email))

        connection.commit()

    except Exception as e:
        connection.rollback()
        connection.close()
        print("Payment error:", e)
        return f"Payment failed: {e}", 500

    connection.close()
    return redirect(url_for('my_bids'))

def sync_listing_statuses():
    """
    Run a startup check to ensure all Auction Listings have the correct status.
    If the number of bids >= Max_bids, Status should be 2 (Sold) if reserve met, else 3 (Reserve Not Met).
    """
    connection = get_connection()
    cursor = connection.cursor()
    
    # Update listings where max bids are reached and reserve price is met
    cursor.execute('''
        UPDATE Auction_Listings
        SET Status = 2
        WHERE Status = 1 AND (Listing_ID, Seller_Email) IN (
            SELECT a.Listing_ID, a.Seller_Email
            FROM Auction_Listings a
            JOIN Bids b ON a.Listing_ID = b.listing_id AND a.Seller_Email = b.seller_email
            GROUP BY a.Listing_ID, a.Seller_Email
            HAVING COUNT(b.bid_id) >= a.Max_bids AND MAX(b.bid_price) >= a.Reserve_Price
        )
    ''')
    
    # Update listings where max bids are reached and reserve price is NOT met
    cursor.execute('''
        UPDATE Auction_Listings
        SET Status = 3
        WHERE Status = 1 AND (Listing_ID, Seller_Email) IN (
            SELECT a.Listing_ID, a.Seller_Email
            FROM Auction_Listings a
            JOIN Bids b ON a.Listing_ID = b.listing_id AND a.Seller_Email = b.seller_email
            GROUP BY a.Listing_ID, a.Seller_Email
            HAVING COUNT(b.bid_id) >= a.Max_bids AND MAX(b.bid_price) < a.Reserve_Price
        )
    ''')
    
    connection.commit()
    connection.close()




if __name__ == "__main__":
    sync_listing_statuses()#syncronizing the database so the listing doesn't stay active if it should be sold or expired
    app.run()