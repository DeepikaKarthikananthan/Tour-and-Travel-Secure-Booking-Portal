# Wayfarer & Co. — Travel & Tour Booking System

A full-stack Travel & Tour Booking web application built with **Flask**,
**SQLAlchemy**, and **SQLite**. This is a normal, securely-implemented
booking application intended to later serve as a base for a controlled
cybersecurity lab (vulnerabilities are NOT included by default).

## Tech Stack

- **Backend:** Python 3, Flask, SQLAlchemy
- **Database:** SQLite (`instance/travel.db`)
- **Frontend:** HTML5, CSS3, Bootstrap 5, Vanilla JavaScript, Jinja2
- **Auth:** Session-based, Werkzeug password hashing

## Project Structure

```
travel_booking/
├── app.py                 # App factory & entrypoint
├── config.py               # Configuration
├── extensions.py           # Shared SQLAlchemy instance
├── seed.py                 # Sample data generator
├── requirements.txt
├── instance/                # SQLite database lives here (auto-created)
├── models/                  # SQLAlchemy models
├── routes/                  # Flask blueprints (main, auth, tours, bookings, profile, admin)
├── templates/                # Jinja2 templates (+ templates/admin, templates/errors)
└── static/                   # CSS, JS, images
```

## Setup Instructions

1. **Create and activate a virtual environment**

   ```bash
   python -m venv venv

   # macOS / Linux
   source venv/bin/activate

   # Windows
   venv\Scripts\activate
   ```

2. **Install dependencies**

   ```bash
   pip install -r requirements.txt
   ```

3. **Seed the database** (creates `instance/travel.db` with sample data)

   ```bash
   python seed.py
   ```

4. **Run the application**

   ```bash
   python app.py
   ```

   The app will be available at **http://127.0.0.1:5000**

   Admin dashboard: **http://127.0.0.1:5000/admin**

## Sample Credentials

After running `seed.py`:

| Role  | Email                          | Password      |
|-------|---------------------------------|---------------|
| Admin | admin@travelbooking.local       | Admin@123     |
| User  | aarav.sharma@example.com        | Password123   |

(Seven more sample users are created — see `seed.py` → `USERS_DATA` — all
using the password `Password123`.)

## Features

**Customer-facing**
- Landing page with hero, search, popular destinations, featured tours, testimonials
- Browse/search/filter tour packages (destination, category, price, duration, sort)
- Tour detail pages with itinerary, inclusions/exclusions, reviews
- Registration / login / logout, "forgot password" UI stub
- User dashboard with upcoming/previous bookings & favorites
- Multi-step booking flow with live cost calculation
- Booking confirmation, booking list, booking details, cancellation
- Profile editing & password change
- Favorites (save/unsave tours)
- Feedback submission (star rating + comment)
- About & Contact pages with FAQ

**Admin panel** (`/admin`)
- Separate admin login/session
- Dashboard with KPIs and Chart.js revenue/status charts
- Manage tours: add / edit / delete / activate-deactivate
- Manage bookings: filter, search, update status
- Manage users: search, activate/deactivate, view booking history
- Manage feedback: view & delete
- Reports page (revenue, bookings by status, top tours)

## Notes on Security

This application uses normal secure coding practices out of the box:

- Passwords hashed with Werkzeug (`generate_password_hash` / `check_password_hash`)
- Session-based authentication with `login_required` / `admin_required` decorators
- Server-side validation on all forms
- Parameterized queries via SQLAlchemy ORM (no raw SQL string concatenation)
- Ownership checks on booking detail/cancel routes (a user can't view/cancel another user's booking)

No intentional vulnerabilities (SQLi, XSS, LFI/RFI, backdoors, etc.) have
been introduced. The codebase is organized so that individual components
(login, search, booking, URL parameters, file handling, database queries,
admin functionality) are easy to isolate if you want to introduce
controlled vulnerabilities for lab purposes later.

## Resetting the Database

To wipe and reseed the database at any point:

```bash
python seed.py
```

This drops all tables and recreates them with fresh sample data.
