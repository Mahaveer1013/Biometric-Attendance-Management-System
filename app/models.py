from . import db
from flask_login import UserMixin
from sqlalchemy.sql import func
from datetime import datetime, timedelta
from sqlalchemy import Interval


current_time = datetime.now()

class Login_admin(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150),nullable=False)
    email=db.Column(db.String(150),unique=True)
    password = db.Column(db.String(150))
    designation = db.Column(db.String(150), nullable=True)
    date = db.Column(db.DateTime(timezone=True), default=current_time)
    # date = db.Column(db.DateTime(timezone=True), default=func.now())

class Emp_login(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.DateTime(timezone=True), default=current_time)
    email = db.Column(db.String(150))
    name = db.Column(db.String(150), nullable=False)
    password = db.Column(db.String(150))
    emp_id = db.Column(db.Integer)
    branch=db.Column(db.String(150),default='KKL')  # DR, FT, KKL
    phoneNumber=db.Column(db.Integer)   #newly added
    role =db.Column(db.String(150), nullable=False)
    late_balance = db.Column(db.Integer, default=20)
    leave_balance = db.Column(db.Integer, default=20)
    address = db.Column(db.String(150))
    gender = db.Column(db.String(150))
    shift=db.Column(db.String(150))
    attendances = db.relationship('Attendance', back_populates='employee', cascade='all, delete-orphan')
    freezed_account =db.Column(db.Boolean(150),default=False)


class Attendance(db.Model,UserMixin):
    id=db.Column(db.Integer,primary_key=True)
    date = db.Column(db.DateTime(timezone=True), default=current_time)
    emp_id = db.Column(db.Integer, db.ForeignKey('emp_login.emp_id'))
    name = db.Column(db.String(150))
    attendance =db.Column(db.String(150))
    branch =db.Column(db.String(150),default='KKL')
    # wages_per_Day=db.Column(db.String(150))
    inTime=db.Column(db.DateTime(timezone=True))
    outTime=db.Column(db.DateTime(timezone=True))
    overtime=db.Column(db.Time(timezone=True))
    employee = db.relationship('Emp_login', back_populates='attendances')
    shiftType=db.Column(db.String(150))
    shiftIntime = db.Column(db.DateTime(timezone=True))
    shift_Outtime = db.Column(db.DateTime(timezone=True))
    TotalDuration=db.Column(db.String(150))
    lateBy=db.Column(db.Time(timezone=True))
    earlyGoingBy=db.Column(db.Time(timezone=True))
    # punchRecords=db.Column(db.String(150))



class LoginEmp(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150),nullable=False)
    email=db.Column(db.String(150),unique=True)
    password = db.Column(db.String(150))
    date = db.Column(db.DateTime(timezone=True), default=current_time)


class Shift_time(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    shiftIntime = db.Column(db.Time(timezone=True))
    shift_Outtime = db.Column(db.Time(timezone=True))
    shiftType = db.Column(db.String(150))



class Backup(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.DateTime(timezone=True), default=current_time)
    email = db.Column(db.String(150))
    name = db.Column(db.String(150))
    password = db.Column(db.String(150))
    emp_id = db.Column(db.Integer)
    branch=db.Column(db.String(150))
    phoneNumber=db.Column(db.Integer)
    role =db.Column(db.String(150))
    address = db.Column(db.String(150))
    gender = db.Column(db.String(150))
    shift=db.Column(db.String(150))
    attendances = db.Column(db.String(150))
    worked=db.Column(db.Integer)





class NewShift(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name_date_day = db.Column(db.String(255))
    filename=db.Column(db.String(255))

    # Define columns for days 1 through 31
    for day_num in range(1, 32):
        locals()[f"day_{day_num}"] = db.Column(db.String(255))
    monday = db.Column(db.String(255))
    tuesday = db.Column(db.String(255))
    wednesday = db.Column(db.String(255))
    thursday = db.Column(db.String(255))
    friday = db.Column(db.String(255))

class notifications(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    reason = db.Column(db.String(255))
    timestamp = db.Column(db.DateTime, default=current_time)
    emp_name = db.Column(db.String(255))
    permission_type = db.Column(db.String(255))
    emp_id = db.Column(db.Integer)
    from_time = db.Column(db.String(150), nullable=False)
    to_time = db.Column(db.String(150), nullable=False)
    req_id = db.Column(db.Integer)

# Late Model (Example)
class late(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    emp_id = db.Column(db.Integer)
    emp_name = db.Column(db.String(150), nullable=False)
    reason = db.Column(db.String(150), nullable=False)
    from_time = db.Column(db.String(150), nullable=False)
    to_time = db.Column(db.String(150), nullable=False)
    status = db.Column(db.String(150), default='Pending')
    # hod_approval = db.Column(db.String(150), default='Pending')
    approved_by = db.Column(db.String(150), default='Pending')
    hr_approval = db.Column(db.String(150), default='Pending')
    date = db.Column(db.DateTime(timezone=True), default=current_time)
# Leave Model (Example)

class leave(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    emp_id = db.Column(db.Integer)
    emp_name = db.Column(db.String(150), nullable=False)
    reason = db.Column(db.String(150), nullable=False)
    from_time = db.Column(db.String(150), nullable=False)
    to_time = db.Column(db.String(150), nullable=False)
    status = db.Column(db.String(150), default='Pending')
    # hod_approval = db.Column(db.String(150), default='Pending')
    approved_by = db.Column(db.String(150), default='Pending')
    hr_approval = db.Column(db.String(150), default='Pending')
    date = db.Column(db.DateTime(timezone=True), default=current_time)



class Festival(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    holiday=db.Column(db.String(150), nullable=False)
    date=db.Column(db.String(150), nullable=False)
    # date= db.Column(db.Date())


class user_edit(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    emp_id = db.Column(db.Integer)
    name = db.Column(db.String(150), nullable=False)
    old_data=db.Column(db.String(150), nullable=False)
    new_data=db.Column(db.String(150), nullable=False)
    data_type=db.Column(db.String(150), nullable=False)

class Week_off(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    emp_id = db.Column(db.Integer)
    # date = db.Column(db.DateTime(timezone=True), default=current_time)
    date= db.Column(db.String(150), nullable=False)

class comp_off(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    emp_id = db.Column(db.Integer)
    # comp_off= db.Column(db.Integer)
    date= db.Column(db.String(150), nullable=False)

class call_duty(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    emp_id = db.Column(db.Integer)
    date= db.Column(db.DateTime(timezone=True))
    inTime= db.Column(db.DateTime(timezone=True))
    outTime= db.Column(db.DateTime(timezone=True))
