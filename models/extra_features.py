from datetime import datetime
from extensions import db


class Coupon(db.Model):
    __tablename__ = "coupons"

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(30), unique=True, nullable=False)
    discount_percent = db.Column(db.Float, nullable=False, default=10.0)
    max_discount = db.Column(db.Float, nullable=True, default=200.0)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def calculate_discount(self, original_price):
        discount = (original_price * self.discount_percent) / 100.0
        if self.max_discount and discount > self.max_discount:
            discount = self.max_discount
        return round(discount, 2)


class CustomTripRequest(db.Model):
    __tablename__ = "custom_trip_requests"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(150), nullable=False)
    phone = db.Column(db.String(30), nullable=True)
    destination = db.Column(db.String(120), nullable=False)
    budget = db.Column(db.String(50), nullable=True)
    travelers = db.Column(db.Integer, default=1, nullable=False)
    preferred_month = db.Column(db.String(50), nullable=True)
    notes = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(30), default="Pending Review", nullable=False)
    admin_quote = db.Column(db.Float, nullable=True, default=0.0)
    admin_notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class NewsletterSubscriber(db.Model):
    __tablename__ = "newsletter_subscribers"

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(150), unique=True, nullable=False)
    subscribed_at = db.Column(db.DateTime, default=datetime.utcnow)


class AssistanceTicket(db.Model):
    __tablename__ = "assistance_tickets"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(150), nullable=False)
    phone = db.Column(db.String(30), nullable=True)
    category = db.Column(db.String(50), nullable=False, default="General Assistance")
    subject = db.Column(db.String(200), nullable=False)
    message = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(30), default="Open", nullable=False)  # 'Open', 'In Progress', 'Resolved'
    admin_response = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class PromotionCampaign(db.Model):
    __tablename__ = "promotion_campaigns"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text, nullable=True)
    banner_text = db.Column(db.String(255), nullable=True)
    discount_percent = db.Column(db.Float, default=15.0, nullable=False)
    promo_code = db.Column(db.String(50), nullable=True)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
