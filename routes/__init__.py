from .auth import auth_bp
from .sensor import sensor_bp
from .dashboard import dashboard_bp
from .prediction import prediction_bp

__all__ = ['auth_bp', 'sensor_bp', 'dashboard_bp', 'prediction_bp']
