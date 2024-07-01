from flask import Flask
from flask_cors import CORS
from dotenv import load_dotenv
from config import Config
from app.routes.ml_routes import ml_routes
from app.routes.code_analysis_routes import code_analysis_routes

load_dotenv()

def create_app(config_class=Config):
    app = Flask(__name__)
    
    # Configure CORS
    CORS(app, resources={r"/*": {
        "origins": "http://localhost:3000",
        "methods": ["GET", "POST", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"]
    }})
    
    app.config.from_object(config_class)

    app.register_blueprint(ml_routes, url_prefix='/ml')
    app.register_blueprint(code_analysis_routes, url_prefix='/code')

    @app.after_request
    def after_request(response):
        response.headers.add('Access-Control-Allow-Origin', 'http://localhost:3000')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
        response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
        return response

    return app

if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)