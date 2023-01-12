from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import Column, Integer, String, Float
from sqlalchemy.orm import relationship
from sqlalchemy import ForeignKey
from sqlalchemy import DateTime
from sqlalchemy import func
engine = create_engine("sqlite:///db/cms.db", echo=True)

class Base(DeclarativeBase):
    pass

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

class Shifts(Base):
    __tablename__ = 'shifts'
    id = Column(Integer, primary_key=True)
    date = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    hours = Column(Integer, unique=False, nullable=False)
    start = Column(Integer, unique=False, nullable=False)
    end = Column(Integer, unique=False, nullable=False)
    gross_income = Column(Float, unique=False, nullable=False)
    taxes = Column(Float, unique=False, nullable=True)
    net_income = Column(Float, unique=False, nullable=False)
    super = Column(Float, unique=False, nullable=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    
    earnings = relationship('Earnings', backref='shifts')

    def __init__(self, date, hours, start, end, gross_income, taxes, net_income, super, user_id):
        self.date = date
        self.hours = hours
        self.start = start
        self.end = end
        self.gross_income = gross_income
        self.taxes = taxes
        self.net_income = net_income
        self.super = super
        self.user_id = user_id

    def __repr__(self) -> str:
        return f'User(id={self.id!r}, name={self.username!r})'

class Earnings(Base):
    __tablename__ = 'earnings'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    gross_earnings = Column(Integer, nullable=True, unique=False)
    taxes = Column(Integer, nullable=True, unique=False)
    net_earnings = Column(Integer, nullable=True, unique=False)
    super_earnings = Column(Integer, nullable=True, unique=False)
    shift_id = Column(Integer, ForeignKey('shifts.id'))
    
    def __init__(self, user_id, gross_earnings, taxes, net_earnings, super_earnings, shift_id):
        self.user_id = user_id
        self.gross_earnings = gross_earnings
        self.taxes = taxes
        self. net_earnings = net_earnings
        self.super_earnings = super_earnings
        self.shift_id = shift_id
    
    def __repr__(self) -> str:
        return f'User(id={self.id!r}, name={self.username!r})'

Base.metadata.create_all(bind=engine)
