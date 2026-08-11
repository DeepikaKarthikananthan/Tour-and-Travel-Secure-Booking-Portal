from datetime import datetime, date

from flask import Blueprint, render_template, request, redirect, url_for, flash, session

from models import db, User, Tour, Booking, Feedback, auto_sync_booking_statuses
from routes.utils import admin_required

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")


# ---------------------------------------------------------------- AUTH ----

@admin_bp.route("/login", methods=["GET", "POST"])
def login():
    if session.get("admin_id"):
        return redirect(url_for("admin.dashboard"))

    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        admin = User.query.filter_by(email=email, role="admin").first()
        if admin and admin.check_password(password):
            if not admin.is_active:
                flash("This admin account has been deactivated.", "danger")
                return render_template("admin/login.html")
            session["admin_id"] = admin.id
            flash(f"Welcome back, {admin.name}.", "success")
            return redirect(url_for("admin.dashboard"))

        flash("Invalid admin credentials.", "danger")

    return render_template("admin/login.html")


@admin_bp.route("/logout")
def logout():
    session.pop("admin_id", None)
    flash("Admin logged out.", "info")
    return redirect(url_for("admin.login"))


# ----------------------------------------------------------- DASHBOARD ----

@admin_bp.route("/")
@admin_bp.route("/dashboard")
@admin_required
def dashboard():
    auto_sync_booking_statuses(db.session)

    stats = {
        "total_users": User.query.filter_by(role="user").count(),
        "total_tours": Tour.query.count(),
        "total_bookings": Booking.query.count(),
        "pending_bookings": Booking.query.filter(Booking.status.in_(["Booked", "Pending"])).count(),
        "confirmed_bookings": Booking.query.filter_by(status="Confirmed").count(),
        "total_revenue": db.session.query(db.func.coalesce(db.func.sum(Booking.total_amount), 0))
        .filter(Booking.status.in_(["Booked", "Confirmed", "Completed"]))
        .scalar(),
        "total_feedback": Feedback.query.count(),
    }

    recent_bookings = Booking.query.order_by(Booking.created_at.desc()).limit(8).all()

    # Simple monthly revenue breakdown (last 6 months) for the chart.
    bookings = Booking.query.filter(Booking.status.in_(["Booked", "Confirmed", "Completed"])).all()
    monthly = {}
    for b in bookings:
        key = b.created_at.strftime("%Y-%m") if b.created_at else "unknown"
        monthly[key] = monthly.get(key, 0) + b.total_amount
    chart_labels = sorted(monthly.keys())[-6:]
    chart_values = [round(monthly[k], 2) for k in chart_labels]

    status_counts = {
        "Booked": Booking.query.filter_by(status="Booked").count(),
        "Confirmed": Booking.query.filter_by(status="Confirmed").count(),
        "Pending": Booking.query.filter_by(status="Pending").count(),
        "Completed": Booking.query.filter_by(status="Completed").count(),
        "Cancelled": Booking.query.filter_by(status="Cancelled").count(),
    }

    return render_template(
        "admin/dashboard.html",
        stats=stats,
        recent_bookings=recent_bookings,
        chart_labels=chart_labels,
        chart_values=chart_values,
        status_counts=status_counts,
    )


# ------------------------------------------------------------- TOURS ----

@admin_bp.route("/tours")
@admin_required
def manage_tours():
    search = request.args.get("q", "").strip()
    query = Tour.query
    if search:
        like = f"%{search}%"
        query = query.filter(db.or_(Tour.name.ilike(like), Tour.destination.ilike(like)))
    tours = query.order_by(Tour.created_at.desc()).all()
    return render_template("admin/tours.html", tours=tours, search=search)


def _parse_tour_form(form):
    def parse_date(value):
        try:
            return datetime.strptime(value, "%Y-%m-%d").date()
        except (ValueError, TypeError):
            return None

    return {
        "name": form.get("name", "").strip(),
        "destination": form.get("destination", "").strip(),
        "category": form.get("category", "General").strip() or "General",
        "description": form.get("description", "").strip(),
        "itinerary": form.get("itinerary", "").strip(),
        "duration": form.get("duration", "").strip(),
        "price": form.get("price", type=float) or 0.0,
        "child_price": form.get("child_price", type=float) or 0.0,
        "available_seats": form.get("available_seats", type=int) or 0,
        "start_date": parse_date(form.get("start_date", "")),
        "end_date": parse_date(form.get("end_date", "")),
        "image_url": form.get("image_url", "").strip(),
        "included": form.get("included", "").strip(),
        "excluded": form.get("excluded", "").strip(),
    }


