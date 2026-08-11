import random
import string
from datetime import datetime, date

from extensions import db


def _generate_reference():
    return "TB" + "".join(random.choices(string.digits, k=8))


def auto_sync_booking_statuses(session):
    """
    Domain logic helper: Automatically transitions past trips (travel_date < today)
    from active statuses ('Booked', 'Confirmed', 'Pending') to 'Completed'.
    Commits session if any records were updated.
    """
    today = date.today()
    past_bookings = session.query(Booking).filter(
        Booking.travel_date < today,
        Booking.status.in_(["Booked", "Confirmed", "Pending"])
    ).all()
    
    if past_bookings:
        for b in past_bookings:
            b.status = "Completed"
        session.commit()


class Booking(db.Model):
    __tablename__ = "bookings"

    id = db.Column(db.Integer, primary_key=True)
    reference = db.Column(db.String(20), unique=True, nullable=False, default=_generate_reference)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    tour_id = db.Column(db.Integer, db.ForeignKey("tours.id"), nullable=False)

    travel_date = db.Column(db.Date, nullable=False)
    adults = db.Column(db.Integer, nullable=False, default=1)
    children = db.Column(db.Integer, nullable=False, default=0)
    contact_number = db.Column(db.String(20), nullable=True)
    special_requests = db.Column(db.Text, nullable=True)

    total_amount = db.Column(db.Float, nullable=False, default=0.0)
    discount_amount = db.Column(db.Float, nullable=False, default=0.0)
    coupon_code = db.Column(db.String(30), nullable=True)
    has_insurance = db.Column(db.Boolean, default=False, nullable=False)
    hotel_tier = db.Column(db.String(30), default="Standard", nullable=False)
    status = db.Column(db.String(20), nullable=False, default="Booked")
    # Booked, Confirmed, Pending, Completed, Cancelled

    refund_amount = db.Column(db.Float, default=0.0, nullable=False)
    refund_status = db.Column(db.String(30), default="None", nullable=False)  # 'None', 'Refund Requested', 'Pending Refund', 'Refunded', 'Ineligible'
    refund_reason = db.Column(db.Text, nullable=True)
    admin_refund_note = db.Column(db.Text, nullable=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def total_travelers(self):
        return self.adults + self.children

    def is_past(self):
        return self.travel_date < date.today()

    def is_cancellable(self):
        return self.status in ["Booked", "Confirmed", "Pending"] and not self.is_past()

    def status_badge_class(self):
        return {
            "Booked": "success",
            "Confirmed": "success",
            "Pending": "warning",
            "Completed": "info",
            "Cancelled": "danger",
        }.get(self.status, "secondary")

    def __repr__(self):
        return f"<Booking {self.reference}>"
