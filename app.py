# APP Imports
from flask import Flask, request, render_template, session, redirect, url_for, flash
from flask_session import Session as Session_flask
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from tempfile import mkdtemp
from datetime import date, datetime
import datetime
import re

# DB Imports
from db.db import Session
from db.db import Users, Earnings, Shifts

# CLASSES, HELPERS & CONST IMPORTS
from helpers import TAX, SUPER, MEDICARE_LEVY
from helpers import calculator, penalties, overtime
from helpers import login_required, apology
from helpers import getCurrent_Dates
from classes import Shift, cardShift

# DB SESSION
dbSession = Session()

# APP DEV SET-UP FOR AUTO RELOADS
# Source CS50
app = Flask(__name__)
app.config["TEMPLATES_AUTO_RELOAD"] = True
app.jinja_env.auto_reload = True

# NO CACHE RESPONSES
# Source: CS50
@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


#FILESYSTEM NO COOKIES
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session_flask(app)

session_flask_user = Session_flask(app)

# ROUTES

# REGISTER
@app.route('/register', methods=['POST','GET'])
def register():
    if request.method == 'POST':
        user = dbSession.query(Users).filter_by(username=request.form['username']).first()
        if user:
            return apology('Username not available')
        else:
            if not request.form['payrate'] and (not request.form['salary'] and not request.form['weekly_hours']):
                return apology('Fields missing')
            else:
                if request.form['password'] != request.form['confirmation']:
                    return apology("passwords are different")
                else:
                    regex_check = re.search(r"[a-zA-Z0-9!@#$%^&*]{8,}", request.form.get("password"))
                    if regex_check:
                        if request.form['salary'] != '' and request.form['weekly_hours'] != '':
                            insert = Users(username=request.form['username'], password=generate_password_hash(request.form['password']), email=request.form['email'], workplace = request.form['workplace'], paid_break = 1, annual_salary = request.form['salary'], weekly_hours = request.form['weekly_hours'])
                        elif 'penalties' in request.form and 'overtime' in request.form:
                            insert = Users(username=request.form['username'], password=generate_password_hash(request.form['password']), email=request.form['email'], workplace = request.form['workplace'], payrate = request.form['payrate'], overtime = 1, penalties = 1, paid_break = 1)
                        elif 'penalties' in request.form:
                            insert = Users(username=request.form['username'], password=generate_password_hash(request.form['password']), email=request.form['email'], workplace = request.form['workplace'], payrate = request.form['payrate'], overtime = 0, penalties = 1, paid_break = 1)
                        elif 'overtime' in request.form:
                            insert = Users(username=request.form['username'], password=generate_password_hash(request.form['password']), email=request.form['email'], workplace = request.form['workplace'], payrate = request.form['payrate'], overtime = 1, paid_break = 1)
                        else:
                            insert = Users(username=request.form['username'], password=generate_password_hash(request.form['password']), email=request.form['email'], workplace = request.form['workplace'], payrate = request.form['payrate'])
                    else:
                        return apology("Sorry your password must be 8 characters and have symbols")
                dbSession.add(insert)
                dbSession.commit()
                flash('Your account has been created')
                return redirect('/login')
    else:
        flash('Welcome, please register below to create an account')
        return render_template("register.html", title = 'register')


# LOGIN
@app.route('/login', methods=['POST', 'GET'])
def login():
    session.clear()
    if request.method == 'POST':
        user = dbSession.query(Users).filter_by(email=request.form['email']).first()
        if user:
            if check_password_hash(user.password, request.form['password']):
                session['user_id'] = user.id
                session['name'] = user.username
                session['logged_in'] = True
                return redirect(url_for("index"))
            else:
                return apology('Wrong Password')
        else:
            return apology('User Unknown')
    else:
            flash('Hello there, you can register or login via the menu at the bottom')
            return render_template('login.html')


# LOGOUT
@app.route('/logout')
@login_required
def logout():
    session.clear()
    flash('You are now logged out')
    return redirect('/login')


