import email
import hashlib
from unittest import result

from flask import Flask, render_template, request,redirect, url_for,session
import sqlite3 as sql

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
        pass  # not showing for debugging purpose
        # return redirect(url_for('authenticate'))  # Redirect to login if they aren't logged in

    return render_template('seller.html')
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
    if user_email:
        femail = user_email
    else:
        femail = "lsuhelpdeskStaff@lsu.edu"  # Fallback email
    return render_template('helpdesk.html', email=femail)
if __name__ == "__main__":
    app.run()