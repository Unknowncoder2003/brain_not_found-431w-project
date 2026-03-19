import hashlib
from unittest import result

from flask import Flask, render_template, request
import sqlite3 as sql

app = Flask(__name__)

host = 'http://127.0.0.1:5000/'


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/name', methods=['POST', 'GET'])
def name():
    error = None
    if request.method == 'POST':
        result = valid_name(request.form['FirstName'], request.form['LastName'])
        if result:
            return render_template('input.html', error=error, result=result)
        else:
            error = 'invalid input name'
    return render_template('input.html', error=error)

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

@app.route('/name', methods=['POST', 'GET'])
def authenticate():
    error = None
    #when click the login button the authenticate stuff occur
    if request.method == 'POST':
        #valid_email_password(request.form['Email'], request.form['Password'])
        #if match then goes to welcome
        #if not match stay in the same page and have error message
        pass

    return  render_template('input.html', error=error)

def password_to_hash_checker(email, password):
    """Helper function for checking the user entered password and verify it against the database"""
    connection = sql.connect('database.db')
    cursor = connection.cursor()
    cursor.execute('SELECT password, salt FROM Users WHERE email = ?', (email,)) #finds the hashed password for the provided username
    result = cursor.fetchone()
    connection.close()
    if result is None:
        #the username is incorrect or not in the databse
            return False
    stored_hash, salt = result
    password_and_salt = (password + salt).encode('utf-8')
    user_input_hash = hashlib.sha256(password_and_salt).hexdigest()
    return user_input_hash == stored_hash
if __name__ == "__main__":
    app.run()


