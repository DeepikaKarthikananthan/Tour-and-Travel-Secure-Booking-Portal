import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))


class Config:
    # NOTE: In a real production deployment this secret key should be loaded
    # from an environment variable. It is hardcoded here only to make the
    # local lab environment simple to run out of the box.
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-key-change-in-production")

    SQLALCHEMY_DATABASE_URI = "sqlite:///" + os.path.join(BASE_DIR, "instance", "travel.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"

    # Pagination
    TOURS_PER_PAGE = 9
    BOOKINGS_PER_PAGE = 10
