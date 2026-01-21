from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from bson import ObjectId
from extensions import mongo
from auth_routes import login_required
from utils_email import (
    send_booking_auto_rejected_unavailable_email,  # if you use this elsewhere
    send_admin_new_booking_email,
)
from config import Config


organizer_bp = Blueprint('organizer', __name__)


def require_organizer(role):
    if session.get('role') != 'organizer':
        return redirect(url_for('index'))
    return role


# ---------------- DASHBOARD ----------------
@organizer_bp.route('/dashboard')
@login_required
def dashboard():
    require_organizer(session.get('role'))

    org_id = ObjectId(session['user_id'])
    total_bookings = mongo.db.bookings.count_documents({'org_id': org_id})

    return render_template(
        'organizer/dashboard.html',
        total_bookings=total_bookings
    )


# ---------------- HALLS LIST ----------------
@organizer_bp.route('/halls')
@login_required
def halls_list():
    require_organizer(session.get('role'))

    selected_location = request.args.get('location', 'all')

    if selected_location == 'all':
        halls = list(mongo.db.halls.find({}))
    else:
        halls = list(mongo.db.halls.find({'location': selected_location}))

    all_locations = mongo.db.halls.distinct('location')

    return render_template(
        'organizer/halls.html',
        halls=halls,
        locations=all_locations,
        selected_location=selected_location
    )


# ---------------- BOOK HALL ----------------
@organizer_bp.route('/book-hall/<string:hall_id>', methods=['GET', 'POST'])
@login_required
def book_hall(hall_id):
    require_organizer(session.get('role'))

    hall = mongo.db.halls.find_one({'_id': ObjectId(hall_id)})
    if not hall:
        flash('Hall not found.', 'danger')
        return redirect(url_for('organizer.halls_list'))

    if request.method == 'POST':
        from_date = request.form['from_date']
        to_date = request.form['to_date']

        # auto‑reject if same hall already booked for overlapping dates
        conflict = mongo.db.bookings.find_one({
            'hall_id': hall['_id'],
            'status': {'$ne': 'rejected'},  # approved or pending block new booking
            '$or': [{
                'from_date': {'$lte': to_date},
                'to_date': {'$gte': from_date},
            }],
        })

        if conflict:
            flash('This hall is already booked for the selected dates. Please choose another date or hall.', 'danger')
            return redirect(url_for('organizer.halls_list'))

        data = {
            'org_id': ObjectId(session['user_id']),
            'hall_id': hall['_id'],
            'from_date': from_date,
            'to_date': to_date,
            'num_people': int(request.form['num_people']),
            'event_name': request.form['event_name'],
            'description': request.form.get('description', ''),
            'food_required': request.form.get('food_required') == 'yes',
            'status': 'pending',
            'total_hours': float(request.form.get('total_hours', 0) or 0),
            'total_price': float(request.form.get('total_price', 0) or 0),
            'booking_type': 'hall',  # mark as hall booking
        }
        booking_id = mongo.db.bookings.insert_one(data).inserted_id

        # notify admin about new hall booking
        org_id = data['org_id']
        user_doc = mongo.db.organizers.find_one({'_id': org_id})
        admin_email = getattr(Config, 'ADMIN_EMAIL', None) or Config.MAIL_FROM
        if admin_email and user_doc:
            extra = f"People: {data['num_people']}, Total: ₹{data['total_price']}"
            send_admin_new_booking_email(
                to_email=admin_email,
                organizer_name=user_doc.get('name', 'User'),
                booking_kind="Hall",
                hall_or_package=hall.get('title', 'Hall'),
                from_date=data['from_date'],
                to_date=data['to_date'],
                extra_info=extra,
            )

        # Decide where to go next based on how user entered (event / hall / food)
        entry_mode = session.get('entry_mode', 'event')

        if entry_mode == 'event':
            # Full event flow: hall then food
            session['hall_booking_id'] = str(booking_id)
            flash('Hall booking submitted! Now select food package.', 'success')
            return redirect(url_for('organizer.food_packages'))
        else:
            # Book Hall only: do not redirect to food
            flash('Hall booking submitted!', 'success')
            return redirect(url_for('organizer.bookings'))

    return render_template('organizer/book_hall.html', hall=hall)


# ---------------- FOOD PACKAGES LIST ----------------
@organizer_bp.route('/food-packages')
@login_required
def food_packages():
    require_organizer(session.get('role'))

    packages = list(mongo.db.food_packages.find({}))
    return render_template('organizer/food_packages.html', packages=packages)


