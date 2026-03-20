import hashlib
from unittest import result

from flask import Flask, render_template, request
import sqlite3 as sql

app = Flask(__name__)

host = 'http://127.0.0.1:5000/'


@app.route('/')
def index():
    return render_template('index.html')

@app.route('/bidder')
def bidder():
    return render_template('bidder.html')

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
    #when click the login button the authenticate stuff occur
    if request.method == 'POST':
        # result1 = valid_email_password(request.form['Email'], request.form['Password'])
        result2 = password_to_hash_checker(request.form['email'], request.form['password'])
        print(result2)
        # if result1 == True and result2 = True: go to welcome.html
        if result2:
            return render_template(find_user_html(request.form['email']), error=error)
        # if not match stay in the same page and have error message or go to another html?
        else:
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
        #the username is incorrect or not in the databse
            print("No matching user.")
            return False
    stored_hash, salt = result
    salt = salt
    stored_hash = stored_hash
    password_and_salt = (password.strip() + salt).encode('utf-8')
    user_input_hash = hashlib.sha256(password_and_salt).hexdigest()
    print(f"Stored Hash: '{stored_hash}' (Length: {len(stored_hash)})")
    print(f"Input  Hash: '{user_input_hash}' (Length: {len(user_input_hash)})")
    print(f"Input Password: '{password}'")
    print(f"Salt Used:   '{salt}' (Length: {len(salt)})")
    return user_input_hash == stored_hash
def find_user_html(email):
    connection = sql.connect('database.db')
    cursor = connection.cursor()
    #Check if the user is Helpdesk staff
    cursor.execute("SELECT 1 FROM Helpdesk WHERE email = ?", (email,))
    if cursor.fetchone():
        connection.close()
        return "helpdesk.html"
    #Check if the user is a Seller
    cursor.execute("SELECT 1 FROM Sellers WHERE email = ?", (email,))
    if cursor.fetchone():
        connection.close()
        return "seller.html"
    #Check if the user is a Bidder
    cursor.execute("SELECT 1 FROM Bidders WHERE email = ?", (email,))
    if cursor.fetchone():
        connection.close()
        return "bidder.html"
    # Default fallback if email is not found in any role table
    connection.close()
    return "index.html"
if __name__ == "__main__":
    app.run()


