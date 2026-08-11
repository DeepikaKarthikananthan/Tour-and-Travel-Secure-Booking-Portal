from flask import Blueprint, jsonify, request, render_template, flash, redirect, url_for, Response, current_app
import csv
import io
from datetime import datetime

from models import db, Tour, Booking, Coupon, CustomTripRequest, NewsletterSubscriber, User
from routes.utils import get_current_user, login_required, admin_required

api_bp = Blueprint("api", __name__)

EXCHANGE_RATES = {
    "USD": 1.0,
    "EUR": 0.92,
    "GBP": 0.79,
    "INR": 83.2,
    "AUD": 1.52,
    "CAD": 1.36,
    "JPY": 155.5
}

CURRENCY_SYMBOLS = {
    "USD": "$",
    "EUR": "€",
    "GBP": "£",
    "INR": "₹",
    "AUD": "A$",
    "CAD": "C$",
    "JPY": "¥"
}


@api_bp.route("/api/currency/convert")
def convert_currency():
    """Real-time Currency Conversion API"""
    target = request.args.get("currency", "USD").upper()
    amount = request.args.get("amount", 0.0, type=float)

    rate = EXCHANGE_RATES.get(target, 1.0)
    symbol = CURRENCY_SYMBOLS.get(target, "$")
    converted = round(amount * rate, 2)

    return jsonify({
        "status": "success",
        "base": "USD",
        "target": target,
        "rate": rate,
        "symbol": symbol,
        "original_amount": amount,
        "converted_amount": converted,
        "formatted": f"{symbol}{converted:,.2f}" if target != "JPY" else f"{symbol}{int(converted):,}"
    })


# ---------------------------------------------------- DEMO ATTACK ENDPOINTS ----

@api_bp.route("/api/verify-token", methods=["POST"])
def verify_token():
    """Attack Demo 7: Timing Side-Channel Attack Comparison API"""
    import time
    from flask import session
    from routes.utils import safe_str_cmp
    
    SECRET_SERVER_TOKEN = "WAYFARER-SECRET-KEY-9988"
    provided_token = request.json.get("token", "") if request.is_json else request.form.get("token", "")
    security_mode = session.get("security_mode", "ON")

    start_time = time.perf_counter()

    if security_mode == "OFF":
        # VULNERABLE DEMO: Standard early-exit string comparison vulnerable to timing leaks
        is_valid = (provided_token == SECRET_SERVER_TOKEN)
        method_used = "Insecure Standard Equality (==) - Microsecond Timing Leak Enabled"
    else:
        # SECURED DEMO: Constant-time comparison using hmac.compare_digest
        is_valid = safe_str_cmp(provided_token, SECRET_SERVER_TOKEN)
        method_used = "Secured Constant-Time hmac.compare_digest() - Timing Side-Channel Neutralized"

    elapsed_ms = round((time.perf_counter() - start_time) * 1000, 4)

    return jsonify({
        "status": "success" if is_valid else "denied",
        "valid": is_valid,
        "security_mode": security_mode,
        "comparison_method": method_used,
        "execution_time_ms": elapsed_ms
    })


@api_bp.route("/demo/clickjacking-test")
def clickjacking_test():
    """Attack Demo 9: Clickjacking iFrame Embedding Test Page"""
    from flask import session
    security_mode = session.get("security_mode", "ON")
    return render_template("clickjacking_demo.html", security_mode=security_mode)



@api_bp.route("/api/coupon/validate", methods=["POST"])
def validate_coupon():
    """Discount Promo Coupon Code Validation Endpoint"""
    data = request.get_json() or {}
    code = (data.get("code") or request.form.get("code") or "").strip().upper()
    total = data.get("total_amount") or request.form.get("total_amount", type=float) or 0.0

    if not code:
        return jsonify({"valid": False, "message": "Please enter a coupon code."}), 400

    coupon = Coupon.query.filter_by(code=code, is_active=True).first()
    if not coupon:
        return jsonify({"valid": False, "message": "Invalid or expired promo code."}), 404

    discount = coupon.calculate_discount(total)
    final_total = max(0.0, round(total - discount, 2))

    return jsonify({
        "valid": True,
        "code": coupon.code,
        "discount_percent": coupon.discount_percent,
        "discount_amount": discount,
        "final_total": final_total,
        "message": f"Coupon '{coupon.code}' applied! You saved ${discount:,.2f}"
    })


@api_bp.route("/api/subscribe", methods=["POST"])
def subscribe_newsletter():
    """Newsletter Subscription API"""
    email = (request.form.get("email") or "").strip().lower()
    if not email or "@" not in email:
        flash("Please enter a valid email address.", "danger")
        return redirect(request.referrer or url_for("main.home"))

    existing = NewsletterSubscriber.query.filter_by(email=email).first()
    if not existing:
        sub = NewsletterSubscriber(email=email)
        db.session.add(sub)
        db.session.commit()

    flash("Thank you for subscribing! Use coupon 'WELCOME10' for 10% off your next trip.", "success")
    return redirect(request.referrer or url_for("main.home"))


