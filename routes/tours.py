from flask import Blueprint, render_template, request, current_app

from models import db, Tour, Feedback
from routes.utils import get_current_user

tours_bp = Blueprint("tours", __name__)


@tours_bp.route("/tours")
def list_tours():
    query = Tour.query.filter_by(is_active=True)

    search = request.args.get("q", "").strip()
    destination = request.args.get("destination", "").strip()
    category = request.args.get("category", "").strip()
    max_price = request.args.get("max_price", "").strip()
    duration = request.args.get("duration", "").strip()
    sort = request.args.get("sort", "").strip()
    page = request.args.get("page", 1, type=int)

    if search:
        like = f"%{search}%"
        query = query.filter(
            db.or_(Tour.name.ilike(like), Tour.destination.ilike(like), Tour.description.ilike(like))
        )
    if destination:
        query = query.filter(Tour.destination == destination)
    if category:
        query = query.filter(Tour.category == category)
    if duration:
        query = query.filter(Tour.duration == duration)
    if max_price:
        try:
            query = query.filter(Tour.price <= float(max_price))
        except ValueError:
            pass

    if sort == "price_asc":
        query = query.order_by(Tour.price.asc())
    elif sort == "price_desc":
        query = query.order_by(Tour.price.desc())
    elif sort == "rating":
        query = query.order_by(Tour.rating.desc())
    else:
        query = query.order_by(Tour.created_at.desc())

    per_page = current_app.config.get("TOURS_PER_PAGE", 9)
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)

    destinations = [
        d[0] for d in db.session.query(Tour.destination).filter_by(is_active=True).distinct().all()
    ]
    categories = [
        c[0] for c in db.session.query(Tour.category).filter_by(is_active=True).distinct().all()
    ]
    durations = [d[0] for d in db.session.query(Tour.duration).distinct().all()]

    # Exclude 'page' and empty values from the filters dict passed to the template
    filters = {k: v.strip() for k, v in request.args.items() if k != "page" and v and v.strip()}

    from flask import session
    from markupsafe import Markup
    security_mode = session.get("security_mode", "ON")
    display_search = Markup(search) if (security_mode == "OFF" and search) else search

    return render_template(
        "tours.html",
        tours=pagination.items,
        pagination=pagination,
        search=display_search,
        selected_dest=destination,
        selected_cat=category,
        selected_max_price=max_price,
        selected_duration=duration,
        selected_sort=sort,
        destinations=sorted(destinations),
        categories=sorted(categories),
        durations=sorted(durations),
        filters=filters,
    )


@tours_bp.route("/tours/<int:tour_id>")
def tour_details(tour_id):
    tour = Tour.query.get_or_404(tour_id)
    reviews = (
        Feedback.query.filter_by(tour_id=tour.id).order_by(Feedback.created_at.desc()).limit(20).all()
    )

    is_favorite = False
    user = get_current_user()
    if user:
        from models import Favorite

        is_favorite = (
            Favorite.query.filter_by(user_id=user.id, tour_id=tour.id).first() is not None
        )

    related = (
        Tour.query.filter(Tour.destination == tour.destination, Tour.id != tour.id, Tour.is_active.is_(True))
        .limit(3)
        .all()
    )

    return render_template(
        "tour_details.html", tour=tour, reviews=reviews, is_favorite=is_favorite, related=related
    )
