from flask import Flask, render_template, request, redirect, url_for, session
from flask_mysqldb import MySQL
import MySQLdb.cursors
import re
from flask_cors import cross_origin
import pandas as pd
import socketio
import pickle


model = pickle.load(open('C:/Users/anura/Desktop/Anurag/Python Project/CODING_PRACTICE/flight_rf.pkl', 'rb'))

# this is the database connection details.

app = Flask(__name__)

app.secret_key = 'this is sparta!'

app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = '123456'
app.config['MYSQL_DB'] = 'pythonlogin'

mysql = MySQL(app)


@app.route('/', methods=['GET', 'POST'])
@cross_origin()
def login():
    msg = ''
    if request.method == 'POST' and 'username' in request.form and 'password' in request.form:
        username = request.form['username']
        password = request.form['password']

        try:
            with mysql.connection.cursor(MySQLdb.cursors.DictCursor) as cursor:
                sql = "SELECT * FROM accounts WHERE username = %s AND password = %s"
                cursor.execute(sql, (username, password))
                account = cursor.fetchone()

                if account:
                    session['loggedin'] = True
                    session['id'] = account['id']
                    session['username'] = account['username']
                    return redirect(url_for('home1'))
                else:
                    msg = 'Incorrect username/password!'
        except mysql.connector.Error as err:
            # Handle database errors (e.g., connection issues, query execution errors)
            msg = f"Database error: {err}"

    return render_template('index.html', msg=msg)


# THIS IS CODES FOR LOGOUT FROM THE WEBPAGES
@app.route('/pythonlogin/logout')
def logout():
    # Remove session data, this will log the user out
    session.pop('loggedin', None)
    session.pop('id', None)
    session.pop('username', None)
    # Redirect to login page
    return redirect(url_for('login'))


# this will be the registration page, we need to use both GET and POST requests
@app.route('/pythonlogin/register', methods=['GET', 'POST'])
def register():
    # Output message if something goes wrong...
    msg = ''
    with mysql.connection.cursor(MySQLdb.cursors.DictCursor) as cursor:

        # Check if "username", "password" and "email" POST requests exist (user submitted form)
        if request.method == 'POST' and 'username' in request.form and 'password' in request.form and 'email' in request.form:
            # Create variables for easy access
            username = request.form['username']
            password = request.form['password']
            email = request.form['email']
            import uuid
            unique_id = str(uuid.uuid4())
            cursor.execute('INSERT INTO accounts (id, username, password, email) VALUES (%s, %s, %s, %s)',
                           (unique_id, username, password, email,))

            # Check if account exists using MySQL


            account = cursor.fetchone()
            # If account exists show error and validation checks
            if account:
                msg = 'Account already exists!'
            elif not re.match(r'[^@]+@[^@]+\.[^@]+', email):
                msg = 'Invalid email address!'
            elif not re.match(r'[A-Za-z0-9]+', username):
                msg = 'Username must contain only characters and numbers!'
            elif not username or not password or not email:
                msg = 'Please fill out the form!'
            else:
                # Account doesn't exist and the form data is valid, now insert new account into accounts table
                import uuid
                unique_id = str(uuid.uuid4())
                cursor.execute('INSERT INTO accounts (id, username, password, email) VALUES (%s, %s, %s, %s)',
                               (unique_id, username, password, email,))
                mysql.connection.commit()
                msg = 'You have successfully registered!'
        elif request.method == 'POST':
            # Form is empty... (no POST data)
            msg = 'Please fill out the form!'
        # Show registration form with message (if any)
        return render_template('register.html', msg=msg)


@app.route('/pythonlogin/home1', methods=['GET', 'POST'])
@cross_origin()
def home1():
    # Check if user is loggedin
    if 'loggedin' in session:
        # User is loggedin show them the home page
        return render_template('home1.html', username=session['username'])
    return redirect(url_for('login'))


# this will be the home page for price page in the application, only accessible for loggedin users
@app.route('/pythonlogin/home', methods=['GET', 'POST'])
@cross_origin()
def home():
    # Check if user is loggedin
    if 'loggedin' in session:
        # User is loggedin show them the home page
        return render_template('home.html', username=session['username'])
    return redirect(url_for('Price_predication'))

    # User is not logged in redirect to login page


