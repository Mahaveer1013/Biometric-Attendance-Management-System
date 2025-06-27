#riglet Mahaveer | lolcat
from datetime import datetime, timedelta,time
import smtplib
from werkzeug.security import generate_password_hash, check_password_hash
import os
from flask import current_app as app
from flask import  flash,redirect,session,redirect
from .models import Attendance, Shift_time, Emp_login,Festival,late,leave,Week_off,comp_off,call_duty
from . import db
from os import path
import sched
from twilio.rest import Client
import schedule
import time
from sqlalchemy import text
from email.mime.text import MIMEText
from twilio.base.exceptions import TwilioRestException
from sqlalchemy import func
import pandas as pd
from sqlalchemy.orm import aliased
from .task import *
from sqlalchemy import create_engine, Column, Integer, String, DateTime, func, or_, and_
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from . import mysql_engine,sqlite_engine
from sqlalchemy.ext.automap import automap_base
from flask import current_app
import sqlite3
import logging
from dotenv import load_dotenv
load_dotenv()
Base = automap_base()
Base.prepare(mysql_engine, reflect=True)
MySQLAttendance = Base.classes.attendance
SessionSQLite = sessionmaker(bind=sqlite_engine)
session_sqlite = SessionSQLite()
SessionMySQL = sessionmaker(bind=mysql_engine)
logging.getLogger('sqlalchemy.dialects.mysql').setLevel(logging.WARNING)
logging.getLogger('sqlalchemy.engine').setLevel(logging.WARNING)

from sqlalchemy.orm import Session
scheduler = sched.scheduler(time.time, time.sleep)


def send_mail(email, subject, body):
    sender_email = os.getenv("EMAIL")
    receiver_email = email
    password = os.getenv("EMAIL_PASS")
    message = MIMEText(body)
    message['From'] = sender_email
    message['To'] = receiver_email
    message['Subject'] = subject
    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.ehlo()
        server.starttls()
        server.login(sender_email, password)
        server.sendmail(sender_email, receiver_email, message.as_string())
        server.quit()
        return True
    except Exception as e:
        print(f'Email error: {str(e)}')
        return False

def send_sms(numbers_to_message, message_body):
    account_sid = os.getenv('TWILIO_ACCOUNT_SID')
    auth_token = os.getenv('TWILIO_AUTH_TOKEN')
    client = Client(account_sid, auth_token)
    from_phone_number = os.getenv('TWILIO_PHONE_NUMBER', '+12069666359')
    if not isinstance(numbers_to_message, (list, tuple)):
        numbers_to_message = [numbers_to_message]
    results = []
    for number in numbers_to_message:
        try:
            formatted_number = validate_and_format_phone_number(str(number))
            message = client.messages.create(
                from_=from_phone_number,
                body=message_body,
                to=formatted_number
            )
            results.append((formatted_number, True))
        except TwilioRestException as e:
            print(f"Twilio error: {e}")
            results.append((number, False))
    return results

def validate_and_format_phone_number(phone_number):

    phone_number=str(phone_number)
    if not phone_number.startswith('+'):
        phone_number = '+91' + phone_number
        print("phone_number:",phone_number)

    return phone_number

def update_or_add_shift(shift_type, in_time, out_time):
    try:
        existing_shift = session_sqlite.query(Shift_time).filter_by(shiftType=shift_type).first()
        print("update_or_add_shift")

        if existing_shift:
            # Update existing shift
            existing_shift.shiftIntime = in_time
            existing_shift.shift_Outtime = out_time
            print("Shift updated")
            session_sqlite.commit()
            return True
        else:
            # Add new shift
            new_shift = Shift_time(
                shiftIntime=in_time,
                shift_Outtime=out_time,
                shiftType=shift_type,
            )
            session_sqlite.add(new_shift)
            session_sqlite.commit()
            print("New shift added")
            return True
    except Exception as e:
        print(f"Error in update_or_add_shift: {str(e)}")
        session_sqlite.rollback()
        return False
    finally:
        session_sqlite.close()

