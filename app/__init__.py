from flask import Flask
from flask_cors import CORS
from config import Config

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Set up CORS
    CORS(app, resources={r"/*": {"origins": "http://localhost:3000"}}, supports_credentials=True)

    from app.routes.ml_routes import ml_routes
    app.register_blueprint(ml_routes, url_prefix='/ml')

    from app.routes.code_analysis_routes import code_analysis_routes
    app.register_blueprint(code_analysis_routes, url_prefix='/code')
    @app.route("/")
    def api_intro():
        return "<p>API says hello!</p>"

    return app