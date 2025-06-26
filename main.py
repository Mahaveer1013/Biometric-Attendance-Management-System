# main.py
from app import create_app, socketio
app = create_app()
socketio.init_app(app)  #  Initialize socketio with the app

if __name__ == '__main__':
    socketio.run(app, debug=True, host='0.0.0.0')
    #socketio.run(app, debug=True)