def read_weekoff(file_path):
    try:
        print("Prestn",file_path)
        if os.path.exists(file_path):
            print(True)
            sheet_names = pd.ExcelFile(file_path).sheet_names

            for sheet_name in sheet_names:
                df = None
                if file_path.lower().endswith('.xlsx'):
                    df = pd.read_excel(file_path, sheet_name, engine='openpyxl')

                elif file_path.lower().endswith('.xls'):
                    df = pd.read_excel(file_path, sheet_name, engine='xlrd')

                else:
                    print("Unsupported file format")
                    return  # Handle unsupported format

                for index, row in df.iterrows():
                    print("str(row['empid']):",row['empid'], "str(row['weekoff']):", str(row['weekoff']))
                    emp_id = str(row['empid'])
                    week_off = str(row['weekoff'])
                    new_week_off = Week_off(
                        emp_id=emp_id,
                    date=week_off
                            )
                    session_sqlite.add(new_week_off)
                session_sqlite.commit()
    except Exception as e:
        print(f"Error in read_weekoff: {str(e)}")
        session_sqlite.rollback()
    finally:
        session_sqlite.close()

def process_excel_data(file_path):
    try:
        if os.path.exists(file_path):
            sheet_names = pd.ExcelFile(file_path).sheet_names

            for sheet_name in sheet_names:
                df = None
                if file_path.lower().endswith('.xlsx'):
                    df = pd.read_excel(file_path, sheet_name, engine='openpyxl', skiprows=1)
                elif file_path.lower().endswith('.xls'):
                    df = pd.read_excel(file_path, sheet_name, engine='xlrd', skiprows=1)
                else:
                    print("Unsupported file format")
                    return  # Handle unsupported format

                for index, row in df.iterrows():
                    shift_type = row['Shift']
                    in_time_str = row['S. InTime']
                    out_time_str = row['S. OutTime']

                    in_time = datetime.strptime(in_time_str, '%H:%M:%S').time()
                    out_time = datetime.strptime(out_time_str, '%H:%M:%S').time()

                    print("Processing: ", shift_type)

                    update_or_add_shift(shift_type, in_time, out_time)
    except Exception as e:
        print(f"Error in process_excel_data: {str(e)}")
    finally:
        session_sqlite.close()

def shiftypdate():
    try:
        employees = session_sqlite.query(Emp_login).all()  # Fetch all employees

        for employee in employees:
            attendance_count = len(employee.attendances)
            print(f"Employee ID: {employee.id}, Attendance Count: {attendance_count}")

            if attendance_count % 2 == 0:
                shifts = ['8G', '8A', '8C', '8B', 'GS', '12A', '12B', '10A', 'WO']
                current_shift_index = shifts.index(employee.shift)
                new_shift_index = (current_shift_index + 1) % len(shifts)
                employee.shift = shifts[new_shift_index]
                session_sqlite.commit()

        return len(employees)
    except Exception as e:
        print(f"Error in shiftypdate: {str(e)}")
        session_sqlite.rollback()
        return 0
    finally:
        session_sqlite.close()

def update_freeze_status_and_remove_absences(emp_id):
    try:
        emp = session_sqlite.query(Emp_login).filter_by(emp_id=emp_id).first()

        thirty_days_ago = datetime.now() - timedelta(days=30)
        absent_records = session_sqlite.query(Attendance).filter(Attendance.emp_id==emp_id, or_(Attendance.attendance=='Absent',Attendance.attendance==None)).filter(Attendance.date >= thirty_days_ago).all()
        # print(f"Employee ID: {emp_id}")
        # print(f"Absent Records: {len(absent_records)}")

        if len(absent_records) >= 30:
            emp.freezed_account = True
            # print("Updating freeze status...")
        else:
            emp.freezed_account = False
            # print("the employee freeze has been removed")

        session_sqlite.commit()
        return f"Success: Freeze status updated and attendance records deleted for employee {emp_id}."

    except Exception as e:
        session_sqlite.rollback()
        print(f"Error: {str(e)}")
        return f"Error: {str(e)}"
    finally:
        session_sqlite.close()

def delete_all_employees():
    try:
        session_sqlite.query(Attendance).delete()
        session_sqlite.commit()
        print("All employee data deleted successfully.")
    except Exception as e:
        session_sqlite.rollback()
        print("An error occurred:", str(e))
    finally:
        session_sqlite.close()

def read_excel_data(file_path, sheet_name=None):
    if sheet_name:
        return pd.read_excel(file_path, sheet_name, engine='openpyxl')
    else:
        return pd.read_excel(file_path, engine='openpyxl')

def read_csv_data(file_path):
    return pd.read_csv(file_path)

