import email
import hashlib
import secrets
from string import hexdigits
from unittest import result

from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3

from passwordHasher import hashed_password

# 统一别名，兼容你原来大量使用的 sql.connect(...)
sql = sqlite3

app = Flask(__name__)
app.secret_key = 'super_secret_nittany_key_that_nobody_will_know'  # for the session (the memory) to work

DB_NAME = 'database.db'
host = 'http://127.0.0.1:5000/'


def get_connection():
    conn = sql.connect(DB_NAME)
    return conn


def ensure_seller_ratings_table():
    """
    确保 seller_ratings 表存在。
    用 auction_id UNIQUE 防止同一笔交易重复评分。
    """
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS seller_ratings (
            rating_id INTEGER PRIMARY KEY AUTOINCREMENT,
            auction_id INTEGER NOT NULL UNIQUE,
            seller_email TEXT NOT NULL,
            bidder_email TEXT NOT NULL,
            rating INTEGER NOT NULL CHECK (rating >= 1 AND rating <= 5),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    connection.commit()
    connection.close()


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
    connection = get_connection()
    Email = connection.execute('SELECT email FROM Users;')
    Password = connection.execute('SELECT password FROM Users;')
    connection.close()
    return None


@app.route('/login', methods=['POST', 'GET'])
def authenticate():
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
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("SELECT 1 FROM Helpdesk WHERE email = ?", (email,))
    if cursor.fetchone():
        connection.close()
        return "helpdesk"

    cursor.execute("SELECT 1 FROM Sellers WHERE email = ?", (email,))
    if cursor.fetchone():
        connection.close()
        return "seller"

    cursor.execute("SELECT 1 FROM Bidders WHERE email = ?", (email,))
    if cursor.fetchone():
        connection.close()
        return "bidder"

    connection.close()
    return "index"


@app.route('/seller', methods=['POST', 'GET'])
def seller():
    user_email = session.get('email')
    if not user_email:
        user_email = 'place_holder@lsu.edu'

    avg_rating = None
    rating_count = 0

    try:
        ensure_seller_ratings_table()

        conn = get_connection()
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()

        cur.execute("""
            SELECT AVG(rating) AS avg_rating, COUNT(*) AS rating_count
            FROM seller_ratings
            WHERE seller_email = ?
        """, (user_email,))
        result = cur.fetchone()
        conn.close()

        if result:
            avg_rating = result['avg_rating']
            rating_count = result['rating_count']

            if avg_rating is not None:
                avg_rating = round(avg_rating, 2)

    except Exception as e:
        print("ERROR in /seller:", e)

    return render_template(
        'seller.html',
        email=user_email,
        avg_rating=avg_rating,
        rating_count=rating_count
    )


@app.route('/bidder', methods=['GET'])
def bidder():
    user_email = session.get('email')
    if not user_email:
        pass

    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute('SELECT first_name FROM Bidders WHERE email = ?', (user_email,))
    result = cursor.fetchone()
    connection.close()

    if result:
        fname = result[0]
    else:
        fname = "Bidder"

    cate = get_category_tree()

    category = request.args.get('category')
    if category:
        items = get_items(category)
    else:
        items = get_all_items()

    return render_template('bidder.html', first_name=fname, categories=cate, items=items)


def categories():
    connection = get_connection()
    top_category = connection.execute('SELECT category_name FROM Categories WHERE parent_category = "Root"')
    top_categories = top_category.fetchall()
    connection.close()
    return top_categories


def get_items(category_name):
    connection = get_connection()
    cursor = connection.cursor()
    items = cursor.execute('SELECT Auction_Title FROM Auction_Listings WHERE Category = ?', (category_name,))
    data = items.fetchall()
    connection.close()
    return data


def get_all_items():
    connection = get_connection()
    cursor = connection.cursor()
    items = cursor.execute('SELECT DISTINCT Auction_Title FROM Auction_Listings')
    data = items.fetchall()
    connection.close()
    return data

@app.route('/item-details', methods=['POST', 'GET'])
def item_details():
    item = request.args.get('item')
    item = item_bid(item)
    return render_template('listing-details.html', item = item)
def item_bid(item_name):
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
                   WHERE Auction_Title = ?
            
                   ''', (item_name,))
    item = cursor.fetchone()
    return item



@app.route('/helpdesk', methods=['POST', 'GET'])
def helpdesk():
    user_email = session.get('email')
    if not user_email:
        pass

    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute('SELECT email FROM Helpdesk WHERE email = ?', (user_email,))
    result = cursor.fetchone()
    connection.close()

    if not result:
        return redirect(url_for('authenticate', error='You do not have access to the help desk'))

    return render_template('helpdesk.html', email=user_email)


@app.route('/profile', methods=['GET'])
def profile():
    user_email = session.get('email')
    if not user_email:
        return redirect(url_for('authenticate'))

    edit = request.args.get("edit")
    edit_basic = edit == "basic"
    edit_address = edit == "address"
    edit_card = edit == "card"

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
            (C.expire_month || '/' || C.expire_year) AS card_exp
        FROM Bidders B
        LEFT JOIN Address A
            ON B.home_address_id = A.address_id
        LEFT JOIN Credit_Cards C
            ON B.email = C.Owner_email
        WHERE B.email = ?
    """, (user_email,))

    user = cursor.fetchone()
    print("DEBUG user =", dict(user) if user else None)
    connection.close()

    return render_template(
        'profile.html',
        user=user,
        edit_basic=edit_basic,
        edit_address=edit_address,
        edit_card=edit_card
    )


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
                request.form['balance']
            ))

            if 'is_local_vendor' in request.form:
                cursor.execute("""
                    INSERT INTO Local_Vendors (email, business_name, business_address_id, customer_service_phone_number)
                    VALUES (?, ?, ?, ?)
                """, (
                    email,
                    request.form['business_name'],
                    request.form['business_address_id'],
                    request.form['customer_service_phone_number']
                ))

        connection.commit()
        connection.close()

        success = "Account created! You can now log in."
        return render_template('register.html', success=success)

    return render_template('register.html')

@app.route('/my-bids', methods=['GET', 'POST'])
def my_bid_page():
    user_email = session.get('email')
    if not user_email:
        pass
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute('''
        SELECT A.Auction_Title, A.Product_Name, B.bid_price
        FROM Auction_Listings A, Bids B
        WHERE B.bidder_email = ? AND B.listing_id = A.Listing_ID''', (user_email,))
    result = cursor.fetchall()
    connection.close()
    print(result)
    return render_template('my-bids.html', email=user_email, listings=result)
@app.route('/my-listings', methods=['POST', 'GET'])
def my_listing():
    user_email = session.get('email')
    if not user_email:
        pass

    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute('''
        SELECT A.Listing_ID, A.Auction_Title, A.Category, A.Reserve_Price, A.Max_bids, A.Status
        FROM Auction_Listings A
        WHERE A.Seller_Email = ?
    ''', (user_email,))
    result = cursor.fetchall()
    connection.close()

    return render_template('my-listings.html', email=user_email, listings=result)


@app.route('/listing-details/<seller_email>/<int:listing_id>')
def listing_details(seller_email, listing_id):
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
        WHERE listing_id = ?
    ''', (listing_id,))
    current_bid_count = cursor.fetchone()[0]

    cursor.execute('''
        SELECT MAX(Bid_price)
        FROM Bids
        WHERE listing_id = ?
    ''', (listing_id,))
    highest_bid = cursor.fetchone()[0] or 0

    # 新增：查 seller 平均评分，方便详情页显示
    ensure_seller_ratings_table()
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

    print(current_bid_count)
    return render_template(
        'listing-details.html',
        item=item,
        bid_count=current_bid_count,
        current_price=highest_bid,
        avg_rating=avg_rating,
        rating_count=rating_count
    )


