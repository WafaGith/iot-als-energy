from flask import Flask, send_from_directory, render_template, abort
from flask_cors import CORS
import os

from database import init_default_admin, get_config
from routes import auth_bp, sensor_bp, dashboard_bp, prediction_bp

base_dir = os.path.abspath(os.path.dirname(__file__))
app = Flask(__name__, template_folder='templates')
CORS(app) # Allow cross-origin for frontend

@app.route('/')
def serve_index():
    return render_template('index.html')

@app.route('/<path:filename>')
def serve_files(filename):
    if filename.endswith('.html'):
        template_path = os.path.join(base_dir, 'templates', filename)
        if os.path.exists(template_path):
            return render_template(filename)
            
    # Fallback for assets, components (like components/sidebar.html), etc
    file_path = os.path.join(base_dir, filename)
    if os.path.exists(file_path):
        return send_from_directory(base_dir, filename)
        
    abort(404)

try:
    init_default_admin()
except Exception as e:
    print(f"Skipping admin init (maybe DB not ready?): {e}")

config = get_config()
app.config['SECRET_KEY'] = config.get('jwt_secret', 'my_super_secret_key_123')

# Register Blueprints
app.register_blueprint(auth_bp, url_prefix='/api/auth')
app.register_blueprint(sensor_bp, url_prefix='/api/sensor')
app.register_blueprint(dashboard_bp, url_prefix='/api')
app.register_blueprint(prediction_bp, url_prefix='/api')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
