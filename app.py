from flask import Flask, render_template, request, session, redirect
import sqlite3
from sqlite3 import Error
from flask_bcrypt import Bcrypt

DB_NAME = "rugby.db"

app = Flask(__name__)
bcrypt = Bcrypt(app)
app.secret_key = "a"


def create_connection(db_file):
    """create a connection to the sqlite db"""
    try:
        connection = sqlite3.connect(db_file)
        connection.execute('pragma foreign_keys=ON')
        return connection
    except Error as e:
        print(e)

    return None


@app.route('/')  #displays the home page
def home():
    return render_template('home.html', logged_in=is_logged_in())


@app.route('/logoff', methods=["GET", "POST"]) #logs off when pressed
def logoff():
    if request.method == "GET":
        if is_logged_in():
            session.pop('email', None)  #deletes the email of the current session
            session.pop('team', None)  #deletes the team of the current session
            print("logged out")
        return redirect('/login')  #returns to the logging page


@app.route('/login', methods=["GET", "POST"])
def login():
    if request.method == "GET":  #displays the loggin page
        return render_template('login.html')

    if is_logged_in():
        email = session['email']  #gets the emails sesion
        print(email)
        query = """SELECT team, roll FROM user WHERE email = ?""" #updates the team name and email from the user table for the curent session
        con = create_connection(DB_NAME)
        cur = con.cursor()
        cur.execute(query, (email,))
        user_data = cur.fetchall()
        con.close()
        team = user_data[0][0]
        roll = user_data[0][1]
        session['team'] = team
        session['roll'] = roll
        print(team)
        print(roll)
        return redirect('/')

    if request.method == "POST":
        email = request.form['email'].strip().lower()  #gets the email from the form
        password = request.form['password'].strip()  #gets the password from the form

        query = """SELECT id, fname, password, team, roll FROM user WHERE email = ?"""  #gets the user data from the assigned email
        con = create_connection(DB_NAME)
        cur = con.cursor()
        cur.execute(query, (email,))
        user_data = cur.fetchall()
        con.close()
        try:  #sets the user data as variables
            userid = user_data[0][0]
            firstname = user_data[0][1]
            db_password = user_data[0][2]
            team = user_data[0][3]
            roll = user_data[0][4]
        except IndexError:
            return redirect("/login?error=Email+invalid+or+password+incorrect")

        if not bcrypt.check_password_hash(db_password, password):  #checks the password is correct for the email provided
            return redirect(request.referrer + "?error=Email+invalid+or+password+incorrect")

        session['email'] = email  #assigns the gamedata to the current session
        session['userid'] = userid
        session['firstname'] = firstname
        session['team'] = team
        session['roll'] = roll
        return redirect('/')  #returns to the home page

    return render_template('login.html', logged_in=is_logged_in())  #displays the login page


@app.route('/signup', methods=["GET", "POST"])
def signup():
    if request.method == "GET":
        return render_template('signup.html')  #displays the signup page

    if request.method == "POST":
        print(request.form)
        fname = request.form.get('fname')  #gets the data from the form
        lname = request.form.get('lname')
        email = request.form.get('email')
        password = request.form.get('password')
        password2 = request.form.get('password2')
        roll = request.form.get('roll')
        team = request.form.get('team')

        if password != password2:  #checks that the passwords are the same
            return redirect('/signup?error=Passwords+dont+match')

        if len(password) < 8:  #checks that the password is longer that 8 characters
            return redirect('/signup?error=Password+must+be+8+characters+or+more')

        hashed_password = bcrypt.generate_password_hash(password)

        con = create_connection(DB_NAME)

        query = "INSERT INTO user(id, fname, lname, email, password, roll, team) " \
                "VALUES(NULL,?,?,?,?,?,?)"  #assigns the data to the user table

        cur = con.cursor()
        try:
            cur.execute(query, (fname, lname, email, hashed_password, roll, team))  #this line actually executes the query
        except sqlite3.IntegrityError:
            return redirect('/signup?error=Email+is+already+used')

        con.commit()
        con.close()
        return redirect('/login')  #opens the login page


@app.route('/data', methods=["GET", "POST"])
def data():
    if request.method == "GET":
        if is_logged_in():  #checks if user is logged in
            team = session['team']
            roll = session['roll']
            print(team)
            print(roll)
            query = """SELECT game_id, opposition,tries_conceded, tries_scored,tackles_made, tackles_missed,turn_overs_made password FROM gamedata  WHERE team = ?"""  #assigns data lists to a variable
            con = create_connection(DB_NAME)
            cur = con.cursor()
            cur.execute(query, (team,))
            team_data = cur.fetchall()
            con.close()
            return render_template('data.html', team_data=team_data,roll=roll )  #opens the data page
        else:
            return redirect("/login?error=Email+invalid+or+password+incorrect")  #returns an error


@app.route('/coach', methods=["GET", "POST"])
def coach():
    if request.method == "GET":
        return render_template('coach.html')  #opens the coach page

    team = session['team']
    roll = session['roll']
    if request.method == "POST":
        triesscored = request.form.get('tries scored')  #assigns the data from the form to variables
        triesconceded = request.form.get('tries conceded')
        opposition = request.form.get('opposition')
        tacklesmade = request.form.get('tackles made')
        tacklesmissed = request.form.get('tackles missed')
        turnover = request.form.get('turnover')
        con = create_connection(DB_NAME)
        query = "INSERT INTO gamedata(opposition, tries_conceded, tries_scored, tackles_made, tackles_missed, turn_overs_made, game_id, team) " \
                "VALUES(?,?,?,?,?,?,NULL,?)"  #inserts variables into the gamedata table

        cur = con.cursor()
        try:
            cur.execute(query, (opposition, triesconceded, triesscored, tacklesmade, tacklesmissed, turnover, team))  #this line actually executes the query
        except sqlite3.IntegrityError:
            return redirect('/coach?error=Invalid+Data')  #rteturns an error

        con.commit()
        con.close()
        return redirect('/data')


def is_logged_in():
    if session.get("email") is None:  #checks if user is logged in
        print("not logged in")
        return False
    else:
        print("logged in")
        return True

app.run(host='127.0.0.1', debug=True)