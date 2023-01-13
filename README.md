<h3 align="center">
<img src="static/images/logo512.png" width="64" height="64">
</h3>
<br><br>

## payChckr

A user-friendly web application designed for workers to easily track and manage their daily working shifts. The application allows you to input your shift details, including start and end times, and calculates your daily working hours and pay using the individual tax regulations from Victoria, Australia. You can view your gross earnings, net earnings, and taxes, as well as total hours worked for any chosen date range. With PayCheckr, keeping track of your pay has never been easier. It's the perfect tool for any worker looking to stay organized and in control of their earnings. Whether you're a freelancer, part-time employee, or full-time worker, PayCheckr has got you covered.

## Features

- Input and track your working shifts
- Calculate your daily working hours and pay
- View your gross earnings, net earnings, taxes, and total hours worked for any chosen date range

> Note that this app uses the Victorian taxes regulations for individuals in Australia. It generates marginal earnings and marginal taxes. No matter if you are threesholding for $18k, the app will deduct taxes at all times.

## Build
<img    src="https://cdn.jsdelivr.net/gh/devicons/devicon/icons/python/python-original.svg" alt="python logo" width="40px" height="40px" />
<img src="https://cdn.jsdelivr.net/gh/devicons/devicon/icons/flask/flask-original.svg" alt="flask logo" width="40px" height="40px" />
<img src="https://cdn.jsdelivr.net/gh/devicons/devicon/icons/sqlalchemy/sqlalchemy-original.svg" alt="sqlalchemy logo" width="40px" height="40px" />
<img src="https://cdn.jsdelivr.net/gh/devicons/devicon/icons/javascript/javascript-plain.svg" alt="javascript logo" width="40px" height="40px"/>
<img src="https://cdn.jsdelivr.net/gh/devicons/devicon/icons/bootstrap/bootstrap-original.svg" alt="bootstrap logo" width="40px" height="40px" />
<img src="https://cdn.jsdelivr.net/gh/devicons/devicon/icons/sass/sass-original.svg" alt="sass logo" width="40px" height="40px" />

## Install

```sh
git clone 
npm --save-dev install
pip install Flask
pip install Flask_Session
pip install --pre SQLAlchemy
```
You can also create a virtual environement using python
```sh
python3 -m venv /path/to/new/virtual/environment
source venv/bin/activate
pip -r requirements.txt
```
Usage of the scripts in the `package.json`:

```
"compile:sass":"sass --watch scss:dst/
```

```
{
  "name": "cms",
  "version": "1.0.0",
  "description": "Check My Shift allows users to track and analyse their working shift values to ensure accuracy between the employer and the employee.",
  "main": "index.js",
  "scripts": {
    "compile:sass":"sass --watch scss:static/",
    "dev":"parcel templates/index.html",
    "build": "parcel build templates/index.html"
  },
  "keywords": [
    "python",
    "flask",
    "sqlalchemy",
    "werkzeug",
    "bootstrap",
    "sass"
  ],
  "author": "Farlane Badache",
  "license": "ISC",
  "devDependencies": {
    "autoprefixer": "^10.4.13",
    "bootstrap": "^5.2.3",
    "postcss-cli": "^10.1.0",
    "sass": "^1.57.1"
  }
}
```
## Project
The application uses flask and sql-Alchemy to reach database safely. The tree below showcases the file structure and is ommiting the `node_modules` and the `__pychache__` folders.

This version of the app only uses `en` as language but I will be 
making the app in `fr` using French taxes regulations.

The app uses the filesytem not cookies and it does not cache responses.


### app setup
```
# APP Imports
from flask import Flask, request, render_template, session, redirect, url_for, flash
from flask_session import Session as Session_flask
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from tempfile import mkdtemp
from datetime import date, datetime
import datetime
import re

# CLASSES, HELPERS & CONST IMPORTS
from helpers import TAX, SUPER, MEDICARE_LEVY
from helpers import calculator, penalties, overtime
from helpers import login_required, apology
from helpers import getCurrent_Dates
from classes import Shift, cardShift

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
```

### db access
Session
```
# DB Imports
from sqlalchemy.orm import sessionmaker, scoped_session

#DB MAIN SESSION
engine = create_engine("sqlite:///cms.db", echo=False)
session_factory = sessionmaker(bind=engine)
Session = scoped_session(session_factory)
```
>Note that this version has a unique session imported to the entire project due to the limitation of sqlite.


### Views
- register
- login
- index
- load
  - edit
  - delete
- summary
- profile

The app mainly create datetime objects and database orm's (Shifts, Users). I also created extra classes to help for the rendering of the data. It is compatible with Chart.js as I can restructure the data to lists.

#### The summary view
```
@app.route('/summary')
@login_required
def summary():

    if request.args.get('viewDate1') and request.args.get('viewDate2'):
        myDate1 = datetime.datetime.strptime(request.args.get('viewDate1'), '%Y-%m-%d')
        myDate2 = datetime.datetime.strptime(request.args.get('viewDate2'), '%Y-%m-%d')
    
    else:
        dates = getCurrent_Dates(date.today(), 'week')
        myDate1 = dates[0]
        myDate2 = dates[1]

    shifts = dbSession.query(Shifts).filter_by(user_id = session['user_id']).filter(Shifts.date >= myDate1).filter(Shifts.date <= myDate2).all()
    cardShifts = cardShift(shifts)

    return render_template('summary.html',shifts = shifts, currentnet_earnings = sum(cardShifts.net_earnings), currentTaxes = sum(cardShifts.taxes), currentHours = sum(cardShifts.hours), myDate1 = myDate1, myDate2 = myDate2)

```

