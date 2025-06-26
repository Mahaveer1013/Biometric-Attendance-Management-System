from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_socketio import SocketIO
import os
from dotenv import load_dotenv
load_dotenv()

from sqlalchemy import create_engine

# Initialize SQLAlchemy
db = SQLAlchemy()
DB_NAME = os.getenv("DB_NAME")

mysql_engine = None
sqlite_engine = None

# Create a socketio instance without initializing it
socketio = SocketIO()

# Factory function to create the Flask app
def create_app():
    global mysql_engine, sqlite_engine  # Declare as global to use them inside the function

    app = Flask(__name__, static_folder='static')

    # Configure the app
    app.config['SECRET_KEY'] = os.getenv("SECRET_KEY")
    db_path = os.path.abspath(os.path.dirname(__file__))
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{os.path.join(db_path, DB_NAME)}'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # Define paths for file uploads
    UPLOAD_FOLDER = os.path.join(app.root_path, 'static/img/profile')
    app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
    EXCEL_FOLDER = os.path.join(app.root_path, 'static/excel')
    app.config['EXCEL_FOLDER'] = EXCEL_FOLDER
    DAY_ATTENDANCE_FOLDER = os.path.join(app.root_path, 'static\XLfile')
    app.config['DAY_ATTENDANCE_FOLDER'] = DAY_ATTENDANCE_FOLDER

    app.config['MAIL_SERVER'] = os.getenv("MAIL_SERVER")
    app.config['MAIL_PORT'] = os.getenv("MAIL_PORT")
    app.config['MAIL_USE_SSL'] = os.getenv("MAIL_USE_SSL")

    app.config['MYSQL_HOST'] = os.getenv("MYSQL_HOST")
    app.config['MYSQL_USER'] = os.getenv("MYSQL_USER")
    app.config['MYSQL_PASSWORD'] = os.getenv("MYSQL_PASSWORD")
    app.config['MYSQL_DB'] = os.getenv("MYSQL_DB")
    app.config['MYSQL_PORT'] = os.getenv("MYSQL_PORT")


    from . import models
    from .models import Attendance,Emp_login
    models.db.init_app(app)
    login_manager = LoginManager()
    login_manager.login_view = 'auth.login'
    login_manager.init_app(app)
    @login_manager.user_loader
    def load_user(user_id):
        return Emp_login.query.get(int(user_id))
    # Create the database if it doesn't exist

    # Define the engines
    mysql_engine = create_engine(
        f"mysql+pymysql://{app.config['MYSQL_USER']}:{app.config['MYSQL_PASSWORD']}@{app.config['MYSQL_HOST']}:{app.config['MYSQL_PORT']}/{app.config['MYSQL_DB']}",echo=True
    )

    sqlite_engine = create_engine(f'sqlite:///{os.path.join(db_path, DB_NAME)}', echo=True)

    # Bind the models to engines
    Attendance.metadata.bind = mysql_engine

    # Import and register blueprints
    from .auth import auth
    from .views import views
    app.register_blueprint(views, url_prefix='/')
    app.register_blueprint(auth, url_prefix='/')

    # Mail configuration
    socketio.init_app(app)
    create_database(app)


    return app

# Function to create the database if it doesn't exist
def create_database(app):
    if not os.path.exists(os.path.join(app.instance_path, DB_NAME)):
        with app.app_context():
            db.create_all()
        print('Created Database!')
