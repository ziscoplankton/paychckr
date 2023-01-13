import datetime
from datetime import date
from helpers import strtoint, getCurrent_Dates, getPrevious_Dates
from db.db import Shifts, Session



# DB SESSION
dbSession = Session()


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


# cardShift for rendering
class cardShift:

    #Data Members
    net_earnings = 0.00
    gross_earnings = 0.00
    taxes = 0.00
    hours = 0.00

    # Constructor
    def __init__(self, shifts):
        self.net_earnings = [shift.net_income for shift in shifts]
        self.gross_earnings = [shift.gross_income for shift in shifts]
        self.taxes = [shift.taxes for shift in shifts]
        self.hours = [shift.hours for shift in shifts]


# MonthlyShifts query to render reports
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
                self.monthTaxes += shift.taxes