# ADD SHIFT
@app.route('/load', methods=['GET', 'POST'])
@login_required
def load():
    if request.method == 'GET':
        user = session['user_id']
        return render_template('load.html')
    else:

        if all((checks in request.form for checks in request.form)):
            dateShift = request.form['shift-date']
            startShift = request.form['shift-start']
            endShift = request.form['shift-end']
            breakShift = request.form['shift-break']

            # Init objects from user inputs of class Shift
            # and make dateTime object if user is not under salary
            # AKA SHIFT USER
            user = dbSession.query(Users).filter_by(id=session['user_id']).first()
            dayShift = datetime.datetime.strptime(dateShift, "%Y-%m-%d")
            shift = Shift(dayShift, startShift, endShift, breakShift, user.penalties)
            if shift.lengthShift <= 0:
                flash('The shift values are wrong please review')
                return redirect(url_for("load"))
            else:
                # CALCULATE SHIFT
                if shift:
                    day = dayShift.strftime("%a %d %b %Y")
                    if not user.annual_salary:
                        if user.overtime == 1 and user.penalties == 1:
                            marginal_shift = penalties(shift, day, user)
                        elif user.overtime == 1:
                            marginal_shift = overtime(shift, day, user)
                        elif user.penalties == 1:
                            marginal_shift = penalties(shift, day, user)
                        else:
                            marginal_shift = calculator(round(shift.lengthShift,3), user.payrate)

                        marginal_salary = temp_salary = (marginal_shift*5) * 52
                        marginal_weekly_hrs = shift.lengthShift * 5
                        taxes = ((marginal_salary * MEDICARE_LEVY) / 52) / marginal_weekly_hrs
                        super = ((marginal_salary * SUPER) / 52) / marginal_weekly_hrs
                        while(temp_salary > 18200):
                            if temp_salary >= 18201 and temp_salary <= 45000:
                                taxes += ((((45000 - 18201) * TAX['1845'])/52) /marginal_weekly_hrs) * shift.lengthShift
                                temp_salary = 18200
                            elif temp_salary >= 45001 and temp_salary <= 120000:
                                taxes += ((((marginal_salary-45001) * TAX['45120'])/52) /marginal_weekly_hrs) * shift.lengthShift
                                temp_salary = 18201
                        net_income = marginal_shift - taxes

                    else:
                        marginal_salary = user.annual_salary
                        marginal_shift = calculator(round(shift.lengthShift,3), (marginal_salary/52)/user.weekly_hours)
                        taxes = (marginal_salary * MEDICARE_LEVY / 52) / user.weekly_hours
                        super = (marginal_salary * SUPER / 52) / user.weekly_hours
                        taxes += ((((45000 - 18201) * TAX['1845'])/52) /user.weekly_hours) * shift.lengthShift
                        taxes += ((((marginal_salary-45001) * TAX['45120'])/52) /user.weekly_hours) * shift.lengthShift

                        net_income = marginal_shift - taxes
                    insert_shift = Shifts(date = shift.shiftDate, hours = round(shift.lengthShift,3), start = startShift, end = endShift, gross_income = marginal_shift, taxes = taxes, net_income = net_income, super = marginal_shift * SUPER, user_id = session['user_id'])
                    dbSession.add(insert_shift)
                    dbSession.commit()
                    findShift = dbSession.query(Shifts).filter_by(date = shift.shiftDate).first()
                    insert_earnings = Earnings(user_id=session['user_id'], gross_earnings = marginal_shift, taxes = taxes, net_earnings = net_income, super_earnings = super, shift_id =findShift.id)
                    dbSession.add(insert_earnings)
                    dbSession.commit()
                    flash(f'The shift for the {day} was created')
                    return redirect('/load')
                else:
                    return apology("Something wrong with your shift")
        else:
            return apology("Sorry something went wrong with the checks. Make sure to have a date, a start and a end time")


