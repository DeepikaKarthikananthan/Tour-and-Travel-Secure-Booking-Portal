"""
Shared Flask extension instances.

Keeping the SQLAlchemy instance here (instead of inside models/__init__.py)
avoids circular-import problems between app.py, the models package and the
routes package.
"""
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()
