from flask import render_template, session, redirect
import datetime
from functools import wraps
import calendar
from datetime import date
from db.db import Shifts, Session

# CONSTANTS
PUBLIC_HOLIDAYS = ['2023-01-01', '2023-01-02', '2023-01-26', '2023-03-13', '2023-04-07', '2023-04-08', '2023-04-09', '2023-04-10', '2023-04-25', '2023-06-12', '2023-09-15', '2023-11-07', '2023-12-25', '2023-12-26']
DAYS_COUNTER = {'Mon':0, 'Tue':1, 'Wed': 2, 'Thu': 3, 'Fri': 4, 'Sat': 5, 'Sun': 6}
FORTNIGHT_DAYS = {'Mon': 13, 'Tue': 12, 'Wed': 11, 'Thu': 10, 'Fri': 9, 'Sat': 8, 'Sun': 7}
QUARTER_MONTHS = {'Jul': 0, 'Aug': 1, 'Sep' : 2, 'Oct' : 0 , 'Nov': 1, 'Dec' : 2, 'Jan' : 0, 'Feb' : 1, 'Mar' : 2, 'Apr' : 0, 'May' : 1, 'Jun' : 2}
PREVIOUS_WEEK_DAYS = {'Mon': 7, 'Tue': 8, 'Wed': 9, 'Thu': 10, 'Fri': 11, 'Sat': 12, 'Sun': 13}
PREV_DAYS_COUNTER = {'Mon': 6, 'Tue': 5, 'Wed': 4, 'Thu': 3, 'Fri': 2, 'Sat': 1, 'Sun': 0}
PREV_FORTNIGHT_DAYS = {'Mon': 14, 'Tue': 15, 'Wed': 16, 'Thu': 17, 'Fri': 18, 'Sat': 19, 'Sun': 20}
PREV_QUARTER_MONTHS = {'Jul': 0, 'Aug': 1, 'Sep' : 2, 'Oct' : 3 , 'Nov': 4, 'Dec' : 5, 'Jan' : 3, 'Feb' : 4, 'Mar' : 5, 'Apr' : 3, 'May' : 4, 'Jun' : 5}
TAX = {'1845': 0.19, '45120': 0.325}
SUPER = 0.105
MEDICARE_LEVY = 0.02

# Make PUBLIC_HOLIDAYS STRINGS DATETIME OBJECTS
for i in range(0,13):
    PUBLIC_HOLIDAYS[i] = datetime.datetime.strptime(PUBLIC_HOLIDAYS[i], '%Y-%m-%d')




# DB SESSION
dbSession = Session()




# Login required wrapper
# Source: https://flask.palletsprojects.com/en/1.1.x/patterns/viewdecorators/

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/login")
        return f(*args, **kwargs)
    return decorated_function

# Error page
# Source CS50
def apology(message, code=400):
    """Render message as an apology to user."""
    def escape(s):
        """
        Escape special characters.

        https://github.com/jacebrowning/memegen#special-characters
        """
        for old, new in [("-", "--"), (" ", "-"), ("_", "__"), ("?", "~q"),
                         ("%", "~p"), ("#", "~h"), ("/", "~s"), ("\"", "''")]:
            s = s.replace(old, new)
        return s
    return render_template("apology.html", top=code, bottom=escape(message))

# Local function to change str to int for shift calculations
def strtoint(str):
    nstr = str.replace(':', '')
    hours = ""
    mins = ""
    for char in range(4):
        if char < 2:
            hours = hours + nstr[char]
        else:
            mins = mins + nstr[char]
    mins = int(mins) / 60
    return int(hours) + mins

