import re
from datetime import date

from flask import Blueprint, render_template, request, redirect, url_for, flash

from models import db, Booking, Tour, Favorite, Feedback, auto_sync_booking_statuses
from routes.utils import login_required, get_current_user

profile_bp = Blueprint("profile", __name__)

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
PHONE_RE = re.compile(r"^[0-9+\-\s()]{7,20}$")


@profile_bp.route("/dashboard")
@login_required
def dashboard():
    user = get_current_user()

    # Automatically transition past trips to Completed in DB
    auto_sync_booking_statuses(db.session)

    all_bookings = Booking.query.filter_by(user_id=user.id).order_by(Booking.created_at.desc()).all()
    upcoming = [b for b in all_bookings if b.status in ["Booked", "Confirmed", "Pending"] and b.travel_date >= date.today()]
    previous = [b for b in all_bookings if b.status in ["Completed", "Cancelled"] or b.travel_date < date.today()]

    favorites = (
        db.session.query(Tour)
        .join(Favorite, Favorite.tour_id == Tour.id)
        .filter(Favorite.user_id == user.id)
        .limit(6)
        .all()
    )

    return render_template(
        "dashboard.html",
        user=user,
        upcoming=upcoming[:5],
        previous=previous[:5],
        total_bookings=len(all_bookings),
        favorites=favorites,
    )


@profile_bp.route("/profile", methods=["GET", "POST"])
@login_required
def view_profile():
    user = get_current_user()

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        phone = request.form.get("phone", "").strip()

        errors = []
        if len(name) < 2:
            errors.append("Please enter your full name.")
        if phone and not PHONE_RE.match(phone):
            errors.append("Please enter a valid phone number.")

        if errors:
            for e in errors:
                flash(e, "danger")
        else:
            user.name = name
            user.phone = phone
            db.session.commit()
            flash("Profile updated successfully.", "success")
        return redirect(url_for("profile.view_profile"))

    return render_template("profile.html", user=user)


@profile_bp.route("/profile/change-password", methods=["POST"])
@login_required
def change_password():
    user = get_current_user()
    current_password = request.form.get("current_password", "")
    new_password = request.form.get("new_password", "")
    confirm_password = request.form.get("confirm_password", "")

    if not user.check_password(current_password):
        flash("Current password is incorrect.", "danger")
    elif len(new_password) < 6:
        flash("New password must be at least 6 characters long.", "danger")
    elif new_password != confirm_password:
        flash("New passwords do not match.", "danger")
    else:
        user.set_password(new_password)
        db.session.commit()
        flash("Password changed successfully.", "success")

    return redirect(url_for("profile.view_profile"))


@profile_bp.route("/favorites")
@login_required
def favorites():
    user = get_current_user()
    tours = (
        db.session.query(Tour)
        .join(Favorite, Favorite.tour_id == Tour.id)
        .filter(Favorite.user_id == user.id)
        .all()
    )
    return render_template("favorites.html", tours=tours)


@profile_bp.route("/favorites/<int:tour_id>/toggle", methods=["POST"])
@login_required
def toggle_favorite(tour_id):
    user = get_current_user()
    tour = Tour.query.get_or_404(tour_id)

    existing = Favorite.query.filter_by(user_id=user.id, tour_id=tour.id).first()
    if existing:
        db.session.delete(existing)
        db.session.commit()
        flash("Removed from favorites.", "info")
    else:
        db.session.add(Favorite(user_id=user.id, tour_id=tour.id))
        db.session.commit()
        flash("Added to favorites.", "success")

    return redirect(request.referrer or url_for("tours.tour_details", tour_id=tour.id))


@profile_bp.route("/feedback", methods=["GET", "POST"])
@login_required
def feedback():
    user = get_current_user()

    if request.method == "POST":
        tour_id = request.form.get("tour_id", type=int)
        rating = request.form.get("rating", type=int)
        comment = request.form.get("comment", "").strip()

        tour = Tour.query.get(tour_id) if tour_id else None
        errors = []
        if not tour:
            errors.append("Please select a valid tour.")
        if not rating or rating < 1 or rating > 5:
            errors.append("Please select a rating between 1 and 5.")
        if len(comment) < 3:
            errors.append("Please write a comment about your experience.")

        if errors:
            for e in errors:
                flash(e, "danger")
        else:
            fb = Feedback(user_id=user.id, tour_id=tour.id, rating=rating, comment=comment)
            db.session.add(fb)
            db.session.commit()
            flash("Thank you for your feedback!", "success")
        return redirect(url_for("profile.feedback"))

    completed_tours = (
        db.session.query(Tour)
        .join(Booking, Booking.tour_id == Tour.id)
        .filter(Booking.user_id == user.id)
        .distinct()
        .all()
    )
    my_feedback = (
        Feedback.query.filter_by(user_id=user.id).order_by(Feedback.created_at.desc()).all()
    )

    return render_template("feedback.html", tours=completed_tours, my_feedback=my_feedback)
