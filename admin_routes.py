import os
from bson import ObjectId
from flask import (
    Blueprint, render_template, request, redirect,
    url_for, flash, session, current_app
)
from werkzeug.utils import secure_filename

from extensions import mongo
from auth_routes import login_required
from utils_security import hash_password
from utils_email import send_booking_confirm_email, send_booking_confirm_email_with_food


admin_bp = Blueprint('admin', __name__)


@login_required
def require_admin(role):
    if session.get('role') != 'admin':
        return redirect(url_for('index'))
    return role


@admin_bp.route('/dashboard')
@login_required
def dashboard():
    organizer_count = mongo.db.organizers.count_documents({})
    halls_count = mongo.db.halls.count_documents({})
    pending_count = mongo.db.bookings.count_documents({'status': 'pending'})
    return render_template(
        'admin/dashboard.html',
        organizer_count=organizer_count,
        halls_count=halls_count,
        pending_count=pending_count,
    )


@admin_bp.route('/organizers', methods=['GET', 'POST'])
@login_required
def organizers():
    require_admin(session.get('role'))
    if request.method == 'POST':
        data = {
            'name': request.form['name'],
            'phone': request.form['phone'],
            'email': request.form['email'],
            'password': hash_password(request.form['password']),
            'address': request.form['address'],
        }
        mongo.db.organizers.insert_one(data)
        flash('Organizer added!')
    orgs = list(mongo.db.organizers.find())
    return render_template('admin/organizers.html', organizers=orgs)


@admin_bp.route('/halls', methods=['GET', 'POST'])
@login_required
def halls():
    require_admin(session.get('role'))

    if request.method == 'POST':
        title = request.form['title']
        capacity = int(request.form['capacity'])
        price_per_hour = float(request.form['price'])
        address = request.form['address']
        description = request.form['description']

        picture_file = request.files.get('picture')
        picture_url = None

        if picture_file and picture_file.filename:
            filename = secure_filename(picture_file.filename)
            upload_folder = os.path.join(
                current_app.root_path, 'static', 'uploads', 'halls'
            )
            os.makedirs(upload_folder, exist_ok=True)
            picture_path = os.path.join(upload_folder, filename)
            picture_file.save(picture_path)
            picture_url = url_for('static', filename=f'uploads/halls/{filename}')

        hall_doc = {
            "title": title,
            "capacity": capacity,
            "price": price_per_hour,
            "address": address,
            "description": description,
            "picture": picture_url,
        }
        mongo.db.halls.insert_one(hall_doc)
        flash('Hall added!')

    halls_list = list(mongo.db.halls.find())
    return render_template('admin/halls.html', halls=halls_list)


@admin_bp.route('/organizers/delete/<organizer_id>', methods=['POST'])
@login_required
def delete_organizer(organizer_id):
    require_admin(session.get('role'))
    mongo.db.organizers.delete_one({'_id': ObjectId(organizer_id)})
    flash('Organizer deleted!')
    return redirect(url_for('admin.organizers'))


@admin_bp.route('/food-packages', methods=['GET', 'POST'])
@login_required
def food_packages():
    require_admin(session.get('role'))

    if request.method == 'POST':
        name = request.form['name']
        price = float(request.form['price'])
        description = request.form['description']

        breakfast = 'breakfast' in request.form
        lunch = 'lunch' in request.form
        dinner = 'dinner' in request.form

        picture_url = None
        file = request.files.get('picture')
        if file and file.filename:
            filename = secure_filename(file.filename)
            upload_folder = os.path.join(
                current_app.root_path, 'static', 'uploads', 'food'
            )
            os.makedirs(upload_folder, exist_ok=True)
            file.save(os.path.join(upload_folder, filename))
            picture_url = url_for('static', filename=f'uploads/food/{filename}')

        data = {
            'name': name,
            'breakfast': breakfast,
            'lunch': lunch,
            'dinner': dinner,
            'price': price,
            'description': description,
            'picture': picture_url,
        }

        mongo.db.food_packages.insert_one(data)
        flash('Food package added!')

    foods = list(mongo.db.food_packages.find())
    return render_template('admin/food_packages.html', foods=foods)


@admin_bp.route('/bookings')
@login_required
def bookings():
    require_admin(session.get('role'))
    
    # Fetch all bookings
    bookings_list = list(mongo.db.bookings.find())
    
    # Enrich each booking with organizer and hall details
    for booking in bookings_list:
        # Fetch organizer
        if 'org_id' in booking:
            organizer = mongo.db.organizers.find_one({'_id': booking['org_id']})
            booking['organizer_name'] = organizer['name'] if organizer else 'N/A'
            booking['organizer_email'] = organizer.get('email', '') if organizer else ''
        else:
            booking['organizer_name'] = 'N/A'
            booking['organizer_email'] = ''
        
        # Fetch hall
        if 'hall_id' in booking:
            hall = mongo.db.halls.find_one({'_id': booking['hall_id']})
            booking['hall_name'] = hall['title'] if hall else 'N/A'
        else:
            booking['hall_name'] = 'N/A'
    
    return render_template('admin/bookings.html', bookings=bookings_list)


@admin_bp.route('/approve/<booking_id>')
@login_required
def approve(booking_id):
    require_admin(session.get('role'))

    booking = mongo.db.bookings.find_one({'_id': ObjectId(booking_id)})
    if not booking:
        flash('Booking not found.', 'danger')
        return redirect(url_for('admin.bookings'))

    # Mark hall booking as approved
    mongo.db.bookings.update_one(
        {'_id': booking['_id']},
        {'$set': {'status': 'approved'}}
    )

    # Check if there's linked food booking and approve it too
    food_booking = None
    if 'linked_food_booking' in booking and booking['linked_food_booking']:
        food_booking = mongo.db.food_bookings.find_one({'_id': booking['linked_food_booking']})
        if food_booking:
            mongo.db.food_bookings.update_one(
                {'_id': food_booking['_id']},
                {'$set': {'status': 'approved'}}
            )

    # Fetch organizer & hall info
    organizer = mongo.db.organizers.find_one({'_id': booking['org_id']})
    hall = mongo.db.halls.find_one({'_id': booking['hall_id']})

    if organizer and organizer.get('email') and hall:
        try:
            # Calculate total (hall + food if exists)
            total_amount = booking.get('total_price', 0)
            food_details = ""
            
            if food_booking:
                total_amount += food_booking.get('total_price', 0)
                food_pkg = mongo.db.food_packages.find_one({'_id': food_booking['package_id']})
                food_details = f"\nFood: {food_pkg['name']} - {food_booking['plates']} plates (₹{food_booking['total_price']})"
            
            send_booking_confirm_email_with_food(
                to_email=organizer['email'],
                hall_name=hall.get('title', 'your hall'),
                from_date=booking.get('from_date', ''),
                to_date=booking.get('to_date', ''),
                hall_price=booking.get('total_price', 0),
                food_details=food_details,
                total_amount=total_amount
            )
            flash('Booking(s) approved and organizer notified by email!', 'success')
        except Exception as e:
            flash(f'Booking approved but email failed: {str(e)}', 'warning')
    else:
        flash('Booking approved!', 'success')

    return redirect(url_for('admin.bookings'))