# Penalty indications to create marginal shift values
def penalties(shift, day, user):

    if shift.shiftDate in PUBLIC_HOLIDAYS:
        return calculator(round(shift.lengthShift,3), user.payrate * 2.0)
    elif day[:3] == 'Sat':
        return calculator(round(shift.lengthShift,3), user.payrate * 1.25)
    elif day[:3] == 'Sun':
        return calculator(round(shift.lengthShift,3), user.payrate * 1.5)
    else:
        # if shift start at 6pm and before 11pm
        if shift.startShift >= 18 and shift.startShift < 23:
            if shift.lengthShift > 5:
                return calculator(5, user.payrate * 1.25) + calculator(round(shift.lengthShift,3) - 5, user.payrate * 1.30)
            else:
                return calculator(shift.lengthShift, user.payrate * 1.25)
        # if shift start at 11pm and before 2am
        elif shift.startShift >= 23 or shift.startShift < 2:
            if shift.lengthShift > 3:
                return calculator(3, user.payrate * 1.30) + calculator(round(shift.lengthShift,3) - 3, user.payrate * 1.125)
            else:
                return calculator(shift.lengthShift, user.payrate * 1.30)
        # if shift start at 2am and before 6am
        elif shift.startShift >= 2 and shift.startShift < 6:
            if shift.lengthShift > 4:
                return calculator(4,user.payrate * 1.125) + calculator(round(shift.lengthShift,3) - 4, user.payrate)
            else:
                return calculator(round(shift.lengthShift,3), user.payrate * 1.125)
        # if shift start after 6am (else)
        else:
            return calculator(round(shift.lengthShift,3),user.payrate)

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

# Create marginal shift values
def calculator(length, payrate):
    return length * payrate


def getCurrent_Dates(date, period):
    weekdayStr = date.strftime("%a")
    startofWeek = date - datetime.timedelta(days=DAYS_COUNTER[weekdayStr])
    if period == 'week':
        endofWeek = date + datetime.timedelta(days=PREV_DAYS_COUNTER[weekdayStr])
        return [startofWeek, endofWeek]
    elif period == 'fortnight':
        FortnightDay = date - datetime.timedelta(days=PREVIOUS_WEEK_DAYS[weekdayStr])
        return [FortnightDay, date]
    elif period == 'month':
        CurrentMonthFirstDay = date.replace(day=1)
        CurrentMonthLastDay = calendar.monthrange(date.year, date.month)
        CurrentMonthLastDay = date.replace(day=CurrentMonthLastDay[1])
        return [CurrentMonthFirstDay, CurrentMonthLastDay]
    elif period == 'quarter':
        MonthDateQTR = date.strftime("%b")
        QuarterMonthStr = date.month - QUARTER_MONTHS[MonthDateQTR]
        QuarterMonth = date.replace(month=QuarterMonthStr, day=1)
        return [QuarterMonth, date]
    elif period =='year':
        FYYear = date - datetime.timedelta(weeks=52)
        FYYear = FYYear.replace(month=7, day=1)
        return [FYYear, date]
    else:
        return 'No date returned'

def getPrevious_Dates(date, period):
    todayStr = date.strftime("%a")
    previousWeek = date - datetime.timedelta(days=PREVIOUS_WEEK_DAYS[todayStr])
    if period == 'week':
        previousWeekDay = previousWeek.strftime('%a')
        endOfpreviousWeek = previousWeek + datetime.timedelta(days=PREV_DAYS_COUNTER[previousWeekDay])
        return [previousWeek, endOfpreviousWeek]
    if period == 'fortnight':
        previousFortnightDate = date - datetime.timedelta(days=PREV_FORTNIGHT_DAYS[todayStr])
        previousFornightDay = previousFortnightDate.strftime('%a')
        endOfpreviousFortnight = previousWeek + datetime.timedelta(days=PREV_DAYS_COUNTER[previousFornightDay])
        return [previousFortnightDate, endOfpreviousFortnight]
    if period == 'month':
        prep = int(date.month)
        # If month = 01 then go back to last month of year (12)
        # Else month - 1
        if prep == 1:
            prep = 12
        else:
            prep = prep - 1
        previousMonthFirstDate = date.replace(month=prep, day=1)
        previousMonthLastDate = calendar.monthrange(previousMonthFirstDate.year, previousMonthFirstDate.month)
        previousMonthLastDate = previousMonthFirstDate.replace(day=previousMonthLastDate[1])
        return [previousMonthFirstDate, previousMonthLastDate]
    if period == 'quarter':
        previousQuarterMonth = date.month - PREV_QUARTER_MONTHS[date.strftime("%b")]
        if date.month <= 7:
            previousQuarterMonth = date.today().replace(day=1, month=previousQuarterMonth, year=date.year - 1)
        else:
            previousQuarterMonth = date.today().replace(day=1, month=previousQuarterMonth)
        previousQuarterLastMonth = calendar.monthrange(previousQuarterMonth.year, previousQuarterMonth.month + 2)
        lastDayQuarterMonth = date.today().replace(day = previousQuarterLastMonth[1], month = previousQuarterMonth.month + 2)
        return [previousQuarterMonth, lastDayQuarterMonth]
    if period == 'year':
        previousFYFirstDay = date.replace(day=1, month=7, year=date.year - 1)
        FindLastdayFY = calendar.monthrange(year=date.year+1, month=6)
        previousFYLastDay = date.replace(day=FindLastdayFY[1], month=6, year=previousFYFirstDay.year + 1)
        return [previousFYFirstDay, previousFYLastDay]
    else:
        return 'No date returned'

