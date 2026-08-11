from datetime import datetime

from extensions import db


class Feedback(db.Model):
    __tablename__ = "feedback"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    tour_id = db.Column(db.Integer, db.ForeignKey("tours.id"), nullable=False)
    booking_id = db.Column(db.Integer, db.ForeignKey("bookings.id"), nullable=True)

    rating = db.Column(db.Integer, nullable=False, default=5)  # 1-5
    comment = db.Column(db.Text, nullable=False, default="")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<Feedback {self.id} rating={self.rating}>"


class Favorite(db.Model):
    __tablename__ = "favorites"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    tour_id = db.Column(db.Integer, db.ForeignKey("tours.id"), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = (db.UniqueConstraint("user_id", "tour_id", name="uq_user_tour_favorite"),)

    def __repr__(self):
        return f"<Favorite user={self.user_id} tour={self.tour_id}>"
