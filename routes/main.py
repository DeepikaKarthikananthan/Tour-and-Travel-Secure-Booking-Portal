from flask import Blueprint, render_template, request, flash, redirect, url_for

from models import db, Tour, Feedback
from routes.utils import get_current_user

main_bp = Blueprint("main", __name__)


@main_bp.app_context_processor
def inject_globals():
    from flask import session
    security_mode = session.get("security_mode", "ON")
    return {
        "current_user": get_current_user(),
        "security_mode": security_mode
    }


@main_bp.route("/demo/toggle-security")
def toggle_security():
    from flask import session
    current = session.get("security_mode", "ON")
    new_mode = "OFF" if current == "ON" else "ON"
    session["security_mode"] = new_mode
    if new_mode == "OFF":
        flash("⚠️ DEMO MODE ACTIVE: Security Controls DISABLED! Vulnerable code execution enabled for supervisor demo.", "warning")
    else:
        flash("🛡️ SECURITY MODE ENFORCED: Defensive controls, parameterized queries, and rate limiting ACTIVE.", "success")
    referrer = request.referrer or url_for("main.home")
    return redirect(referrer)


@main_bp.route("/")
def home():
    featured_tours = (
        Tour.query.filter_by(is_active=True).order_by(Tour.rating.desc()).limit(6).all()
    )
    seen = set()
    destinations = []
    for tour in Tour.query.filter_by(is_active=True).order_by(Tour.rating.desc()).all():
        if tour.destination not in seen:
            seen.add(tour.destination)
            destinations.append((tour.destination, tour.image_url))
        if len(destinations) >= 8:
            break
    testimonials = (
        Feedback.query.filter(Feedback.rating >= 4)
        .order_by(Feedback.created_at.desc())
        .limit(6)
        .all()
    )
    return render_template(
        "home.html",
        featured_tours=featured_tours,
        destinations=destinations,
        testimonials=testimonials,
    )


@main_bp.route("/about")
def about():
    stats = {
        "tours": Tour.query.count() or 500,
        "travelers": 10000,
        "destinations": db.session.query(Tour.destination).distinct().count() or 50,
        "rating": 4.8,
    }
    return render_template("about.html", stats=stats)


@main_bp.route("/contact", methods=["GET", "POST"])
def contact():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip()
        message = request.form.get("message", "").strip()

        if not name or not email or not message:
            flash("Please fill in all required fields.", "danger")
        else:
            # In a full production app this would be persisted or emailed.
            flash("Thank you for reaching out! Our team will get back to you soon.", "success")
            return redirect(url_for("main.contact"))

    return render_template("contact.html")
