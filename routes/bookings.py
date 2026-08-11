from datetime import datetime, date

from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app

from models import db, Tour, Booking, auto_sync_booking_statuses
from routes.utils import login_required, get_current_user

bookings_bp = Blueprint("bookings", __name__)


@bookings_bp.route("/book/<int:tour_id>", methods=["GET", "POST"])
@login_required
def book_tour(tour_id):
    tour = Tour.query.get_or_404(tour_id)
    user = get_current_user()

    if not tour.is_active:
        flash("This tour package is currently unavailable.", "warning")
        return redirect(url_for("tours.list_tours"))

    if request.method == "POST":
        travel_date_raw = request.form.get("travel_date", "")
        adults = request.form.get("adults", "1")
        children = request.form.get("children", "0")
        contact_number = request.form.get("contact_number", "").strip()
        special_requests = request.form.get("special_requests", "").strip()
        coupon_code = request.form.get("coupon_code", "").strip().upper()
        has_insurance = True if request.form.get("has_insurance") else False
        hotel_tier = request.form.get("hotel_tier", "Standard").strip()

        errors = []

        try:
            travel_date = datetime.strptime(travel_date_raw, "%Y-%m-%d").date()
            if travel_date < date.today():
                errors.append("Travel date cannot be in the past.")
        except ValueError:
            errors.append("Please select a valid travel date.")
            travel_date = None

        try:
            adults = int(adults)
            if adults < 1:
                errors.append("At least one adult is required.")
        except ValueError:
            errors.append("Invalid number of adults.")
            adults = 1

        try:
            children = int(children)
            if children < 0:
                errors.append("Number of children cannot be negative.")
        except ValueError:
            errors.append("Invalid number of children.")
            children = 0

        total_travelers = adults + children
        if total_travelers > tour.available_seats:
            errors.append(
                f"Only {tour.available_seats} seat(s) available for this tour."
            )

        if not contact_number:
            errors.append("Please provide a contact number.")

        if errors:
            for e in errors:
                flash(e, "danger")
            return render_template("booking.html", tour=tour, form=request.form)

        adult_cost = tour.price * adults
        child_cost = tour.child_price * children
        base_total = adult_cost + child_cost

        # Add-ons: Insurance ($39 per traveler) and Hotel Tier Surcharge
        insurance_cost = (39.0 * total_travelers) if has_insurance else 0.0
        hotel_surcharge = 150.0 if hotel_tier == "Deluxe" else (300.0 if hotel_tier == "5-Star Luxury" else 0.0)
        
        gross_total = base_total + insurance_cost + hotel_surcharge

        # Coupon Discount calculation
        discount_amount = 0.0
        if coupon_code:
            from models import Coupon
            cp = Coupon.query.filter_by(code=coupon_code, is_active=True).first()
            if cp:
                discount_amount = cp.calculate_discount(gross_total)
            else:
                coupon_code = None

        final_total = max(0.0, round(gross_total - discount_amount, 2))

        booking = Booking(
            user_id=user.id,
            tour_id=tour.id,
            travel_date=travel_date,
            adults=adults,
            children=children,
            contact_number=contact_number,
            special_requests=special_requests,
            total_amount=final_total,
            discount_amount=discount_amount,
            coupon_code=coupon_code,
            has_insurance=has_insurance,
            hotel_tier=hotel_tier,
            status="Booked",
        )
        tour.available_seats -= total_travelers

        # Award user 1 Reward Point per $10 spent
        points_earned = int(final_total / 10)
        user.reward_points += points_earned

        db.session.add(booking)
        db.session.commit()

        flash(f"Your booking has been submitted successfully! You earned {points_earned} reward points.", "success")
        return redirect(url_for("bookings.booking_confirmation", booking_id=booking.id))

    return render_template("booking.html", tour=tour, form={})


@bookings_bp.route("/booking/confirmation/<int:booking_id>")
@login_required
def booking_confirmation(booking_id):
    user = get_current_user()
    auto_sync_booking_statuses(db.session)
    booking = Booking.query.get_or_404(booking_id)
    if booking.user_id != user.id:
        flash("You do not have permission to view this booking.", "danger")
        return redirect(url_for("profile.dashboard"))
    return render_template("booking_confirmation.html", booking=booking)


@bookings_bp.route("/my-bookings")
@login_required
def my_bookings():
    user = get_current_user()
    auto_sync_booking_statuses(db.session)

    status = request.args.get("status", "").strip()
    page = request.args.get("page", 1, type=int)

    query = Booking.query.filter_by(user_id=user.id)
    if status:
        query = query.filter_by(status=status)
    query = query.order_by(Booking.created_at.desc())

    per_page = current_app.config.get("BOOKINGS_PER_PAGE", 10)
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)

    return render_template("bookings.html", bookings=pagination.items, pagination=pagination, status=status)


@bookings_bp.route("/booking/<int:booking_id>")
@login_required
def booking_details(booking_id):
    user = get_current_user()
    auto_sync_booking_statuses(db.session)

    booking = Booking.query.get_or_404(booking_id)
    if booking.user_id != user.id:
        flash("You do not have permission to view this booking.", "danger")
        return redirect(url_for("profile.dashboard"))
    return render_template("booking_details.html", booking=booking)


@bookings_bp.route("/booking/<int:booking_id>/cancel", methods=["POST"])
@login_required
def cancel_booking(booking_id):
    user = get_current_user()
    booking = Booking.query.get_or_404(booking_id)

    if booking.user_id != user.id:
        flash("You do not have permission to cancel this booking.", "danger")
        return redirect(url_for("profile.dashboard"))

    if booking.is_cancellable():
        booking.tour.available_seats += booking.total_travelers()
        booking.status = "Cancelled"
        booking.refund_amount = booking.total_amount
        booking.refund_status = "Refund Requested"
        booking.refund_reason = request.form.get("reason") or "Cancelled by customer before travel date"

        # Deduct reward points earned on this booking
        points_to_deduct = int(booking.total_amount / 10)
        user.reward_points = max(0, user.reward_points - points_to_deduct)

        db.session.commit()
        flash(f"Booking cancelled successfully. Your refund request of ${booking.refund_amount:,.2f} has been submitted to the admin team.", "info")
    else:
        flash("This booking can no longer be cancelled.", "warning")

    return redirect(url_for("bookings.booking_details", booking_id=booking.id))


@bookings_bp.route("/booking/<int:booking_id>/request-refund", methods=["POST"])
@login_required
def request_refund(booking_id):
    user = get_current_user()
    booking = Booking.query.get_or_404(booking_id)

    if booking.user_id != user.id:
        flash("You do not have permission for this booking.", "danger")
        return redirect(url_for("profile.dashboard"))

    reason = request.form.get("reason", "").strip()
    booking.refund_status = "Refund Requested"
    booking.refund_amount = booking.total_amount
    if reason:
        booking.refund_reason = reason

    db.session.commit()
    flash(f"Refund request of ${booking.total_amount:,.2f} submitted to our admin team. Status will update once processed.", "success")
    return redirect(url_for("bookings.booking_details", booking_id=booking.id))
