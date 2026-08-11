from extensions import db  # noqa: F401

# Import models so they are registered with SQLAlchemy metadata as soon as
# the `models` package is imported anywhere in the app.
from .user import User              # noqa: E402,F401
from .tour import Tour              # noqa: E402,F401
from .booking import Booking, auto_sync_booking_statuses  # noqa: E402,F401
from .feedback import Feedback, Favorite  # noqa: E402,F401
from .extra_features import Coupon, CustomTripRequest, NewsletterSubscriber, AssistanceTicket, PromotionCampaign, LockoutRevokeRequest  # noqa: E402,F401