def add_employee(file_path):
    summary = {'added': 0, 'updated': 0, 'skipped': 0, 'errors': []}
    try:
        if not os.path.exists(file_path):
            summary['errors'].append('File not found')
            return summary
        _, file_extension = os.path.splitext(file_path)
        if file_extension.lower() in ['.xlsx', '.xls']:
            sheet_names = pd.ExcelFile(file_path).sheet_names
        elif file_extension.lower() == '.csv':
            sheet_names = [None]
        else:
            summary['errors'].append('Unsupported file format')
            return summary
        data_to_insert = []
        for sheet_name in sheet_names:
            if file_extension.lower() in ['.xlsx', '.xls']:
                df = read_excel_data(file_path, sheet_name)
            elif file_extension.lower() == '.csv':
                df = read_csv_data(file_path)
            else:
                continue
            for index, row in df.iterrows():
                try:
                    emp_id = str(row['emp_id'])
                    if not emp_id:
                        summary['skipped'] += 1
                        continue
                    existing_emp = session_sqlite.query(Emp_login).filter_by(emp_id=emp_id).first()
                    if not existing_emp:
                        data_to_insert.append({
                            'emp_id': emp_id,
                            'name': row.get('name', ''),
                            'role': row.get('designation', ''),
                            'email': row.get('email', ''),
                            'phoneNumber': str(row.get('phoneNumber', '')),
                            'shift': row.get('shift', ''),
                            'branch': row.get('branch', ''),
                            'gender': row.get('gender', ''),
                            'password': generate_password_hash(str(row.get('phoneNumber', '')))
                        })
                        summary['added'] += 1
                    else:
                        existing_emp.name = row.get('name', existing_emp.name)
                        existing_emp.role = row.get('designation', existing_emp.role)
                        existing_emp.email = row.get('email', existing_emp.email)
                        existing_emp.phoneNumber = str(row.get('phoneNumber', existing_emp.phoneNumber))
                        existing_emp.shift = row.get('shift', existing_emp.shift)
                        existing_emp.gender = row.get('gender', existing_emp.gender)
                        existing_emp.password = generate_password_hash(str(row.get('phoneNumber', existing_emp.phoneNumber)))
                        summary['updated'] += 1
                except Exception as e:
                    summary['errors'].append(f'Row {index}: {str(e)}')
                    summary['skipped'] += 1
        if data_to_insert:
            try:
                with session_sqlite.begin_nested():
                    session_sqlite.bulk_insert_mappings(Emp_login, data_to_insert)
                session_sqlite.commit()
            except Exception as e:
                summary['errors'].append(f'Bulk insert error: {str(e)}')
        else:
            session_sqlite.commit()
    except Exception as e:
        summary['errors'].append(str(e))
        session_sqlite.rollback()
    finally:
        session_sqlite.close()
    return summary

def up_festival(file_path):
    try:
        if not os.path.exists(file_path):
            flash("File does not exist", "error")
            return
        with session_sqlite.begin_nested():
            # Delete all records from the Festival table
            session_sqlite.query(Festival).delete()

        sheet_names = pd.ExcelFile(file_path).sheet_names

        # Iterate through each sheet in the Excel file
        for sheet_name in sheet_names:
            df = None
            # Read data from the Excel file based on the file extension
            if file_path.lower().endswith('.xlsx'):
                df = pd.read_excel(file_path, sheet_name, engine='openpyxl')
            elif file_path.lower().endswith('.xls'):
                df = pd.read_excel(file_path, sheet_name, engine='xlrd')
            else:
                raise ValueError("Unsupported file format. Only .xlsx and .xls files are supported.")
            print(df)
            # Iterate through rows in the DataFrame and add records to the Festival table
            for index, row in df.iterrows():
                try:
                    add_festival = Festival(
                        holiday=row['Public Holidays'],
                        date=row['Date'],
                    )
                    session_sqlite.add(add_festival)

                except Exception as e:
                    # Handle specific errors or print more information for debugging
                    print(f"Error adding festival at index {index}: {str(e)}")

                # Commit the changes to the database
        session_sqlite.commit()
        flash("Festivals added successfully", category="success")
    except Exception as e:
        print("festival upload error",e)
        session_sqlite.rollback()
        flash(f"Error adding festivals: {str(e)}", category="error")
    finally:
        session_sqlite.close()

def check_send_sms(emp_id):
    try:
        emp = session_sqlite.query(Emp_login).filter_by(emp_id=emp_id).first()

        if emp:
            Phonenum = emp.phoneNumber
            email = emp.email
            sub='Miss punch'
            message = f"""
            Dear {emp.name}:
            It is a gentle reminder to you,
            You have missed to keep the punch in the biometric machine
            """
            print("Phone number:", Phonenum)
            send_mail(email=email, body=message,subject=sub)
            send_sms(Phonenum ,message)
    except Exception as e:
        print(f"Error in check_send_sms: {str(e)}")
    finally:
        session_sqlite.close()