# HOME
@app.route('/')
@login_required
def index():
    user = dbSession.query(Users).filter_by(id=session['user_id']).first()
    if user:
        currentWeeknet_earnings = 0
        currentWeekHours = 0
        currentWeekTaxes = 0
        currentWeekgross_earnings = 0

        if not request.args.get('viewDate'):
            myDate = date.today()
            # MAKE WEEKLY EARNINGS & SHIFTS
            currentWeekDates = getCurrent_Dates(myDate, 'week')

            currentWeekShifts = dbSession.query(Shifts).filter_by(user_id = session['user_id']).filter(Shifts.date >= currentWeekDates[0]).filter(Shifts.date <= currentWeekDates[1]).all()

        else:
            myDate = datetime.datetime.strptime(request.args.get('viewDate'), '%Y-%m-%d')
            currentWeekDates = getCurrent_Dates(myDate, 'week')
            currentWeekShifts = dbSession.query(Shifts).filter_by(user_id = session['user_id']).filter(Shifts.date >= currentWeekDates[0]).filter(Shifts.date <= currentWeekDates[1]).all()


        if currentWeekShifts:
            for shift in currentWeekShifts:
                currentWeeknet_earnings += shift.net_income
                currentWeekHours += shift.hours
                currentWeekTaxes += shift.taxes
                currentWeekgross_earnings += shift.gross_income
        return render_template("index.html",myDate = myDate, currentHours = currentWeekHours, currentnet_earnings = currentWeeknet_earnings, currentWeekgross_earnings = currentWeekgross_earnings, currentTaxes = currentWeekTaxes)
    else:
        flash('Sorry something is wrong with your session and account, please login again')
        return redirect(url_for("login"))


# VIEWS
@app.route('/summary')
@login_required
def summary():

    if request.args.get('viewDate1') and request.args.get('viewDate2'):
        myDate1 = datetime.datetime.strptime(request.args.get('viewDate1'), '%Y-%m-%d')
        myDate2 = datetime.datetime.strptime(request.args.get('viewDate2'), '%Y-%m-%d')
        flash('Great ! The view is now updated')
    else:
        dates = getCurrent_Dates(date.today(), 'week')
        myDate1 = dates[0]
        myDate2 = dates[1]
        flash('Please choose the dates that you\'d like to view')

    shifts = dbSession.query(Shifts).filter_by(user_id = session['user_id']).filter(Shifts.date >= myDate1).filter(Shifts.date <= myDate2).all()
    cardShifts = cardShift(shifts)

    return render_template('summary.html',shifts = shifts, currentnet_earnings = sum(cardShifts.net_earnings), currentWeekgross_earnings = sum(cardShifts.gross_earnings), currentTaxes = sum(cardShifts.taxes), currentHours = sum(cardShifts.hours), myDate1 = myDate1, myDate2 = myDate2)


# DELETE SHIFT
@app.route('/delete')
@login_required
def delete():
    if request.args.get('id'):
        item = dbSession.query(Shifts).filter_by(user_id = session['user_id']).filter_by(id = int(request.args.get('id'))).delete()
        dbSession.commit()
        flash('You\'ve successfully deleted a shift')
        return redirect('/summary')
    else:
        return apology('Deletion did not worked', 204)


