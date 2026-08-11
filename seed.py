"""
Seed the local SQLite database with an admin account, sample users, tour
packages, bookings and feedback.

Usage:
    python seed.py
"""
import random
from datetime import date, timedelta, datetime

from app import create_app
from extensions import db
from models import User, Tour, Booking, Feedback, Favorite

random.seed(42)

TOURS_DATA = [
    dict(
        name="Romantic Paris Getaway",
        destination="Paris",
        category="City Break",
        duration="5 Days / 4 Nights",
        price=1299.0,
        child_price=799.0,
        available_seats=25,
        rating=4.8,
        description=(
            "Stroll along the Seine, marvel at the Eiffel Tower, and savor "
            "world-class cuisine on this classic Parisian escape."
        ),
        itinerary=(
            "Day 1: Arrival & Eiffel Tower evening tour\n"
            "Day 2: Louvre Museum & Seine river cruise\n"
            "Day 3: Versailles day trip\n"
            "Day 4: Montmartre & Sacre-Coeur\n"
            "Day 5: Departure"
        ),
        included="Hotel accommodation\nDaily breakfast\nAirport transfers\nGuided city tour",
        excluded="International flights\nTravel insurance\nPersonal expenses",
        image_url="https://images.unsplash.com/photo-1502602898536-47ad22581b52",
    ),
    dict(
        name="Dubai Desert & Luxury Escape",
        destination="Dubai",
        category="Luxury",
        duration="4 Days / 3 Nights",
        price=1499.0,
        child_price=999.0,
        available_seats=30,
        rating=4.7,
        description=(
            "Experience futuristic skylines, thrilling desert safaris, and "
            "opulent shopping in the heart of the UAE."
        ),
        itinerary=(
            "Day 1: Arrival & Burj Khalifa visit\n"
            "Day 2: Desert safari with BBQ dinner\n"
            "Day 3: Dubai Mall & Marina cruise\n"
            "Day 4: Departure"
        ),
        included="5-star hotel\nDaily breakfast\nDesert safari\nAirport transfers",
        excluded="International flights\nVisa fees\nOptional excursions",
        image_url="https://images.unsplash.com/photo-1512453979798-5ea266f8880c",
    ),
    dict(
        name="Bali Tropical Paradise",
        destination="Bali",
        category="Beach",
        duration="6 Days / 5 Nights",
        price=999.0,
        child_price=599.0,
        available_seats=20,
        rating=4.9,
        description=(
            "Unwind on pristine beaches, explore ancient temples, and enjoy "
            "the laid-back island vibe of Bali."
        ),
        itinerary=(
            "Day 1: Arrival in Ubud\n"
            "Day 2: Rice terraces & temple hopping\n"
            "Day 3: Seminyak beach day\n"
            "Day 4: Nusa Penida island tour\n"
            "Day 5: Spa & leisure\n"
            "Day 6: Departure"
        ),
        included="Villa accommodation\nDaily breakfast\nIsland tour\nAirport transfers",
        excluded="International flights\nTravel insurance\nAlcoholic beverages",
        image_url="https://images.unsplash.com/photo-1537996194471-e657df975ab4",
    ),
    dict(
        name="Singapore City Explorer",
        destination="Singapore",
        category="City Break",
        duration="4 Days / 3 Nights",
        price=1099.0,
        child_price=699.0,
        available_seats=28,
        rating=4.6,
        description=(
            "Discover Gardens by the Bay, Sentosa Island, and a vibrant "
            "food scene in this ultra-modern city-state."
        ),
        itinerary=(
            "Day 1: Arrival & Marina Bay Sands\n"
            "Day 2: Sentosa Island & Universal Studios\n"
            "Day 3: Gardens by the Bay & city tour\n"
            "Day 4: Departure"
        ),
        included="Hotel accommodation\nDaily breakfast\nSentosa day pass\nAirport transfers",
        excluded="International flights\nMeals not listed\nPersonal expenses",
        image_url="https://images.unsplash.com/photo-1525625293386-3f8f99389edd",
    ),
    dict(
        name="Maldives Overwater Bliss",
        destination="Maldives",
        category="Honeymoon",
        duration="5 Days / 4 Nights",
        price=2199.0,
        child_price=1499.0,
        available_seats=15,
        rating=5.0,
        description=(
            "Stay in an overwater villa surrounded by turquoise lagoons — "
            "the ultimate honeymoon and relaxation destination."
        ),
        itinerary=(
            "Day 1: Arrival & speedboat transfer to resort\n"
            "Day 2: Snorkeling excursion\n"
            "Day 3: Sunset dolphin cruise\n"
            "Day 4: Spa day\n"
            "Day 5: Departure"
        ),
        included="Overwater villa\nAll meals\nSnorkeling gear\nResort transfers",
        excluded="International flights\nAlcoholic beverages\nSpa treatments",
        image_url="https://images.unsplash.com/photo-1514282401047-d79a71a590e8",
    ),
    dict(
        name="Swiss Alps Adventure",
        destination="Switzerland",
        category="Adventure",
        duration="7 Days / 6 Nights",
        price=2499.0,
        child_price=1699.0,
        available_seats=18,
        rating=4.8,
        description=(
            "Ride scenic railways, hike alpine trails, and take in "
            "breathtaking mountain views across Switzerland."
        ),
        itinerary=(
            "Day 1: Arrival in Zurich\n"
            "Day 2: Lucerne & Mount Pilatus\n"
            "Day 3: Interlaken & Jungfraujoch\n"
            "Day 4: Zermatt & the Matterhorn\n"
            "Day 5: Lake Geneva\n"
            "Day 6: Bernese Oberland hiking\n"
            "Day 7: Departure"
        ),
        included="Hotel accommodation\nDaily breakfast\nSwiss rail pass\nGuided hikes",
        excluded="International flights\nLunch & dinner\nTravel insurance",
        image_url="https://images.unsplash.com/photo-1530122037265-a5f1f91d3b99",
    ),
    dict(
        name="Kerala Backwaters Retreat",
        destination="Kerala",
        category="Nature",
        duration="5 Days / 4 Nights",
        price=699.0,
        child_price=399.0,
        available_seats=22,
        rating=4.7,
        description=(
            "Cruise the tranquil backwaters on a houseboat and explore "
            "lush tea plantations in God's Own Country."
        ),
        itinerary=(
            "Day 1: Arrival in Kochi\n"
            "Day 2: Munnar tea gardens\n"
            "Day 3: Thekkady wildlife sanctuary\n"
            "Day 4: Alleppey houseboat cruise\n"
            "Day 5: Departure"
        ),
        included="Hotel & houseboat stay\nAll meals on houseboat\nSightseeing\nTransfers",
        excluded="Flights to Kochi\nPersonal expenses\nTips",
        image_url="https://images.unsplash.com/photo-1602216056096-3b40cc0c9944",
    ),
    dict(
        name="Royal Rajasthan Heritage Tour",
        destination="Rajasthan",
        category="Heritage",
        duration="8 Days / 7 Nights",
        price=899.0,
        child_price=549.0,
        available_seats=24,
        rating=4.6,
        description=(
            "Explore majestic forts, royal palaces, and vibrant markets "
            "across Jaipur, Udaipur, and Jodhpur."
        ),
        itinerary=(
            "Day 1: Arrival in Jaipur\n"
            "Day 2: Amber Fort & City Palace\n"
            "Day 3: Jaipur to Jodhpur\n"
            "Day 4: Mehrangarh Fort\n"
            "Day 5: Jodhpur to Udaipur\n"
            "Day 6: Lake Pichola & City Palace\n"
            "Day 7: Local markets & culture\n"
            "Day 8: Departure"
        ),
        included="Hotel accommodation\nDaily breakfast\nPrivate car & driver\nSightseeing",
        excluded="Flights\nLunch & dinner\nMonument entry fees",
        image_url="https://images.unsplash.com/photo-1477587458883-47145ed94245",
    ),
    dict(
        name="Goa Beach & Nightlife Escape",
        destination="Goa",
        category="Beach",
        duration="4 Days / 3 Nights",
        price=449.0,
        child_price=249.0,
        available_seats=35,
        rating=4.4,
        description=(
            "Sun, sand, and nightlife — Goa offers the perfect mix of "
            "relaxation and vibrant beach parties."
        ),
        itinerary=(
            "Day 1: Arrival & North Goa beaches\n"
            "Day 2: Water sports & Fort Aguada\n"
            "Day 3: South Goa & spice plantation\n"
            "Day 4: Departure"
        ),
        included="Beach resort stay\nDaily breakfast\nAirport transfers\nWater sports session",
        excluded="Flights\nAlcohol\nOptional activities",
        image_url="https://images.unsplash.com/photo-1512343879784-a960bf40e7f2",
    ),
    dict(
        name="Kashmir Valley Wonders",
        destination="Kashmir",
        category="Nature",
        duration="6 Days / 5 Nights",
        price=799.0,
        child_price=499.0,
        available_seats=20,
        rating=4.9,
        description=(
            "Glide on a shikara across Dal Lake and take in the snow-capped "
            "peaks of 'Paradise on Earth'."
        ),
        itinerary=(
            "Day 1: Arrival in Srinagar & houseboat check-in\n"
            "Day 2: Dal Lake shikara ride & Mughal Gardens\n"
            "Day 3: Gulmarg gondola ride\n"
            "Day 4: Pahalgam valley\n"
            "Day 5: Sonmarg excursion\n"
            "Day 6: Departure"
        ),
        included="Houseboat & hotel stay\nDaily breakfast\nPrivate transfers\nShikara ride",
        excluded="Flights\nGondola tickets\nLunch & dinner",
        image_url="https://images.unsplash.com/photo-1566837945700-30057527ade0",
    ),
    dict(
        name="Santorini Sunset Escape",
        destination="Santorini",
        category="Honeymoon",
        duration="5 Days / 4 Nights",
        price=1799.0,
        child_price=1199.0,
        available_seats=16,
        rating=4.9,
        description=(
            "Whitewashed villages, blue-domed churches, and unforgettable "
            "sunsets over the Aegean Sea."
        ),
        itinerary=(
            "Day 1: Arrival in Fira\n"
            "Day 2: Oia village & sunset viewing\n"
            "Day 3: Catamaran cruise\n"
            "Day 4: Wine tasting tour\n"
            "Day 5: Departure"
        ),
        included="Boutique hotel stay\nDaily breakfast\nSunset cruise\nAirport transfers",
        excluded="International flights\nLunch & dinner\nTravel insurance",
        image_url="https://images.unsplash.com/photo-1533105079780-92b9be482077",
    ),
]