@app.route('/pythonlogin/Price_Prediction', methods=['GET', 'POST'])
@cross_origin()
def Price_prediction():
    msg = ''
    # Check if "username" and "password" POST requests exist (user submitted form)
    if request.method == 'POST' and 'username' in request.form and 'password' in request.form:
        # Create variables for easy access
        username = request.form['username']
        password = request.form['password']
        # Check if account exists using MySQL
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM accounts WHERE username = %s AND password = %s', (username, password,))
        # Fetch one record and return result
        account = cursor.fetchone()
        # If account exists in accounts table in out database
        if account:
            # Create session data, we can access this data in other routes
            session['loggedin'] = True
            session['id'] = account['id']
            session['username'] = account['username']
            # Redirect to home page
            return redirect(url_for('home'))
        else:
            # Account doesn't exist or username/password incorrect
            msg = 'Incorrect username/password!'
    return render_template('price.html', msg=msg)


#this function is for price predictions for the journey


@app.route('/predict', methods=['GET', 'POST'])
@cross_origin()
def predict():
    if request.method == 'POST':
        dep_time = request.form['Dep_Time']

        Journey_day = pd.to_datetime(dep_time, format="%Y-%m-%dT%H:%M").day
        Journey_month = pd.to_datetime(dep_time, format="%Y-%m-%dT%H:%M").month

        Departure_hour = pd.to_datetime(dep_time, format="%Y-%m-%dT%H:%M").hour
        Departure_min = pd.to_datetime(dep_time, format="%Y-%m-%dT%H:%M").minute

        arrival_time = request.form['Arrival_Time']
        Arrival_hour = pd.to_datetime(arrival_time, format="%Y-%m-%dT%H:%M").hour
        Arrival_min = pd.to_datetime(arrival_time, format="%Y-%m-%dT%H:%M").minute

        Total_stops = int(request.form['stops'])

        dur_hour = abs(Arrival_hour - Departure_hour)
        dur_min = abs(Arrival_min - Departure_min)

        airline = request.form['airline']
        if airline == 'Jet Airways':
            Jet_Airways = 1
            IndiGo = 0
            Air_India = 0
            Multiple_carriers = 0
            SpiceJet = 0
            Vistara = 0
            GoAir = 0
            Multiple_carriers_Premium_economy = 0
            Jet_Airways_Business = 0
            Vistara_Premium_economy = 0
            Trujet = 0

        elif airline == 'IndiGo':
            Jet_Airways = 0
            IndiGo = 1
            Air_India = 0
            Multiple_carriers = 0
            SpiceJet = 0
            Vistara = 0
            GoAir = 0
            Multiple_carriers_Premium_economy = 0
            Jet_Airways_Business = 0
            Vistara_Premium_economy = 0
            Trujet = 0

        elif airline == 'Air India':
            Jet_Airways = 0
            IndiGo = 0
            Air_India = 1
            Multiple_carriers = 0
            SpiceJet = 0
            Vistara = 0
            GoAir = 0
            Multiple_carriers_Premium_economy = 0
            Jet_Airways_Business = 0
            Vistara_Premium_economy = 0
            Trujet = 0

        elif airline == 'Multiple carriers':
            Jet_Airways = 0
            IndiGo = 0
            Air_India = 0
            Multiple_carriers = 1
            SpiceJet = 0
            Vistara = 0
            GoAir = 0
            Multiple_carriers_Premium_economy = 0
            Jet_Airways_Business = 0
            Vistara_Premium_economy = 0
            Trujet = 0

        elif airline == 'SpiceJet':
            Jet_Airways = 0
            IndiGo = 0
            Air_India = 0
            Multiple_carriers = 0
            SpiceJet = 1
            Vistara = 0
            GoAir = 0
            Multiple_carriers_Premium_economy = 0
            Jet_Airways_Business = 0
            Vistara_Premium_economy = 0
            Trujet = 0

        elif airline == 'Vistara':
            Jet_Airways = 0
            IndiGo = 0
            Air_India = 0
            Multiple_carriers = 0
            SpiceJet = 0
            Vistara = 1
            GoAir = 0
            Multiple_carriers_Premium_economy = 0
            Jet_Airways_Business = 0
            Vistara_Premium_economy = 0
            Trujet = 0

        elif airline == 'GoAir':
            Jet_Airways = 0
            IndiGo = 0
            Air_India = 0
            Multiple_carriers = 0
            SpiceJet = 0
            Vistara = 0
            GoAir = 1
            Multiple_carriers_Premium_economy = 0
            Jet_Airways_Business = 0
            Vistara_Premium_economy = 0
            Trujet = 0

        elif airline == 'Multiple carriers Premium economy':
            Jet_Airways = 0
            IndiGo = 0
            Air_India = 0
            Multiple_carriers = 0
            SpiceJet = 0
            Vistara = 0
            GoAir = 0
            Multiple_carriers_Premium_economy = 1
            Jet_Airways_Business = 0
            Vistara_Premium_economy = 0
            Trujet = 0

        elif airline == 'Jet Airways Business':
            Jet_Airways = 0
            IndiGo = 0
            Air_India = 0
            Multiple_carriers = 0
            SpiceJet = 0
            Vistara = 0
            GoAir = 0
            Multiple_carriers_Premium_economy = 0
            Jet_Airways_Business = 1
            Vistara_Premium_economy = 0
            Trujet = 0

        elif airline == 'Vistara Premium economy':
            Jet_Airways = 0
            IndiGo = 0
            Air_India = 0
            Multiple_carriers = 0
            SpiceJet = 0
            Vistara = 0
            GoAir = 0
            Multiple_carriers_Premium_economy = 0
            Jet_Airways_Business = 0
            Vistara_Premium_economy = 1
            Trujet = 0

        elif airline == 'Trujet':
            Jet_Airways = 0
            IndiGo = 0
            Air_India = 0
            Multiple_carriers = 0
            SpiceJet = 0
            Vistara = 0
            GoAir = 0
            Multiple_carriers_Premium_economy = 0
            Jet_Airways_Business = 0
            Vistara_Premium_economy = 0
            Trujet = 1

        else:
            Jet_Airways = 0
            IndiGo = 0
            Air_India = 0
            Multiple_carriers = 0
            SpiceJet = 0
            Vistara = 0
            GoAir = 0
            Multiple_carriers_Premium_economy = 0
            Jet_Airways_Business = 0
            Vistara_Premium_economy = 0
            Trujet = 0

        Source = request.form["Source"]
        if Source == 'Delhi':
            s_Delhi = 1
            s_Kolkata = 0
            s_Mumbai = 0
            s_Chennai = 0

        elif Source == 'Kolkata':
            s_Delhi = 0
            s_Kolkata = 1
            s_Mumbai = 0
            s_Chennai = 0

        elif Source == 'Mumbai':
            s_Delhi = 0
            s_Kolkata = 0
            s_Mumbai = 1
            s_Chennai = 0

        elif Source == 'Chennai':
            s_Delhi = 0
            s_Kolkata = 0
            s_Mumbai = 0
            s_Chennai = 1

        else:
            s_Delhi = 0
            s_Kolkata = 0
            s_Mumbai = 0
            s_Chennai = 0

        Destination = request.form["Destination"]
        if Destination == 'Cochin':
            d_Cochin = 1
            d_Delhi = 0
            d_Hyderabad = 0
            d_Kolkata = 0

        elif Destination == 'Delhi':
            d_Cochin = 0
            d_Delhi = 1
            d_Hyderabad = 0
            d_Kolkata = 0

        elif Destination == 'Hyderabad':
            d_Cochin = 0
            d_Delhi = 0
            d_Hyderabad = 1
            d_Kolkata = 0

        elif Destination == 'Kolkata':
            d_Cochin = 0
            d_Delhi = 0
            d_Hyderabad = 0
            d_Kolkata = 1

        else: #Banglore
            d_Cochin = 0
            d_Delhi = 0
            d_Hyderabad = 0
            d_Kolkata = 0

        output = model.predict([[Total_stops,
                                 Journey_day,
                                 Journey_month,
                                 Departure_hour,
                                 Departure_min,
                                 Arrival_hour,
                                 Arrival_min,
                                 dur_hour,
                                 dur_min,
                                 Air_India,
                                 GoAir,
                                 IndiGo,
                                 Jet_Airways,
                                 Jet_Airways_Business,
                                 Multiple_carriers,
                                 Multiple_carriers_Premium_economy,
                                 SpiceJet,
                                 Trujet,
                                 Vistara,
                                 Vistara_Premium_economy,
                                 s_Chennai,
                                 s_Delhi,
                                 s_Kolkata,
                                 s_Mumbai,
                                 d_Cochin,
                                 d_Delhi,
                                 d_Hyderabad,
                                 d_Kolkata]])

        output = round(output[0], 2)
        return render_template('home.html', predictions='You will have to Pay approx Rs. {}'.format(output))
    return redirect(url_for('Price_predication'))


# this will be the profile page, only accessible for loggedin users
@app.route('/pythonlogin/profile')
def profile():
    # Check if user is loggedin
    if 'loggedin' in session:
        # We need all the account info for the user so we can display it on the profile page
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM accounts WHERE id = %s', (session['id'],))
        account = cursor.fetchone()
        # Show the profile page with account info
        return render_template('profile.html', account=account)
    # User is not loggedin redirect to login page
    return redirect(url_for('login'))


if __name__ == '__main__':
    app.run(debug=True)