def check_date_format(date):
    str(date).replace('/','-')
    str(date).replace('.','-')
    # print(date.date())
check_date_format('2022/12/02 12:20:00')

def month_attendance():
    try:
        start_date, end_date = get_last_month_dates()

        # Query the database for last month's attendance up to the current date
        last_month_attendance = session_sqlite.query(Attendance).filter(
            Attendance.date.between(start_date, end_date)
        ).all()
        # print(start_date,end_date)

        # Create a dictionary to store attendance records for each emp_id
        employee_data = {}
        date = set()

        for record in last_month_attendance:
            emp_id = record.emp_id
            record_date=record.date.date().day
            date.add(record_date)

            # If emp_id is not in t8e dictionary, create a new list for that emp_id
            if emp_id not in employee_data:
                employee_data[emp_id] = []

            # Append the record to the list for that emp_id
            employee_data[emp_id].append(record)

        date = list(date)
        return [employee_data,date]
    except Exception as e:
        print(f"Error in month_attendance: {str(e)}")
        return [{}, []]
    finally:
        session_sqlite.close()
    #return render_template('month_attendance.html', employee_data=employee_data,date=date)

def get_last_month_dates():
    today = datetime.today()
    first_day_of_current_month = today.replace(day=1)
    last_day_of_last_month = first_day_of_current_month - timedelta(days=1)
    first_day_of_last_month = last_day_of_last_month.replace(day=1)
    return first_day_of_last_month, today

def check_leave(date_str, emp_id):
    try:
        date = datetime.strptime(date_str, "%d.%m.%Y").date()
        previous_date = date - timedelta(days=1)
        previous_previous_date = previous_date - timedelta(days=1)

        previous_date_attend = session_sqlite.query(Attendance).filter_by(emp_id=emp_id, date=previous_date).first()
        previous_previous_date_attend = session_sqlite.query(Attendance).filter_by(emp_id=emp_id, date=previous_previous_date).first()

        if previous_date_attend and (previous_date_attend.attendance == 'Holiday' or previous_date_attend.attendance == 'Week Off'):
            if previous_previous_date_attend and previous_previous_date_attend.attendance == 'Leave':
                previous_date_attend.attendance = 'Leave'
                session_sqlite.commit()
    except Exception as e:
        print(f"Error in check_leave: {str(e)}")
        session_sqlite.rollback()
    finally:
        session_sqlite.close()

def createXL():
    try:
        saveFolder = current_app.config['DAY_ATTENDANCE_FOLDER']

        # Connect to the SQLite database
        sqlite_file = 'app/database.db'
        conn = sqlite3.connect(sqlite_file)

        # Read data from the 'call_duty' table
        call_duty_df = pd.read_sql_query("SELECT * FROM call_duty", conn)

        # Read data from the 'Attendance' table
        attendance_df = pd.read_sql_query("SELECT * FROM Attendance", conn)

        # Merge the dataframes with a left join to keep all rows from 'attendance_df'
        merged_df = pd.merge(attendance_df, call_duty_df, on='emp_id', how='left', suffixes=('_attendance', '_call_duty'))

        # Save the merged dataframe to Excel
        merged_df.to_excel(os.path.join(saveFolder, "merged_data.xlsx"), index=False)

        return True  # Return True if the file creation is successful
    except Exception as e:
        error_message = "Error creating Excel file: {}".format(str(e))
        print(error_message)
        return False  # Return False if an error occurs during file creation

def calculate_time_difference(time1, time2):
    # Convert time objects to strings
    # time1_str = time1.strftime('%H:%M:%S')
    # time2_str = time2.strftime('%H:%M:%S')

    # Convert time strings to datetime objects (without seconds)
    # time1_obj = datetime.strptime(time1_str, '%H:%M:%S').time()
    # time2_obj = datetime.strptime(time2_str, '%H:%M:%S').time()

    # Convert time objects to seconds

    seconds1 = int(time1.hour) * 3600 + int(time1.minute) * 60
    seconds2 = int(time2.hour) * 3600 + int(time2.minute) * 60

    difference_seconds = seconds2 - seconds1
    if '-' in str(difference_seconds):
        return None

    # Convert seconds to hours and minutes
    total_minutes = difference_seconds // 60
    total_hours = total_minutes // 60
    minutes = total_minutes % 60

    time_difference=datetime(2024,1,1,total_hours,minutes,0)

    return time_difference.time()




def calculate_time_difference_total_timeduraction(time1, time2):
    time_difference = time2 - time1
    return str(time_difference)