@api_bp.route("/custom-trip", methods=["GET", "POST"])
def custom_trip():
    """Custom Tailor-Made Trip Request Route"""
    user = get_current_user()

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        phone = request.form.get("phone", "").strip()
        destination = request.form.get("destination", "").strip()
        budget = request.form.get("budget", "").strip()
        travelers = request.form.get("travelers", 1, type=int)
        preferred_month = request.form.get("preferred_month", "").strip()
        notes = request.form.get("notes", "").strip()

        if not name or not email or not destination:
            flash("Please fill in your name, email, and target destination.", "danger")
        else:
            req = CustomTripRequest(
                name=name,
                email=email,
                phone=phone,
                destination=destination,
                budget=budget,
                travelers=travelers,
                preferred_month=preferred_month,
                notes=notes
            )
            db.session.add(req)
            db.session.commit()
            flash("Your custom itinerary request has been received! Our travel specialists will contact you within 24 hours.", "success")
            return redirect(url_for("api.custom_trip"))

    my_requests = []
    if user:
        my_requests = CustomTripRequest.query.filter_by(email=user.email).order_by(CustomTripRequest.created_at.desc()).all()

    return render_template("custom_trip.html", user=user, my_requests=my_requests)


@api_bp.route("/tours/compare")
def compare_tours():
    """Side-by-Side Tour Package Comparison Tool"""
    tour_ids = request.args.getlist("id", type=int)
    if not tour_ids:
        # Default to first 3 tours for demo
        tours = Tour.query.filter_by(is_active=True).limit(3).all()
    else:
        tours = Tour.query.filter(Tour.id.in_(tour_ids)).all()

    all_tours = Tour.query.filter_by(is_active=True).all()
    return render_template("compare_tours.html", tours=tours, all_tours=all_tours)


@api_bp.route("/profile/passport")
@login_required
def user_passport():
    """User Digital Travel Passport & Loyalty Badges Route"""
    user = get_current_user()
    user_bookings = Booking.query.filter_by(user_id=user.id).all()
    completed_bookings = [b for b in user_bookings if b.status == "Completed"]
    
    total_spent = sum(b.total_amount for b in completed_bookings)
    destinations_visited = set(b.tour.destination for b in completed_bookings if b.tour)
    
    # Calculate badges
    badges = []
    if len(user_bookings) >= 1:
        badges.append({"title": "First Journey", "icon": "fa-plane-arrival", "desc": "Booked your first experience"})
    if len(destinations_visited) >= 3:
        badges.append({"title": "Globe Trotter", "icon": "fa-earth-americas", "desc": "Visited 3+ distinct destinations"})
    if total_spent >= 2000:
        badges.append({"title": "VIP Voyager", "icon": "fa-crown", "desc": "Spent over $2,000 on journeys"})
    if user.reward_points >= 200:
        badges.append({"title": "Points Collector", "icon": "fa-gem", "desc": "Accumulated 200+ reward points"})

    return render_template(
        "passport.html",
        user=user,
        completed_bookings=completed_bookings,
        destinations_visited=destinations_visited,
        total_spent=total_spent,
        badges=badges
    )


@api_bp.route("/booking/<int:booking_id>/invoice")
@login_required
def booking_invoice(booking_id):
    """Printable PDF / HTML Booking Invoice Receipt Route"""
    user = get_current_user()
    booking = Booking.query.get_or_404(booking_id)

    # Allow booking owner or admin to access invoice
    if booking.user_id != user.id and not user.is_admin():
        flash("You do not have permission to access this invoice.", "danger")
        return redirect(url_for("profile.dashboard"))

    return render_template("invoice.html", booking=booking)


@api_bp.route("/faq")
def faq():
    """Interactive Searchable FAQ Knowledgebase"""
    return render_template("faq.html")


@api_bp.route("/assistance", methods=["GET", "POST"])
def assistance():
    """24/7 Emergency Assistance & Ticket Submission Route"""
    user = get_current_user()
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        phone = request.form.get("phone", "").strip()
        category = request.form.get("category", "General Assistance")
        subject = request.form.get("subject", "").strip()
        message = request.form.get("message", "").strip()

        if not name or not email or not subject or not message:
            flash("Please fill in all required fields.", "danger")
        else:
            from models import AssistanceTicket
            ticket = AssistanceTicket(name=name, email=email, phone=phone, category=category, subject=subject, message=message)
            db.session.add(ticket)
            db.session.commit()
            flash(f"Your assistance request has been submitted to our 24/7 support team (Ticket #{ticket.id}).", "success")
            return redirect(url_for("api.assistance"))

    my_tickets = []
    if user:
        from models import AssistanceTicket
        my_tickets = AssistanceTicket.query.filter_by(email=user.email).order_by(AssistanceTicket.created_at.desc()).all()

    return render_template("assistance.html", user=user, my_tickets=my_tickets)


@api_bp.route("/admin/export/bookings")
@admin_required
def export_bookings_csv():
    """1-Click Admin CSV Data Export for Bookings"""
    bookings = Booking.query.order_by(Booking.created_at.desc()).all()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "Booking ID", "Reference", "Customer Name", "Customer Email",
        "Tour Name", "Destination", "Travel Date", "Travelers",
        "Total Amount ($)", "Discount ($)", "Coupon Code", "Status", "Booked At"
    ])

    for b in bookings:
        writer.writerow([
            b.id,
            b.reference,
            b.user.name if b.user else "N/A",
            b.user.email if b.user else "N/A",
            b.tour.name if b.tour else "N/A",
            b.tour.destination if b.tour else "N/A",
            b.travel_date.strftime("%Y-%m-%d") if b.travel_date else "",
            b.total_travelers(),
            f"{b.total_amount:.2f}",
            f"{b.discount_amount:.2f}",
            b.coupon_code or "None",
            b.status,
            b.created_at.strftime("%Y-%m-%d %H:%M:%S") if b.created_at else ""
        ])

    csv_data = output.getvalue()
    return Response(
        csv_data,
        mimetype="text/csv",
        headers={"Content-Disposition": f"attachment;filename=bookings_export_{datetime.now().strftime('%Y%m%d')}.csv"}
    )
