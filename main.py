from app import create_app
from werkzeug.serving import run_simple

app = create_app()
    
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8444)
    # socketio.run(app, debug=True)