@admin_bp.route("/tours/add", methods=["GET", "POST"])
@admin_required
def add_tour():
    if request.method == "POST":
        data = _parse_tour_form(request.form)
        errors = []
        if not data["name"]:
            errors.append("Tour name is required.")
        if not data["destination"]:
            errors.append("Destination is required.")
        if data["price"] <= 0:
            errors.append("Price must be greater than zero.")
        if data["available_seats"] < 0:
            errors.append("Available seats cannot be negative.")

        if errors:
            for e in errors:
                flash(e, "danger")
            return render_template("admin/add_tour.html", form=request.form)

        tour = Tour(**data)
        db.session.add(tour)
        db.session.commit()
        flash("Tour package added successfully.", "success")
        return redirect(url_for("admin.manage_tours"))

    return render_template("admin/add_tour.html", form={})


@admin_bp.route("/tours/<int:tour_id>/edit", methods=["GET", "POST"])
@admin_required
def edit_tour(tour_id):
    tour = Tour.query.get_or_404(tour_id)

    if request.method == "POST":
        data = _parse_tour_form(request.form)
        errors = []
        if not data["name"]:
            errors.append("Tour name is required.")
        if not data["destination"]:
            errors.append("Destination is required.")
        if data["price"] <= 0:
            errors.append("Price must be greater than zero.")

        if errors:
            for e in errors:
                flash(e, "danger")
            return render_template("admin/edit_tour.html", tour=tour, form=request.form)

        for key, value in data.items():
            setattr(tour, key, value)
        db.session.commit()
        flash("Tour package updated successfully.", "success")
        return redirect(url_for("admin.manage_tours"))

    return render_template("admin/edit_tour.html", tour=tour, form=None)


@admin_bp.route("/tours/<int:tour_id>/delete", methods=["POST"])
@admin_required
def delete_tour(tour_id):
    tour = Tour.query.get_or_404(tour_id)
    if Booking.query.filter_by(tour_id=tour.id).first():
        flash("Cannot delete a tour that has existing bookings. Deactivate it instead.", "warning")
    else:
        db.session.delete(tour)
        db.session.commit()
        flash("Tour package deleted.", "info")
    return redirect(url_for("admin.manage_tours"))


@admin_bp.route("/tours/<int:tour_id>/toggle", methods=["POST"])
@admin_required
def toggle_tour(tour_id):
    tour = Tour.query.get_or_404(tour_id)
    tour.is_active = not tour.is_active
    db.session.commit()
    flash(f"Tour {'activated' if tour.is_active else 'deactivated'}.", "info")
    return redirect(url_for("admin.manage_tours"))


# ---------------------------------------------------------- BOOKINGS ----

@admin_bp.route("/bookings")
@admin_required
def manage_bookings():
    auto_sync_booking_statuses(db.session)

    status = request.args.get("status", "").strip()
    search = request.args.get("q", "").strip()

    query = Booking.query
    if status:
        query = query.filter_by(status=status)
    if search:
        query = query.join(User).filter(
            db.or_(User.name.ilike(f"%{search}%"), User.email.ilike(f"%{search}%"))
        )
    bookings = query.order_by(Booking.created_at.desc()).all()

    return render_template("admin/bookings.html", bookings=bookings, status=status, search=search)


@admin_bp.route("/bookings/<int:booking_id>/status", methods=["POST"])
@admin_required
def update_booking_status(booking_id):
    booking = Booking.query.get_or_404(booking_id)
    new_status = request.form.get("status", "")

    valid = {"Booked", "Confirmed", "Pending", "Completed", "Cancelled"}
    if new_status not in valid:
        flash("Invalid status.", "danger")
        return redirect(url_for("admin.manage_bookings"))

    if new_status == "Cancelled" and booking.status != "Cancelled":
        booking.tour.available_seats += booking.total_travelers()
    elif booking.status == "Cancelled" and new_status != "Cancelled":
        booking.tour.available_seats -= booking.total_travelers()

    booking.status = new_status
    db.session.commit()
    flash(f"Booking {booking.reference} marked as {new_status}.", "success")
    return redirect(url_for("admin.manage_bookings"))