USERS_DATA = [
    ("Aarav Sharma", "aarav.sharma@example.com", "+91 98765 43210"),
    ("Emily Johnson", "emily.johnson@example.com", "+1 415 555 0132"),
    ("Liam Chen", "liam.chen@example.com", "+65 8123 4567"),
    ("Fatima Al Mansoori", "fatima.almansoori@example.com", "+971 50 123 4567"),
    ("Sofia Rossi", "sofia.rossi@example.com", "+39 333 123 4567"),
    ("Noah Williams", "noah.williams@example.com", "+44 7700 900123"),
    ("Priya Nair", "priya.nair@example.com", "+91 90000 11122"),
    ("Lucas Müller", "lucas.mueller@example.com", "+41 79 123 45 67"),
]

FEEDBACK_COMMENTS = [
    "Absolutely fantastic experience, everything was well organized!",
    "Great value for money and the guide was extremely knowledgeable.",
    "Loved every moment of this trip, will definitely book again.",
    "Beautiful destination, though the schedule felt a little rushed.",
    "Our family had an amazing time, highly recommend this package.",
    "The accommodations exceeded our expectations.",
    "A wonderful blend of adventure and relaxation.",
    "Customer support was responsive throughout the trip.",
]


def run():
    app = create_app()
    with app.app_context():
        db.drop_all()
        db.create_all()

        # --- Admin account -------------------------------------------------
        admin = User(name="System Administrator", email="admin@travelbooking.local", role="admin")
        admin.set_password("Admin@123")
        db.session.add(admin)

        # --- Sample users ----------------------------------------------------
        users = []
        for name, email, phone in USERS_DATA:
            u = User(name=name, email=email, phone=phone, role="user")
            u.set_password("Password123")
            db.session.add(u)
            users.append(u)

        db.session.commit()

        # --- Tour packages -----------------------------------------------
        tours = []
        today = date.today()
        for i, data in enumerate(TOURS_DATA):
            start = today + timedelta(days=15 + i * 5)
            end = start + timedelta(days=int(data["duration"].split(" ")[0]))
            tour = Tour(
                start_date=start,
                end_date=end,
                is_active=True,
                **data,
            )
            db.session.add(tour)
            tours.append(tour)

        db.session.commit()

        # --- Sample bookings ------------------------------------------------
        statuses = ["Pending", "Confirmed", "Completed", "Cancelled"]
        for i in range(18):
            user = random.choice(users)
            tour = random.choice(tours)
            adults = random.randint(1, 3)
            children = random.randint(0, 2)
            status = random.choices(statuses, weights=[2, 3, 3, 1])[0]

            travel_date = today + timedelta(days=random.randint(-60, 90))
            total = tour.price * adults + tour.child_price * children

            booking = Booking(
                user_id=user.id,
                tour_id=tour.id,
                travel_date=travel_date,
                adults=adults,
                children=children,
                contact_number=user.phone or "+1 555 000 0000",
                special_requests=random.choice(
                    ["", "Vegetarian meals please.", "Wheelchair accessibility needed.", "Anniversary trip - late checkout requested."]
                ),
                total_amount=total,
                status=status,
                created_at=datetime.utcnow() - timedelta(days=random.randint(1, 120)),
            )
            db.session.add(booking)

        db.session.commit()

        # --- Sample feedback --------------------------------------------------
        completed_bookings = Booking.query.filter(Booking.status == "Completed").all()
        for booking in completed_bookings:
            if random.random() < 0.8:
                fb = Feedback(
                    user_id=booking.user_id,
                    tour_id=booking.tour_id,
                    booking_id=booking.id,
                    rating=random.randint(3, 5),
                    comment=random.choice(FEEDBACK_COMMENTS),
                    created_at=booking.created_at + timedelta(days=random.randint(1, 10)),
                )
                db.session.add(fb)

        # --- Sample favorites ---------------------------------------------
        for user in users:
            for tour in random.sample(tours, k=random.randint(1, 3)):
                db.session.add(Favorite(user_id=user.id, tour_id=tour.id))

        db.session.commit()

        print("Database seeded successfully!")
        print("--------------------------------------------------")
        print(f"Admin login:  admin@travelbooking.local / Admin@123")
        print(f"Sample user:  {USERS_DATA[0][1]} / Password123")
        print("--------------------------------------------------")


if __name__ == "__main__":
    run()