# FUNCTIONS TO RETRIEVE DB DATA
def getCurrent_Shifts(date, user_id, period):
    dates = getCurrent_Dates(date, period)
    if period == 'week':
        return dbSession.query(Shifts).filter_by(user_id=user_id).filter(Shifts.date >= dates[0]).filter(Shifts.date <= dates[1]).all()
    elif period == 'fortnight':
        return dbSession.query(Shifts).filter_by(user_id=user_id).filter(Shifts.date >= dates[0]).filter(Shifts.date <= dates[1]).all()
    elif period == 'month':
        return dbSession.query(Shifts).filter_by(user_id=user_id).filter(Shifts.date >= dates[0]).filter(Shifts.date <= dates[1]).all()
    elif period == 'quarter':
        return dbSession.query(Shifts).filter_by(user_id=user_id).filter(Shifts.date <= date).filter(Shifts.date >= dates[0]).all()
    elif period == 'year':
        return dbSession.query(Shifts).filter_by(user_id=user_id).filter(Shifts.date <= date).filter(Shifts.date >= dates[0]).all()
    else:
        return dbSession.query(Shifts).filter_by(user_id=user_id).all()

def getPrevious_Shifts(date, user_id, period):
    dates = getPrevious_Dates(date, period)
    if period == 'week':
        return dbSession.query(Shifts).filter_by(user_id=user_id).filter(Shifts.date >= dates[0]).filter(Shifts.date <= dates[1]).all()
    if period == 'fortnight':
        return dbSession.query(Shifts).filter_by(user_id=user_id).filter(Shifts.date >= dates[0]).filter(Shifts.date <= dates[1]).all()
    if period == 'month':
        return dbSession.query(Shifts).filter_by(user_id=user_id).filter(Shifts.date >= dates[0]).filter(Shifts.date <= dates[1]).all()
    if period == 'quarter':
        return dbSession.query(Shifts).filter_by(user_id=user_id).filter(Shifts.date >= dates[0]).filter(Shifts.date <= dates[1]).all()
    if period == 'year':
        return dbSession.query(Shifts).filter_by(user_id=user_id).filter(Shifts.date >= dates[0]).filter(Shifts.date <= dates[1]).all()

# Object to render template
class monthlyShifts():
    # Data Members
    monthNet = 0
    monthNet = 0
    monthHours = 0
    monthTaxes = 0
    monthDates = None
    monthShifts = None

    # Constructor
    def __init__(self, user_id, view):
        # Create dates, then shifts
        if view == 'previous':
            self.monthDates = monthDates = getPrevious_Dates(date.today(), 'month')
        else:

            self.monthDates = monthDates = getCurrent_Dates(date.today(), 'month')

        self.monthShifts = monthShifts = dbSession.query(Shifts).filter_by(user_id = user_id).filter(Shifts.date >= monthDates[0]).filter(Shifts.date <= monthDates[1]).all()
        # Increment monthly obj values
        if monthShifts:
            for shift in monthShifts:
                self.monthNet += shift.net_income
                self.monthHours += shift.hours
                self.monthTaxes += shift.tax
