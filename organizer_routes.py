from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from bson import ObjectId
from extensions import mongo
from auth_routes import login_required

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

    return render_template('organizer/dashboard.html',
                           total_bookings=total_bookings)




# ---------------- HALLS LIST ----------------

@organizer_bp.route('/halls')
@login_required
def halls_list():
    require_organizer(session.get('role'))

    halls = list(mongo.db.halls.find({}))
    return render_template('organizer/halls.html', halls=halls)


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
        data = {
            'org_id': ObjectId(session['user_id']),
            'hall_id': hall['_id'],
            'from_date': request.form['from_date'],
            'to_date': request.form['to_date'],
            'num_people': int(request.form['num_people']),
            'event_name': request.form['event_name'],
            'description': request.form.get('description', ''),
            'food_required': request.form.get('food_required') == 'yes',
            'status': 'pending',
            'total_hours': float(request.form.get('total_hours', 0) or 0),
            'total_price': float(request.form.get('total_price', 0) or 0),
            'booking_type': 'hall'  # NEW: mark as hall booking
        }
        booking_id = mongo.db.bookings.insert_one(data).inserted_id
        
        # NEW: Save booking_id in session and redirect to food
        session['hall_booking_id'] = str(booking_id)
        flash('Hall booking submitted! Now select food package.', 'success')
        return redirect(url_for('organizer.food_packages'))  # Changed redirect

    return render_template('organizer/book_hall.html', hall=hall)




# ---------------- FOOD PACKAGES LIST ----------------

# ---------- FOOD PACKAGES LIST (organizer) ----------

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

        food_booking_data = {
            'org_id': ObjectId(session['user_id']),
            'package_id': pkg['_id'],
            'plates': plates,
            'total_price': total_price,
            'status': 'pending',
            'booking_type': 'food'  # NEW: mark as food booking
        }
        
        # NEW: Link to hall booking if exists
        if 'hall_booking_id' in session:
            food_booking_data['linked_hall_booking'] = ObjectId(session['hall_booking_id'])
            # Also update hall booking to link back
            mongo.db.bookings.update_one(
                {'_id': ObjectId(session['hall_booking_id'])},
                {'$set': {'linked_food_booking': None}}  # Will update after insert
            )
        
        food_id = mongo.db.food_bookings.insert_one(food_booking_data).inserted_id
        
        # Update hall booking with food link
        if 'hall_booking_id' in session:
            mongo.db.bookings.update_one(
                {'_id': ObjectId(session['hall_booking_id'])},
                {'$set': {'linked_food_booking': food_id}}
            )
            session.pop('hall_booking_id')  # Clear session
        
        flash('Food package booking submitted! Await admin approval.', 'success')
        return redirect(url_for('organizer.bookings'))

    return render_template('organizer/book_food.html', package=pkg)




# ---------------- BOOKINGS LIST ----------------

@organizer_bp.route('/bookings')
@login_required
def bookings():
    require_organizer(session.get('role'))

    org_id = ObjectId(session['user_id'])
    org_bookings = list(mongo.db.bookings.find({'org_id': org_id}))

    hall_ids = [b['hall_id'] for b in org_bookings]
    halls = {
        h['_id']: h
        for h in mongo.db.halls.find({'_id': {'$in': hall_ids}})
    }

    return render_template(
        'organizer/bookings.html',
        bookings=org_bookings,
        halls=halls
    )

@organizer_bp.route('/payment')
def payment():
    return render_template('payment.html')