def create_dummy_attendance():
    try:
        current_time_with_ms = datetime.now().time()
        current_time = datetime.strptime(current_time_with_ms.strftime('%H:%M:%S'), '%H:%M:%S').time()
        shift_times = session_sqlite.query(Shift_time).all()
        print(shift_times,'\n\n\n\n\n')

        current_shifts=get_current_shift()
        session_sqlite.query(Attendance).filter(
            Attendance.attendance == None,
            ~Attendance.shiftType.in_(current_shifts)
        ).update({Attendance.attendance: 'Absent'}, synchronize_session=False)
        session_sqlite.commit()
        for current_shift in current_shifts:
            shift=session_sqlite.query(Shift_time).filter_by(shiftType=current_shift).first()
                    # current_shift = '8C'
                # if current_time == shift.shiftIntime:
                    # Call your function here
                    # emp=session_sqlite.query(Emp_login).filter_by(Shift=current_shift).all()
            emp=session_sqlite.query(Emp_login).filter_by(shift=current_shift,freezed_account=False).all()
            for emp in emp:
                attendance_status=None
                update_freeze_status_and_remove_absences(emp.emp_id)

                week_off = session_sqlite.query(Week_off).filter_by(emp_id=emp.emp_id, date=str(datetime.now().date())).first()
                leave_check = session_sqlite.query(leave).filter_by(emp_id=emp.emp_id,date=datetime.now().date(), status='Approved').first()
                # late_check = session_sqlite.query(late).filter_by(emp_id=emp_id,date=datetime.now().date(), status='Approved').first()
                holiday=check_holiday(datetime.now().date())
                if holiday:
                    attendance_status='Holiday'
                elif week_off:
                    attendance_status='Week Off'
                elif leave_check:
                    attendance_status = 'Leave'
                    if emp.branch=='FT':
                        status=check_ft(datetime.now().date(),emp.emp_id)
                        if status!=None:
                            attendance_status=status

                atten=session_sqlite.query(Attendance).filter(Attendance.emp_id==emp.emp_id,func.date(Attendance.date)==datetime.now().date()).first()


                shiftIntime,shift_Outtime=check_shift(shift.shiftIntime,shift.shift_Outtime)

                if atten == None:
                            dummy_atten = Attendance(
                                    emp_id=emp.emp_id,
                                    name=emp.name,
                                    branch=emp.branch,
                                    shiftType=current_shift,
                                    attendance=attendance_status,
                                    shiftIntime=shiftIntime,
                                    shift_Outtime=shift_Outtime,
                                    inTime=None,
                                    outTime=None,
                                )
                            session_sqlite.add(dummy_atten)
                            session_sqlite.commit()
    except Exception as e:
        print(f"Error in create_dummy_attendance: {str(e)}")
        session_sqlite.rollback()
    finally:
        session_sqlite.close()

def check_holiday(curr_date):
    try:
        is_holiday = session_sqlite.query(Festival).filter_by(date = str(curr_date)).first()
        if is_holiday:
            print(is_holiday)
            return True
        else:
            return False
    except Exception as e:
        print(f"Error in check_holiday: {str(e)}")
        return False
    finally:
        session_sqlite.close()

def check_shift(shiftIntime,shiftOuttime):
    print('inTime : ',shiftIntime)
    print('outTime : ',shiftOuttime)
    if shiftIntime>shiftOuttime:
        shiftIntime = datetime.combine(datetime.now().date(), shiftIntime)
        shiftOuttime = datetime.combine((datetime.now().date()+timedelta(days=1)), shiftOuttime)
    else:
        shiftIntime = datetime.combine(datetime.now().date(), shiftIntime)
        shiftOuttime = datetime.combine(datetime.now().date(), shiftOuttime)

    print('inTime : ',shiftIntime)
    print('outTime : ',shiftOuttime)


    return shiftIntime,shiftOuttime