# -------------------------------------------------------------- USERS ----

@admin_bp.route("/users")
@admin_required
def manage_users():
    search = request.args.get("q", "").strip()
    query = User.query.filter_by(role="user")
    if search:
        like = f"%{search}%"
        query = query.filter(db.or_(User.name.ilike(like), User.email.ilike(like)))
    users = query.order_by(User.created_at.desc()).all()
    return render_template("admin/users.html", users=users, search=search)


@admin_bp.route("/users/<int:user_id>/toggle", methods=["POST"])
@admin_required
def toggle_user(user_id):
    user = User.query.get_or_404(user_id)
    user.is_active = not user.is_active
    db.session.commit()
    flash(f"User {'activated' if user.is_active else 'deactivated'}.", "info")
    return redirect(url_for("admin.manage_users"))


@admin_bp.route("/users/<int:user_id>")
@admin_required
def user_details(user_id):
    user = User.query.get_or_404(user_id)
    bookings = Booking.query.filter_by(user_id=user.id).order_by(Booking.created_at.desc()).all()
    return render_template("admin/user_details.html", user=user, bookings=bookings)


# ----------------------------------------------------------- FEEDBACK ----

@admin_bp.route("/feedback")
@admin_required
def manage_feedback():
    feedback_items = Feedback.query.order_by(Feedback.created_at.desc()).all()
    return render_template("admin/feedback.html", feedback_items=feedback_items)


@admin_bp.route("/feedback/<int:feedback_id>/delete", methods=["POST"])
@admin_required
def delete_feedback(feedback_id):
    fb = Feedback.query.get_or_404(feedback_id)
    db.session.delete(fb)
    db.session.commit()
    flash("Feedback removed.", "info")
    return redirect(url_for("admin.manage_feedback"))


# ------------------------------------------------------------ REPORTS ----

@admin_bp.route("/reports")
@admin_required
def reports():
    total_revenue = (
        db.session.query(db.func.coalesce(db.func.sum(Booking.total_amount), 0))
        .filter(Booking.status.in_(["Confirmed", "Completed"]))
        .scalar()
    )
    top_tours = (
        db.session.query(Tour.name, db.func.count(Booking.id).label("count"))
        .join(Booking, Booking.tour_id == Tour.id)
        .group_by(Tour.id)
        .order_by(db.func.count(Booking.id).desc())
        .limit(5)
        .all()
    )
    bookings_by_status = (
        db.session.query(Booking.status, db.func.count(Booking.id))
        .group_by(Booking.status)
        .all()
    )
    return render_template(
        "admin/reports.html",
        total_revenue=total_revenue,
        top_tours=top_tours,
        bookings_by_status=bookings_by_status,
    )


@admin_bp.route("/bookings/<int:booking_id>/refund", methods=["POST"])
@admin_required
def update_booking_refund(booking_id):
    booking = Booking.query.get_or_404(booking_id)
    refund_status = request.form.get("refund_status", "Refunded")
    refund_amount = request.form.get("refund_amount", type=float)
    if not refund_amount or refund_amount <= 0:
        refund_amount = booking.total_amount
    reason = request.form.get("refund_reason", "").strip()
    admin_note = request.form.get("admin_refund_note", "").strip()

    booking.refund_status = refund_status
    booking.refund_amount = refund_amount
    if refund_status == "Refunded":
        booking.status = "Cancelled"

    if reason:
        booking.refund_reason = reason
    if admin_note:
        booking.admin_refund_note = admin_note
    elif refund_status == "Refunded":
        booking.admin_refund_note = f"Full refund of ${refund_amount:,.2f} approved and processed by administrator."

    if refund_status == "Refunded" and booking.user:
        points_to_deduct = int(refund_amount / 10)
        booking.user.reward_points = max(0, booking.user.reward_points - points_to_deduct)

    db.session.commit()
    flash(f"Refund of ${refund_amount:,.2f} for booking {booking.reference} has been approved & processed. User notification updated.", "success")
    return redirect(url_for("admin.manage_bookings"))


# -------------------------------------------------------- CUSTOM TRIPS ----

@admin_bp.route("/custom-trips")
@admin_required
def manage_custom_trips():
    from models import CustomTripRequest
    requests = CustomTripRequest.query.order_by(CustomTripRequest.created_at.desc()).all()
    return render_template("admin/custom_trips.html", requests=requests)