@app.route('/deactivate-listing/<seller_email>/<int:listing_id>', methods=['POST'])
def deactivate_listing(seller_email, listing_id):
    user_email = session.get('email')
    if not user_email:
        return redirect(url_for('authenticate'))

    if user_email != seller_email:
        return redirect(url_for('my_listing', error='You do not have access to the deactivate listing'))

    try:
        connection = get_connection()
        cursor = connection.cursor()

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


@app.route('/edit-listing/<seller_email>/<int:listing_id>', methods=['GET', 'POST'])
def edit_listing(seller_email, listing_id):
    user_email = session.get('email')

    if not user_email or user_email != seller_email:
        return redirect(url_for('authenticate'))

    if request.method == 'POST':
        connection = get_connection()
        cursor = connection.cursor()

        title = request.form['auction_title']
        prod_name = request.form['product_name']
        cat = request.form['category']
        desc = request.form['description']
        qty = request.form['quantity']
        reserve = request.form['reserve']
        max_b = request.form['max_bids']

        cursor.execute('SELECT 1 FROM Categories WHERE category_name = ?', (cat,))
        if not cursor.fetchone():
            connection.close()
            return "Error: Category does not exist.", 400

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


def get_category_tree():
    """Helper function to get the category tree"""
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
    if not user_email:
        return redirect(url_for('authenticate'))

    if request.method == 'POST':
        title = request.form.get('auction_title')
        p_name = request.form.get('product_name')
        cat = request.form.get('category')
        desc = request.form.get('description')
        qty = int(request.form.get('quantity'))
        reserve = float(request.form.get('reserve'))
        max_b = int(request.form.get('max_bids'))

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
    return render_template('post-item.html', category_tree=category_tree)


if __name__ == "__main__":
    ensure_seller_ratings_table()
    app.run()