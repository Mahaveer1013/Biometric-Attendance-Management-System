# main.py
from app import create_app, socketio

app = create_app()
socketio.init_app(app)  #  Initialize socketio with the app

# app.config['MYSQL_HOST'] = 'localhost'
# app.config['MYSQL_USER'] = 'root'
# app.config['MYSQL_PASSWORD'] = 'sabari'
# app.config['MYSQL_DB'] = 'server'

# mysql = MySQL(app)

# Create Table
# with app.app_context():
#     cursor = mysql.connection.cursor()
#     cursor.execute('''
#         CREATE TABLE IF NOT EXISTS Attendance (
#             id INT AUTO_INCREMENT PRIMARY KEY,
#             emp_id INT NOT NULL,
#             inTime DATETIME NOT NULL,
#             outTime DATETIME,
#             shiftType VARCHAR(255)
#         )
#     ''')
#     mysql.connection.commit()
#     cursor.close()

# # Function to add dummy data
# def add_dummy_data():
#     with app.app_context():
#         cursor = mysql.connection.cursor()

#         # Generate random emp_id (between 1 and 100) and shift (e.g., '8A', '8B', '8C')
#         emp_id = random.randint(1, 100)
#         shift = random.choice(['8A', '8B', '8C'])

#         # Generate random intime within the last 7 days
#         intime = datetime.now()

#         # Calculate random outtime as intime + random duration (between 1 and 4 hours)
#         outtime = intime + timedelta(hours=random.uniform(1, 4))

#         cursor.execute('''\

#             INSERT INTO Attendance (emp_id, inTime, outTime, shiftType) VALUES (%s, %s, %s, %s)
#         ''', (emp_id, intime, outtime, shift))

#         mysql.connection.commit()
#         cursor.close()
#         print("Data added for emp_id:", emp_id, "and shift:", shift, "with intime:", intime, "and outtime:", outtime)

# # Initialize scheduler
# scheduler = BackgroundScheduler()
# scheduler.add_job(add_dummy_data, trigger='interval', seconds=1)
# scheduler.start()

if __name__ == '__main__':
    socketio.run(app, debug=True, host='0.0.0.0')
    #socketio.run(app, debug=True)