# EDIT SHIFT
@app.route('/edit', methods = ['POST', 'GET'])
@login_required
def edit():

    if request.method == 'POST':
        user = dbSession.query(Users).filter_by(id = session['user_id']).first()
        date = datetime.datetime.strptime(request.form['shift-date'], "%Y-%m-%d")
        shiftToEdit = dbSession.query(Shifts).filter_by(date = date).first()
        earningsToEdit = dbSession.query(Earnings).filter_by(shift_id = shiftToEdit.id).first()
        dayShift = datetime.datetime.strptime(shiftToEdit.date.strftime("%Y-%m-%d"), "%Y-%m-%d")
        if user.penalties:
            penalties = user.penalties
        else:
            penalties = 0

        shift = Shift(dayShift, request.form['shift-start'], request.form['shift-end'], request.form['shift-break'], penalties)
        if shift and shiftToEdit and earningsToEdit:
            day = dayShift.strftime("%a %d %b %Y")
            if not user.annual_salary:
                if user.overtime == 1 and user.penalties == 1:
                    marginal_shift = penalties(shift, day, user)
                elif user.overtime == 1:
                    marginal_shift = overtime(shift, day, user)
                elif user.penalties == 1:
                    marginal_shift = penalties(shift, day, user)
                else:
                    marginal_shift = calculator(round(shift.lengthShift,3), user.payrate)

                marginal_salary = temp_salary = (marginal_shift*5) * 52
                marginal_weekly_hrs = shift.lengthShift * 5
                taxes = ((marginal_salary * MEDICARE_LEVY) / 52) / marginal_weekly_hrs
                super = ((marginal_salary * SUPER) / 52) / marginal_weekly_hrs
                while(temp_salary > 18200):
                    if temp_salary >= 18201 and temp_salary <= 45000:
                        taxes += ((((45000 - 18201) * TAX['1845'])/52) /marginal_weekly_hrs) * shift.lengthShift
                        temp_salary = 18200
                    elif temp_salary >= 45001 and temp_salary <= 120000:
                        taxes += ((((marginal_salary-45001) * TAX['45120'])/52) /marginal_weekly_hrs) * shift.lengthShift
                        temp_salary = 18201
                net_income = marginal_shift - taxes

            else:
                marginal_salary = user.annual_salary
                marginal_shift = calculator(round(shift.lengthShift,3), (marginal_salary/52)/user.weekly_hours)
                taxes = (marginal_salary * MEDICARE_LEVY / 52) / user.weekly_hours
                super = (marginal_salary * SUPER / 52) / user.weekly_hours
                taxes += ((((45000 - 18201) * TAX['1845'])/52) /user.weekly_hours) * shift.lengthShift
                taxes += ((((marginal_salary-45001) * TAX['45120'])/52) /user.weekly_hours) * shift.lengthShift

                net_income = marginal_shift - taxes

            earningsToEdit.gross_earnings = marginal_shift
            earningsToEdit.taxes = taxes
            earningsToEdit.net_earnings = net_income
            earningsToEdit.super_earnings = super
            shiftToEdit.hours = round(shift.lengthShift, 3)
            shiftToEdit.start = request.form['shift-start']
            shiftToEdit.end = request.form['shift-end']
            shiftToEdit.gross_income = marginal_shift
            shiftToEdit.tax = taxes
            shiftToEdit.net_income = net_income
            shiftToEdit.super = marginal_shift * SUPER

            dbSession.commit()
            flash('You\'ve successfully edited a shift')
            return redirect('/summary')
        else:
            return apology('Not authorised', 302)
    else:
        if int(request.args.get('id')):
            shiftToEdit = dbSession.query(Shifts).filter_by(id = request.args.get('id')).first()
            if shiftToEdit:
                return render_template('edit.html', user = session['user_id'], date = shiftToEdit.date.strftime('%Y-%m-%d'))
            else:
                return apology('Shift was not found', 404)
        else:
            return apology('Not authorised', 302)

# EDIT PROFILE
@app.route('/profile', methods =['GET', 'POST'])
@login_required
def profile():
    if request.method == 'GET':
        profile = dbSession.query(Users).filter_by(id = request.args.get('id')).first()
        if profile:
            return render_template('profile.html', profile = profile, user = profile )
        else:
            return apology('User not found', 404)
    else:
        profile = dbSession.query(Users).filter_by(id = request.form['id']).first()
        password = generate_password_hash(request.form['password'])
        if check_password_hash(password, request.form['password']):
            profile.username = request.form['username']
            profile.password = password
            profile.email = request.form['email']
            profile.workplace = request.form['workplace']
            profile.payrate = request.form['payrate']
            if request.form['salary'] != 0:
                profile.salary = request.form['salary']
            elif request.form['weekly_hours'] != 0:
                profile.weekly_hours = request.form['weekly_hours']
            else:
                profile.salary = None
                profile.weekly_hours = None

            dbSession.commit()
            flash('You\'ve successfully updated your profile')
            return redirect('/')
        else:
            return apology('Passwords are not identical', 302)


# Handling errors
# Source CS50
def errorhandler(e):
    """Handle error"""
    if not isinstance(e, HTTPException):
        e = InternalServerError()
    return apology(e.name, e.code)


# Listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)