def fetch_and_store_data():
    session_mysql = None
    try:
        current_date = datetime.now().date()
        session_mysql = SessionMySQL()
        yesterday_date=current_date - timedelta(days=1)


        mysql_data = session_mysql.query(MySQLAttendance).filter(
            (func.date(MySQLAttendance.time) == current_date)
        ).all()

        # print(mysql_data)

        for record in mysql_data:
            try:
                existing_record = session_sqlite.query(Attendance).filter(
                    and_(Attendance.emp_id == record.emp_id, func.date(Attendance.date) == current_date)
                ).first()

                yesterday_atten=session_sqlite.query(Attendance).filter(
                    and_(Attendance.emp_id == record.emp_id, func.date(Attendance.date) == yesterday_date,Attendance.inTime!=None ,or_(
            Attendance.outTime == None,
            Attendance.outTime == record.time
        ))).first()
                emp = session_sqlite.query(Emp_login).filter_by(emp_id=record.emp_id).first()
                current_shifts=get_current_shift()
                if yesterday_atten:
                    if yesterday_atten.outTime!=record.time:
                        yesterday_atten.outTime=record.time
                        session_sqlite.commit()
                        calculate_Attendance_from_db(yesterday_atten.id)

                elif not existing_record:

                    # shiftTime = session_sqlite.query(Shift_time).filter_by(shiftType=emp.shift).first()

                    emp_id=record.emp_id
                    # shift_times = session_sqlite.query(Shift_time).all()
                    # current_time = datetime.now().time()

                    week_off = session_sqlite.query(Week_off).filter_by(emp_id=emp_id, date=str(datetime.now().date())).first()
                    shift_for_emp=session_sqlite.query(Shift_time).filter_by(shiftType=emp.shift).first()

                    time_diff=calculate_time_difference(record.time,shift_for_emp.shift_Outtime)
                    if emp.shift not in current_shifts:
                        attendance_status='Wrong Shift'
                    # elif calculate_time_difference(record.time,shift_for_emp.shift_Outtime)<twenty_minutes:
                    elif ((time_diff.hour*3600)+(time_diff.minute*60)+(time_diff.second))<7200:
                        attendance_status='Present'
                    elif check_holiday(datetime.now().date()):
                        attendance_status = 'Hp'
                    elif week_off:
                        attendance_status = 'Wop'
                    else:
                        attendance_status = 'Present'

                    if emp.branch=='FT':
                        status=check_ft(emp_id,current_date)
                        if status=='Week Off':
                            attendance_status='Wop'


                    emp_shift=session_sqlite.query(Emp_login).filter_by(emp_id=emp_id).first().shift
                    shift_time=session_sqlite.query(Shift_time).filter_by(shiftType=emp_shift).first()

                    shiftIntime,shift_Outtime=check_shift(shift_time.shiftIntime,shift_time.shift_Outtime)


                    sqlite_record = Attendance(
                                    emp_id=record.emp_id,
                                    name=emp.name,
                                    branch=emp.branch,
                                    attendance=attendance_status,
                                    shiftType=emp.shift,
                                    shiftIntime=shiftIntime,
                                    shift_Outtime=shift_Outtime,
                                    inTime=record.time,
                                    outTime=None,
                                )
                    session_sqlite.add(sqlite_record)
                    session_sqlite.commit()
                    inserted_id = sqlite_record.id
                    calculate_Attendance_from_db(inserted_id)

                else:
                    if existing_record.inTime==None:
                        existing_record.inTime=record.time
                        attendance_status = 'Present'
                        week_off = session_sqlite.query(Week_off).filter_by(emp_id=emp.emp_id, date=str(datetime.now().date())).first()
                        if week_off:
                            attendance_status = 'Wop'
                        if emp.shift not in current_shifts:
                            attendance_status='Wrong Shift'
                        if emp.branch=='FT':
                            status=check_ft(emp.emp_id,current_date)
                            if status=='Week Off':
                                attendance_status='Wop'
                            if emp.shift not in current_shifts:
                                attendance_status='Wrong Shift'
                        if check_holiday(datetime.now().date()):
                            attendance_status = 'Hp'
                        existing_record.attendance=attendance_status
                        session_sqlite.commit()
                        calculate_Attendance_from_db(existing_record.id)

                    elif existing_record.inTime!=record.time and existing_record.outTime!=record.time:
                                existing_record.outTime = record.time
                                session_sqlite.commit()
                                calculate_Attendance_from_db(existing_record.id)
            except Exception as e:
                print(e)

    except Exception as e:
        print("Exception:/n/n", e)
    finally:
        if session_mysql:
            session_mysql.close()
        session_sqlite.close()

    return redirect('/')