@admin_bp.route("/custom-trips/<int:req_id>/update", methods=["POST"])
@admin_required
def update_custom_trip(req_id):
    from models import CustomTripRequest
    req = CustomTripRequest.query.get_or_404(req_id)
    req.status = request.form.get("status", "Pending Review")
    req.admin_quote = request.form.get("admin_quote", type=float) or 0.0
    req.admin_notes = request.form.get("admin_notes", "").strip()
    db.session.commit()
    flash(f"Custom trip request from {req.name} updated successfully.", "success")
    return redirect(url_for("admin.manage_custom_trips"))


# ---------------------------------------------------- ASSISTANCE TICKETS ----

@admin_bp.route("/assistance")
@admin_required
def manage_assistance():
    from models import AssistanceTicket
    tickets = AssistanceTicket.query.order_by(AssistanceTicket.created_at.desc()).all()
    return render_template("admin/assistance.html", tickets=tickets)


@admin_bp.route("/assistance/<int:ticket_id>/reply", methods=["POST"])
@admin_required
def reply_assistance_ticket(ticket_id):
    from models import AssistanceTicket
    ticket = AssistanceTicket.query.get_or_404(ticket_id)
    ticket.status = request.form.get("status", "Resolved")
    ticket.admin_response = request.form.get("admin_response", "").strip()
    db.session.commit()
    flash(f"Assistance ticket #{ticket.id} updated.", "success")
    return redirect(url_for("admin.manage_assistance"))


# -------------------------------------------------------- SUBSCRIBERS ----

@admin_bp.route("/subscribers")
@admin_required
def manage_subscribers():
    from models import NewsletterSubscriber
    subscribers = NewsletterSubscriber.query.order_by(NewsletterSubscriber.subscribed_at.desc()).all()
    return render_template("admin/subscribers.html", subscribers=subscribers)


# -------------------------------------------------------- PROMOTIONS & CLONING ----

@admin_bp.route("/tours/<int:tour_id>/clone", methods=["POST"])
@admin_required
def clone_tour(tour_id):
    original = Tour.query.get_or_404(tour_id)
    cloned = Tour(
        name=f"{original.name} (Copy)",
        destination=original.destination,
        category=original.category,
        description=original.description,
        itinerary=original.itinerary,
        duration=original.duration,
        price=original.price,
        child_price=original.child_price,
        available_seats=original.available_seats,
        image_url=original.image_url,
        included=original.included,
        excluded=original.excluded,
        rating=original.rating,
        difficulty=original.difficulty,
        season=original.season,
        tags=original.tags,
        is_active=True
    )
    db.session.add(cloned)
    db.session.commit()
    flash(f"Tour package '{original.name}' successfully cloned!", "success")
    return redirect(url_for("admin.manage_tours"))


@admin_bp.route("/promotions", methods=["GET", "POST"])
@admin_required
def manage_promotions():
    from models import PromotionCampaign
    if request.method == "POST":
        title = request.form.get("title", "").strip()
        banner_text = request.form.get("banner_text", "").strip()
        discount_percent = request.form.get("discount_percent", 15.0, type=float)
        promo_code = request.form.get("promo_code", "").strip().upper()

        if title:
            promo = PromotionCampaign(
                title=title,
                banner_text=banner_text,
                discount_percent=discount_percent,
                promo_code=promo_code,
                is_active=True
            )
            db.session.add(promo)
            db.session.commit()
            flash("New promo campaign created successfully!", "success")
            return redirect(url_for("admin.manage_promotions"))

    promos = PromotionCampaign.query.order_by(PromotionCampaign.created_at.desc()).all()
    return render_template("admin/promotions.html", promos=promos)


@admin_bp.route("/analytics")
@admin_required
def analytics():
    # Category popularity calculation
    categories_data = (
        db.session.query(Tour.category, db.func.count(Booking.id))
        .join(Booking, Booking.tour_id == Tour.id)
        .group_by(Tour.category)
        .all()
    )
    labels = [c[0] for c in categories_data] or ["City Break", "Nature & Adventure", "Beach & Resort"]
    data = [c[1] for c in categories_data] or [12, 18, 9]

    return render_template("admin/analytics.html", labels=labels, data=data)


@admin_bp.route("/settings")
@admin_required
def settings():
    return render_template("admin/settings.html")
