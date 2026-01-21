import os
from flask import Flask, render_template, session, redirect, url_for
from config import Config
from extensions import mongo
from auth_routes import auth_bp
from admin_routes import admin_bp
from organizer_routes import organizer_bp


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    mongo.init_app(app)

    # Register blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(organizer_bp, url_prefix='/organizer')

    @app.route('/')
    def index():
        return render_template('index.html')

    @app.route('/logout')
    def logout():
        session.clear()  # removes session['role'] and others
        return redirect(url_for('index'))


    return app


app = create_app()

if __name__ == '__main__':
    # Create default admin on first run
    if not mongo.db.admins.find_one({'username': 'admin'}):
        from utils_security import hash_password
        mongo.db.admins.insert_one({
            'username': 'admin',
            'password': hash_password('admin123'),
            'status': 'approved',
        })
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
