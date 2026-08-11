from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify
from datetime import datetime

from models import db, Tour, Booking, User, Favorite
from routes.utils import get_current_user, login_required, admin_required

tools_bp = Blueprint("tools", __name__)


@tools_bp.route("/vacation-quiz", methods=["GET", "POST"])
def vacation_quiz():
    """Interactive Vacation Recommendation Quiz"""
    matched_tours = []
    if request.method == "POST":
        vibe = request.form.get("vibe", "City Break")
        budget = request.form.get("budget", "medium")
        season = request.form.get("season", "All Year")
        difficulty = request.form.get("difficulty", "Easy")

        query = Tour.query.filter_by(is_active=True)

        if vibe:
            query = query.filter(Tour.category.ilike(f"%{vibe}%"))
        
        all_tours = query.all()
        if not all_tours:
            all_tours = Tour.query.filter_by(is_active=True).all()

        # Score tours based on matching parameters
        scored = []
        for tour in all_tours:
            score = 70  # Base match score
            if tour.category.lower() in vibe.lower():
                score += 15
            if budget == "low" and tour.price < 1500:
                score += 10
            elif budget == "high" and tour.price >= 3000:
                score += 10
            if tour.difficulty and tour.difficulty.lower() == difficulty.lower():
                score += 5
            scored.append({"tour": tour, "match_score": min(99, score)})

        scored.sort(key=lambda x: x["match_score"], reverse=True)
        matched_tours = scored[:3]

    return render_template("vacation_quiz.html", matched_tours=matched_tours)


@tools_bp.route("/tools/expense-calculator")
def expense_calculator():
    """Interactive Trip Expense Splitter & Budget Planner"""
    tours = Tour.query.filter_by(is_active=True).all()
    return render_template("expense_calculator.html", tours=tours)


@tools_bp.route("/tools/packing-checklist", methods=["GET", "POST"])
def packing_checklist():
    """Destination Weather & Smart Packing Checklist Generator"""
    checklist = []
    selected_category = request.args.get("category", "City Break")

    if selected_category == "Beach & Resort":
        checklist = [
            {"item": "High SPF Sunscreen & After-sun lotion", "cat": "Essentials"},
            {"item": "Swimwear & UV Rashguards", "cat": "Clothing"},
            {"item": "Polarized Sunglasses & Wide-brim Hat", "cat": "Accessories"},
            {"item": "Waterproof Phone Pouch", "cat": "Electronics"},
            {"item": "Beach Towel & Flip-flops", "cat": "Footwear"}
        ]
    elif selected_category in ["Mountain Trek", "Nature & Adventure"]:
        checklist = [
            {"item": "Sturdy Ankle-Support Hiking Boots", "cat": "Footwear"},
            {"item": "Breathable Moisture-Wicking Base Layers", "cat": "Clothing"},
            {"item": "Waterproof Windbreaker Jacket", "cat": "Clothing"},
            {"item": "Trekking Poles & Hydration Bladder", "cat": "Gear"},
            {"item": "First Aid Kit & Emergency Thermal Blanket", "cat": "Safety"}
        ]
    else: # City Break / Cultural
        checklist = [
            {"item": "Comfortable Walking Sneakers", "cat": "Footwear"},
            {"item": "Universal Power Adapter & Power Bank", "cat": "Electronics"},
            {"item": "Cross-body Anti-theft Daypack", "cat": "Bags"},
            {"item": "Versatile Casual Outfits", "cat": "Clothing"},
            {"item": "Travel Passport & Digital Copies", "cat": "Documents"}
        ]

    return render_template("packing_checklist.html", checklist=checklist, selected_category=selected_category)


@tools_bp.route("/safety-advisories")
def safety_advisories():
    """Global Travel Health & Safety Guidelines"""
    return render_template("safety_advisories.html")


@tools_bp.route("/booking/<int:booking_id>/eticket")
@login_required
def booking_eticket(booking_id):
    """Digital Boarding Pass & E-Ticket Generator"""
    user = get_current_user()
    booking = Booking.query.get_or_404(booking_id)

    if booking.user_id != user.id and not user.is_admin():
        flash("Unauthorized access to e-ticket.", "danger")
        return redirect(url_for("profile.dashboard"))

    return render_template("eticket.html", booking=booking)


@tools_bp.route("/profile/referral")
@login_required
def referral_program():
    """User Referral Program & Reward Points Claim"""
    user = get_current_user()
    if not user.referral_code:
        user.referral_code = f"WAYFARER-{user.id:04d}"
        db.session.commit()

    return render_template("referral.html", user=user)