def calculate_Attendance_from_db(id):
    try:
        attendance = session_sqlite.query(Attendance).filter_by(id=id).first()
        # shift = session_sqlite.query(Shift_time).filter_by(shiftType=attendance.shiftType).first()
        inTime=attendance.inTime
        outTime=attendance.outTime

        if inTime != None:
            lateBy = calculate_time_difference(attendance.shiftIntime, inTime)
        else:
            attendance.lateBy = None
        attendance.lateBy=lateBy

        if lateBy != None:
            lateBy_str = str(lateBy)



            hours, minutes, seconds = map(int, lateBy_str.split(':'))
            if (hours * 60 + minutes > 10):
                attendance.attendance = 'Half day'

        if outTime is not None:
            if outTime ==datetime(1,1,1,0,0,0):
                outTime=attendance.shift_Outtime
            attendance.earlyGoingBy = calculate_time_difference(outTime, attendance.shift_Outtime)
            time_worked = calculate_time_difference_total_timeduraction(inTime, outTime)
            attendance.TotalDuration = time_worked

            overtime_hours = calculate_time_difference(attendance.shift_Outtime, outTime)
            attendance.overtime = overtime_hours
        else:
            attendance.overtime = None
            attendance.earlyGoingBy = None
            attendance.TotalDuration = None
        # print('attendance.lateBy',attendance.lateBy)
        # print('attendance.overtime',attendance.overtime)
        # print('attendance.earlyGoingBy',attendance.earlyGoingBy)
        # print('attendance.TotalDuration',attendance.TotalDuration)

        session_sqlite.commit()
        # session_sqlite.close()


    except Exception as e:
        print("Exception:", e)
        session_sqlite.rollback()
    finally:
        session_sqlite.close()

def check_ft(today_date, emp_id):
    try:
        today_date=datetime.now().date()
        yesterday_date = today_date - timedelta(days=1)
        two_before_date = today_date - timedelta(days=2)
        three_before_date = today_date - timedelta(days=3)
        four_before_date = today_date - timedelta(days=4)

        yesterday_attend=session_sqlite.query(Attendance).filter_by(emp_id=emp_id,date=yesterday_date).first()
        if yesterday_attend and (yesterday_attend.attendance=='Present' or yesterday_attend.attendance=='Half day' ):
            two_before_attend=session_sqlite.query(Attendance).filter_by(emp_id=emp_id,date=two_before_date).first()
            if two_before_attend and (two_before_attend.attendance=='Present' or two_before_attend.attendance=='Half day'):
                two_before_attend_s_continue=session_sqlite.query(comp_off).filter_by(emp_id=emp_id,date=two_before_attend)
                yesterday_attend_s_continue=session_sqlite.query(comp_off).filter_by(emp_id=emp_id,date=yesterday_attend)
                if two_before_attend_s_continue or yesterday_attend_s_continue:
                    if two_before_attend_s_continue:
                        session_sqlite.delete(two_before_attend_s_continue)
                    if yesterday_attend_s_continue:
                        session_sqlite.delete(yesterday_attend_s_continue)
                    session_sqlite.commit()
                    three_before_attend=session_sqlite.query(Attendance).filter_by(emp_id=emp_id,date=three_before_date).first()
                    if three_before_attend.attendance=='Week Off':
                        return 'Rest'
                    elif four_before_attend.attendance=='Rest':
                        return 'Week Off'
                three_before_attend=session_sqlite.query(Attendance).filter_by(emp_id=emp_id,date=three_before_date).first()
                if three_before_attend and (three_before_attend.attendance=='Present' or three_before_attend.attendance=='Half day'):
                    four_before_attend=session_sqlite.query(Attendance).filter_by(emp_id=emp_id,date=four_before_date).first()
                    if four_before_attend.attendance and four_before_attend.attendance=='Week Off':
                        return 'Rest'
                    elif four_before_attend.attendance=='Rest':
                        return 'Week Off'

        print('eng dhan problem')
        return None
    except Exception as e:
        print(f"Error in check_ft: {str(e)}")
        return None
    finally:
        session_sqlite.close()

def get_current_shift():
    try:
        now = datetime.now().time()
        # now=datetime(2024,2,2,5,0,0).time()
        print(now)
        # current_time = datetime.strptime(now.strftime('%H:%M:%S'), '%H:%M:%S').time()
        shift_times = session_sqlite.query(Shift_time).all()
        shifts=[]
        for shift in shift_times:
            start=shift.shiftIntime
            end=shift.shift_Outtime

            if start < end:
                if start <= now < end:
                    print(start , '<', now , '<', end)
                    shifts.append(shift.shiftType)
            else: # Over midnight
                if start <= now or now < end:
                    print(start , '<', now , '<', end)
                    shifts.append(shift.shiftType)
        print(shifts,'\n\n\n\n\n\n')
        return shifts
    except Exception as e:
        print(f"Error in get_current_shift: {str(e)}")
        return []
    finally:
        session_sqlite.close()