# ---------- BOOK FOOD PACKAGE ----------
@organizer_bp.route('/book-food/<string:package_id>', methods=['GET', 'POST'])
@login_required
def book_food(package_id):
    require_organizer(session.get('role'))

    pkg = mongo.db.food_packages.find_one({'_id': ObjectId(package_id)})
    if not pkg:
        flash('Food package not found.', 'danger')
        return redirect(url_for('organizer.food_packages'))

    if request.method == 'POST':
        plates = int(request.form.get('plates') or 0)
        total_price = float(request.form.get('total_price') or 0)

        # read from/to dates from form
        from_date = request.form.get('from_date')
        to_date = request.form.get('to_date')

        food_booking_data = {
            'org_id': ObjectId(session['user_id']),
            'package_id': pkg['_id'],
            'plates': plates,
            'total_price': total_price,
            'status': 'pending',
            'booking_type': 'food',  # mark as food booking
            'from_date': from_date,
            'to_date': to_date,
        }

        # Link to hall booking if exists
        if 'hall_booking_id' in session:
            food_booking_data['linked_hall_booking'] = ObjectId(session['hall_booking_id'])
            # placeholder link on hall side; will be updated after insert
            mongo.db.bookings.update_one(
                {'_id': ObjectId(session['hall_booking_id'])},
                {'$set': {'linked_food_booking': None}}
            )

        food_id = mongo.db.food_bookings.insert_one(food_booking_data).inserted_id

        # Update hall booking with food link
        if 'hall_booking_id' in session:
            mongo.db.bookings.update_one(
                {'_id': ObjectId(session['hall_booking_id'])},
                {'$set': {'linked_food_booking': food_id}}
            )
            session.pop('hall_booking_id')  # Clear session

        # notify admin about new food booking
        org_id = food_booking_data['org_id']
        user_doc = mongo.db.organizers.find_one({'_id': org_id})
        admin_email = getattr(Config, 'ADMIN_EMAIL', None) or Config.MAIL_FROM
        if admin_email and user_doc:
            extra = f"Plates: {plates}, Total: ₹{total_price}"
            send_admin_new_booking_email(
                to_email=admin_email,
                organizer_name=user_doc.get('name', 'User'),
                booking_kind="Food",
                hall_or_package=pkg.get('name', 'Food Package'),
                from_date=from_date or '-',
                to_date=to_date or '-',
                extra_info=extra,
            )

        flash('Food package booking submitted! Await admin approval.', 'success')
        return redirect(url_for('organizer.bookings'))

    return render_template('organizer/book_food.html', package=pkg)


# ---------------- BOOKINGS LIST ----------------
@organizer_bp.route('/bookings')
@login_required
def bookings():
    require_organizer(session.get('role'))

    org_id = ObjectId(session['user_id'])

    # Hall (and hall+food) bookings for this organizer
    org_bookings = list(mongo.db.bookings.find({'org_id': org_id}))

    # Preload halls for names
    hall_ids = [b['hall_id'] for b in org_bookings if 'hall_id' in b]
    halls = {
        h['_id']: h
        for h in mongo.db.halls.find({'_id': {'$in': hall_ids}})
    }

    # Enrich hall bookings with hall name and food info
    for b in org_bookings:
        hall = halls.get(b.get('hall_id'))
        b['hall_name'] = hall['title'] if hall else 'N/A'

        if b.get('linked_food_booking'):
            b['combined_type'] = 'Hall + Food'
            food_booking = mongo.db.food_bookings.find_one(
                {'_id': b['linked_food_booking']}
            )
            if food_booking:
                b['food_plates'] = food_booking.get('plates', 0)
                b['food_total'] = food_booking.get('total_price', 0)
            else:
                b['food_plates'] = None
                b['food_total'] = None
        else:
            b['combined_type'] = 'Hall Only'
            b['food_plates'] = None
            b['food_total'] = None

    # Also include FOOD-ONLY bookings for this organizer
    food_only = list(mongo.db.food_bookings.find({
        'org_id': org_id,
        'booking_type': 'food',
        '$or': [
            {'linked_hall_booking': {'$exists': False}},
            {'linked_hall_booking': None},
        ],
    }))

    for f in food_only:
        pkg = mongo.db.food_packages.find_one({'_id': f['package_id']})
        f['event_name'] = pkg['name'] if pkg else 'Food Package'
        f['hall_name'] = '-'  # no hall

        # use stored from_date / to_date from food booking
        f['from_date'] = f.get('from_date', '-')
        f['to_date'] = f.get('to_date', '-')

        f['num_people'] = '-'  # not applicable
        f['combined_type'] = 'Food Only'
        f['food_plates'] = f.get('plates', 0)
        f['food_total'] = f.get('total_price', 0)

    # merge both lists (hall-based and food-only)
    all_bookings = org_bookings + food_only

    return render_template(
        'organizer/bookings.html',
        bookings=all_bookings,
        halls=halls
    )


# ---------------- PAYMENT PAGE ----------------
@organizer_bp.route('/payment/<string:booking_id>')
@login_required
def payment(booking_id):
    require_organizer(session.get('role'))

    # Get hall booking
    booking = mongo.db.bookings.find_one({'_id': ObjectId(booking_id)})
    if not booking:
        flash('Booking not found.', 'danger')
        return redirect(url_for('organizer.bookings'))

    # Check if this organizer owns this booking
    if str(booking['org_id']) != session['user_id']:
        flash('Unauthorized access.', 'danger')
        return redirect(url_for('organizer.bookings'))

    # Get hall details
    hall = mongo.db.halls.find_one({'_id': booking['hall_id']})

    # Calculate total (hall + food if linked)
    total_amount = booking.get('total_price', 0)
    food_details = None

    if 'linked_food_booking' in booking and booking['linked_food_booking']:
        food_booking = mongo.db.food_bookings.find_one({'_id': booking['linked_food_booking']})
        if food_booking:
            total_amount += food_booking.get('total_price', 0)
            food_pkg = mongo.db.food_packages.find_one({'_id': food_booking['package_id']})
            food_details = {
                'name': food_pkg['name'] if food_pkg else 'N/A',
                'plates': food_booking['plates'],
                'price': food_booking['total_price']
            }

    return render_template(
        'organizer/payment.html',
        booking=booking,
        hall=hall,
        food_details=food_details,
        total_amount=total_amount
    )
