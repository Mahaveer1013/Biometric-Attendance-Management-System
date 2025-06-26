from flask_login import login_required, login_user, logout_user, current_user
from flask import Blueprint, render_template, request, flash, redirect, url_for,session
from werkzeug.security import generate_password_hash, check_password_hash
from .models import Attendance,Shift_time,Backup, late, leave,notifications,NewShift,Emp_login,call_duty
from . import db
import datetime
from flask import current_app as app
from sqlalchemy.exc import SQLAlchemyError
import time
from datetime import datetime, timedelta
from .funcations import *



auth = Blueprint('auth', __name__)

@auth.route('/admin-login', methods=['POST', 'GET'])       # this is the overall login ....
def login():
    admin = Emp_login.query.filter_by(email='vsabarinathan1611@gmail.com').first()
    if admin:
        if request.method == 'POST':

            email = request.form.get('email')
            password = request.form.get('password')
            # session.clear()

            dbemail = Emp_login.query.filter_by(email=email).first()
            print(dbemail)
            if dbemail :
                if check_password_hash(dbemail.password, password):

                    login_user(dbemail, remember=True)

                    if dbemail.role == "admin":
                        session['admin_name']=dbemail.name
                        print("admin session created")
                        return redirect(url_for('views.admin'))

                    elif dbemail.role == "employee":
                        session['emp_id'] = dbemail.emp_id
                        session['name'] = dbemail.name
                        session['email'] = email
                        session['phNumber']=dbemail.phoneNumber
                        session['leave_balance']=dbemail.leave_balance
                        session['late_balance']=dbemail.late_balance
                        return redirect(url_for('views.user_dashboard'))
                        #return redirect(url_for('views.emp_login'))

                else:
                    flash("Incorrect Password", category='error')
            else:
                flash("Incorrect Email", category='error')
    else:
        # Assuming you're using Flask's generate_password_hash to hash passwords during registration
        addAdmin = Emp_login(
            name="Admin",
            email="vsabarinathan1611@gmail.com",
            phoneNumber="123456789",
            password=generate_password_hash("admin"),
            role="admin",
            emp_id='9999'
        )
        db.session.add(addAdmin)
        db.session.commit()
        print('Created Admin!')

    return render_template('login.html')

@auth.route('/login', methods=['POST', 'GET'])
def admin_login():

    print("session cleared")
    return render_template("login.html")

@auth.route('/logout', methods=['GET', 'POST'])
def logout():
    logout_user()
    return redirect(url_for('auth.login'))

@auth.route('/addemp', methods=['POST', 'GET'])
@login_required
def attendance():
    try:

            file_path = os.path.join(app.config['EXCEL_FOLDER'], 'employee_data.xlsx')  # Use correct case 'EXCEL_FOLDER'
            addemployee(file_path)  # Call the data processing function


    except Exception as e:
        print("Error occurred:", e)
        db.session.rollback()  # Rollback in case of error
    return redirect(url_for('views.admin'))


@auth.route('/signup',methods=['POST','GET'])
def signup():
    if request.method == 'POST':
        # Get user input from the form
        email = request.form['email']
        password = request.form['password']
        emp_id = request.form['emp_id']  # Assuming you have a form field for emp_id
        name = request.form['name']
        ph_number = request.form['ph_number']
        role = request.form['role']
        # Check if a user with the same email already exists
        existing_user = Emp_login.query.filter_by(email=email).first()
        existing_id = Emp_login.query.filter_by(id=emp_id).first()
        if existing_user:
            flash('Email already exists. Please choose a different email.')

        elif existing_id:
            flash('Emp id already exists. Please choose a different email.')
        else:
            # Create a new Emp_login object and add it to the database
            new_login = Emp_login(email=email, password=generate_password_hash(password), role=role,phoneNumber=ph_number, emp_id=emp_id, name=name)
            db.session.add(new_login)
            db.session.commit()

            # Redirect to a success page or perform any other necessary actions
            return render_template("login.html")

    # Render the signup form for GET requests
    return render_template('signup.html')
