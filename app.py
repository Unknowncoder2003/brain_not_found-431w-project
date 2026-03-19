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


def valid_name(first_name, last_name):
    connection = sql.connect('database.db')
    connection.execute('CREATE TABLE IF NOT EXISTS users(firstname TEXT, lastname TEXT);')
    connection.execute('INSERT INTO users (firstname, lastname) VALUES (?,?);', (first_name, last_name))
    connection.commit()
    cursor = connection.execute('SELECT * FROM users;')
    return cursor.fetchall()

def valid_email_password(username, password):
    connection = sql.connect('database.db')
    email = connection.execute('SELECT email FROM users;')
    password = connection.execute('SELECT password FROM users;')
    return None

@app.route('/name', methods=['POST', 'GET'])
def authenticate(username, password):
    error = None
    #when click the login button the authenticate stuff occur
    if request.method == 'POST':
        #valid_email_password(username, password)
        #if match then goes to welcome
        #if not match stay in the same page and have error message
        pass

    return  render_template('input.html', error=error)

if __name__ == "__main__":
    app.run()


