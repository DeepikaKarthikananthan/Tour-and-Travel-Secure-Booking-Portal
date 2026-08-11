from datetime import datetime

from extensions import db


class Tour(db.Model):
    __tablename__ = "tours"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    destination = db.Column(db.String(100), nullable=False, index=True)
    category = db.Column(db.String(50), nullable=False, default="General")
    description = db.Column(db.Text, nullable=False, default="")
    itinerary = db.Column(db.Text, nullable=True)
    duration = db.Column(db.String(50), nullable=False, default="")  # e.g. "5 Days / 4 Nights"
    price = db.Column(db.Float, nullable=False, default=0.0)
    child_price = db.Column(db.Float, nullable=False, default=0.0)
    available_seats = db.Column(db.Integer, nullable=False, default=0)
    start_date = db.Column(db.Date, nullable=True)
    end_date = db.Column(db.Date, nullable=True)
    image_url = db.Column(db.String(400), nullable=True)
    included = db.Column(db.Text, nullable=True)
    excluded = db.Column(db.Text, nullable=True)
    rating = db.Column(db.Float, nullable=False, default=4.5)
    difficulty = db.Column(db.String(30), nullable=False, default="Easy")  # Easy, Moderate, Challenging, Expedition
    season = db.Column(db.String(30), nullable=False, default="All Year")   # Spring, Summer, Autumn, Winter, All Year
    tags = db.Column(db.String(200), nullable=True, default="Popular, Recommended")  # Comma separated
    latitude = db.Column(db.Float, nullable=True, default=46.8182)
    longitude = db.Column(db.Float, nullable=True, default=8.2275)
    max_seats = db.Column(db.Integer, nullable=False, default=30)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    bookings = db.relationship("Booking", backref="tour", lazy=True)
    feedbacks = db.relationship("Feedback", backref="tour", lazy=True)
    favorited_by = db.relationship("Favorite", backref="tour", lazy=True)

    def included_list(self):
        return [x.strip() for x in (self.included or "").split("\n") if x.strip()]

    def excluded_list(self):
        return [x.strip() for x in (self.excluded or "").split("\n") if x.strip()]

    def itinerary_list(self):
        return [x.strip() for x in (self.itinerary or "").split("\n") if x.strip()]

    def average_rating(self):
        if not self.feedbacks:
            return self.rating
        vals = [f.rating for f in self.feedbacks]
        return round(sum(vals) / len(vals), 1)

    def __repr__(self):
        return f"<Tour {self.name}>"