def out_time_reminder_email():
    try:
        todaydate = datetime.now().date()
        yesterday = (datetime.now() - timedelta(days=1)).date()

        last_shift = session_sqlite.query(Attendance).filter((func.DATE(Attendance.date) == todaydate) & (Attendance.inTime != None) & (Attendance.outTime == None)).all()
        yesterday_last_shift = session_sqlite.query(Attendance).filter((func.DATE(Attendance.date) == yesterday) & (Attendance.inTime != None) & (Attendance.outTime == None)).all()

        print("\n\n\n\n\n\n\n\ninside the code")
        print(last_shift)
        print(yesterday_last_shift)

        if last_shift:
            for i in last_shift:
                emailid = session_sqlite.query(Emp_login).filter_by(emp_id=i.emp_id).first()
                print("\n\n\n\n\n\n\n\n\nemailid",emailid)
                if emailid:
                    email = emailid.email
                    subject = "Out Time Missing"
                    body = f"Dear Employee,\n\nYour out time is missing for today's shift. Please make sure to record your out time before leaving the premises.\n\nBest regards,\nKanchi Karpooram Limited"
                    send_mail(email, subject, body)

        if yesterday_last_shift:
            for i in yesterday_last_shift:
                emailid = session_sqlite.query(Emp_login).filter_by(emp_id=i.emp_id).first()
                print("\n\n\n\n\n\n\n\n\nemailid",emailid)
                if emailid:
                    email = emailid.email
                    subject = "Out Time Missing"
                    body = f"Dear Employee,\n\nYour out time is missing for today's shift. Please make sure to record your out time before leaving the premises.\n\nBest regards,\nKanchi Karpooram Limited"
                    send_mail(email, subject, body)
    except Exception as e:
        print(f"Error in out_time_reminder_email: {str(e)}")
    finally:
        session_sqlite.close()

def out_time_reminder_message():
    try:
        todaydate = datetime.now().date()
        yesterday = (datetime.now() - timedelta(days=1)).date()

        last_shift = session_sqlite.query(Attendance).filter((func.DATE(Attendance.date) == todaydate) & (Attendance.inTime != None) & (Attendance.outTime == None)).all()
        yesterday_last_shift = session_sqlite.query(Attendance).filter((func.DATE(Attendance.date) == yesterday) & (Attendance.inTime != None) & (Attendance.outTime == None)).all()

        print("\n\n\n\n\n\n\n\ninside the code")
        print(last_shift)
        print(yesterday_last_shift)

        if last_shift:
            for i in last_shift:
                number = []
                emailid = session_sqlite.query(Emp_login).filter_by(emp_id=i.emp_id).first()
                print("\n\n\n\n\n\n\n\n\nemailid",emailid)
                if emailid:
                    number.append(emailid.phoneNumber)
                    message_body = f"Dear Employee,\n\nYour out time is missing for today's shift. Please make sure to record your out time before leaving the premises.\n\nBest regards,\nKanchi Karpooram Limited"
                    send_sms(number, message_body)

        if yesterday_last_shift:
            number = []
            for i in yesterday_last_shift:
                emailid = session_sqlite.query(Emp_login).filter_by(emp_id=i.emp_id).first()
                print("\n\n\n\n\n\n\n\n\nemailid",emailid)
                if emailid:
                    number.append(emailid.phoneNumber)
                    message_body = f"Dear Employee,\n\nYour out time is missing for today's shift. Please make sure to record your out time before leaving the premises.\n\nBest regards,\nKanchi Karpooram Limited"
                    print("list of numbers ",number)
                    send_sms(number, message_body)
    except Exception as e:
        print(f"Error in out_time_reminder_message: {str(e)}")
    finally:
        session_sqlite.close()

# def punch_out_reminder(emp_id):
#     if emp_id:
#             number = []
#             emailid = session_sqlite.query(Emp_login).filter_by(emp_id=emp_id).first()
#             print("\n\n\n\n\n\n\n\n\nemailid",emailid)
#             if emailid:
#                 number.append(emailid.phoneNumber)
#                 message_body = f"Dear Employee,\n\nYour out time is missing for today's shift. Please make sure to record your out time before leaving the premises.\n\nBest regards,\nKanchi Karpooram Limited"
#                 send_sms(number, message_body)

#     if emp_id:
#             emailid = session_sqlite.query(Emp_login).filter_by(emp_id=emp_id).first()
#             print("\n\n\n\n\n\n\n\n\nemailid",emailid)
#             if emailid:
#                 email = emailid.email
#                 subject = "Out Time Missing"
#                 body = f"Dear Employee,\n\nYour out time is missing for today's shift. Please make sure to record your out time before leaving the premises.\n\nBest regards,\nKanchi Karpooram Limited"
#                 send_mail(email, subject, body)