### Classes
- Users ORM:
```
class Users(Base):
    __tablename__ = 'users'
    id = Column('id', Integer, primary_key=True)
    username = Column('username', String, unique=True)
    password = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False)
    workplace = Column(String, nullable=False)
    payrate = Column(Float, nullable=True, unique=False)
    overtime = Column(Integer, nullable=True, unique=False)
    penalties = Column(Integer, nullable=True, unique=False)
    paid_break = Column(Integer, nullable=True, unique=False)
    annual_salary = Column(Integer, nullable=True, unique=False)
    weekly_hours = Column(Integer, nullable=True, unique=False)
    
    shifts = relationship('Shifts', backref='users')
    earnings = relationship('Earnings', backref='users')

    def __init__(self, username, password, email, workplace, payrate = None, overtime = None, penalties = None, paid_break = None, annual_salary = None, weekly_hours = None):
        self.username = username
        self.password = password
        self.email = email
        self.workplace = workplace
        self.payrate = payrate
        self.overtime = overtime
        self.penalties = penalties
        self.paid_break = paid_break
        self.annual_salary = annual_salary
        self.weekly_hours = weekly_hours

    def __repr__(self) -> str:
        return f'User(id={self.id!r}, name={self.username!r})'

```

- Shift Class

```
# Model for shift creation before insert to db
class Shift:
    
    # Data Members
    shiftDate = datetime
    startShift = 0.00
    endShift = 0.00
    breakShift = 0.00
    lengthShift = 0.00
    
    # Constructor
    def __init__(self, shiftDate, startShift, endShift, breakShift, penalties = 0):
        self.shiftDate = shiftDate
        self.startShift = strtoint(startShift)
        self.endShift = strtoint(endShift)
        self.breakShift = strtoint(breakShift)
        self.tmp_length = self.endShift - self.startShift
        self.penalties = penalties
        if penalties:
            # if shift is between 3 and 5hrs
            if self.tmp_length >= 3 and self.tmp_length <= 5:
                # if break is not over 15mins
                if self.breakShift <= 0.25:
                    self.lengthShift = self.tmp_length
                else:
                    self.lengthShift = self.tmp_length - (breakShift - 0.25)
            # if shift is between 5 and 7hrs
            elif self.tmp_length > 5 and self.tmp_length <= 7:
                # if break is under or equal to 45mins (30mins unpaid + 15mins paid)
                if self.breakShift <= 0.75:
                    self.lengthShift = self.tmp_length - 0.50
                else:
                    self.lengthShift = (self.tmp_length - 0.50) - ((breakShift - 0.50) - 0.25)
            # if shift is between 7 and 9hrs
            elif self.tmp_length >= 7 and self.tmp_length <= 9:
                # if break is inferior or equal to 1 hr
                if self.breakShift <= 1:
                    self.lengthShift = self.tmp_length - 0.75
                else:
                    self.lengthShift = (self.tmp_length - 0.75) - ((breakShift - 0.75) - 0.25)
            # Shift over 10 hours
            else:
                if self.breakShift <= 2:
                    self.lengthShift = self.tmp_length - 2
                else:
                    self.lengthShift = (self.tmp_length - 2) - ((breakShift - 2))
        else:
            self.lengthShift = (self.endShift - self.startShift) - self.breakShift

```


### Helpers
There is a few helpers, to get dates and to create shift models

```
# Overtime indications to create marginal shift values
def overtime(shift, day, user):
    
    if shift.shiftDate in PUBLIC_HOLIDAYS:
        return calculator(round(shift.lengthShift,3),user.payrate * 2.0)
    elif day[3:] != 'Sun':
        return calculator(round(shift.lengthShift,3),user.payrate * 1.5)
    else:
        if shift.lengthShift > 3:
            return calculator(3,user.payrate * 1.5) + calculator(round(shift.lengthShift,3) - 3, user.payrate * 2)
        else:
            return calculator(round(shift.lengthShift,3),user.payrate * 1.5)

```
### Tree
```
├── app.py
├── classes.py
├── db
│   ├── cms.db
│   ├── db.py
│   └── __pycache__
│       └── db.cpython-310.pyc
├── helpers.py
├── package.json
├── package-lock.json
├── README.md
├── scss
│   ├── components
│   │   ├── _animations.scss
│   │   ├── _buttons.scss
│   │   ├── _mixins.scss
│   │   └── _typography.scss
│   ├── _custom.scss
│   ├── sections
│   │   ├── _main_reports.scss
│   │   ├── _navbar.scss
│   │   ├── _profile.scss
│   │   ├── _registration_form.scss
│   │   ├── _shift_form.scss
│   │   └── _shift_table.scss
│   └── styles.scss
├── static
│   ├── bootstrap.bundle.js
│   ├── bootstrap.bundle.js.map
│   ├── images
│   ├── main.js
│   ├── registrationform.js
│   ├── styles.css
│   └── styles.css.map
└── templates
    ├── apology.html
    ├── edit.html
    ├── index.html
    ├── layout.html
    ├── load.html
    ├── login.html
    ├── profile.html
    ├── register.html
    └── summary.html

8 directories, 36 files
```

###
## 🤹‍♂️ Author

**Farlane Badache**

* Website: [ziscoplankton](https://ziscoplankton.github.io)
* Github: [@ziscoplankton](https://github.com/ziscoplankton)
* Paychckr: [paychckr](https://ziscoplankton.pythonanywhere.com)
## Support

Give a ⭐️ if this project helped you in anyways or if you just liked it!


## Contribute

If you have any suggestions or improvements, please feel free to submit a pull request.
