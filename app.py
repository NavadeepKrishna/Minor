from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_bcrypt import Bcrypt
from config import Config

# Initialize extensions outside the app factory
db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
bcrypt = Bcrypt()

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Initialize extensions with the app
    db.init_app(app)
    migrate.init_app(app, db)
    bcrypt.init_app(app)
    
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message_category = 'info'

    # Register Blueprints
    from routes import main as main_bp
    from routes import auth as auth_bp
    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp, url_prefix='/auth')

    # Import models so Flask-Migrate knows about them
    from models import User, Role, Scan
    
    return app

# We remove the 'if __name__ == "__main__":' block here 
# because we rely on the 'flask run' command with the factory pattern.

# User loader function for Flask-Login
from models import User # Import here to avoid circular dependency issues
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))