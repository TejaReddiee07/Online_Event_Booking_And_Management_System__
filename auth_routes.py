from flask import Blueprint, render_template, request, redirect, url_for, session, flash

from extensions import mongo
from utils_security import verify_password, hash_password
from utils_email import (
    send_admin_new_admin_request_email,
    send_admin_registration_pending_email,
)

auth_bp = Blueprint('auth', __name__)


# ------------- SHARED DECORATOR -------------
def login_required(f):
    def wrap(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('auth.admin_login'))
        return f(*args, **kwargs)
    wrap.__name__ = f.__name__
    return wrap


# ------------- ADMIN AUTH -------------
@auth_bp.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        admin = mongo.db.admins.find_one({'username': username})
        if admin and verify_password(admin['password'], password):
            # allow login ONLY if approved
            if admin.get('status', 'approved') != 'approved':
                flash('Your admin account is not approved yet.', 'danger')
                return render_template('auth/admin_login.html')

            session['user_id'] = str(admin['_id'])
            session['role'] = 'admin'
            session['username'] = admin['username']  # needed for super-admin checks
            flash('Admin login successful')
            return redirect(url_for('admin.dashboard'))

        flash('Invalid admin credentials')
    return render_template('auth/admin_login.html')


@auth_bp.route('/admin/register', methods=['GET', 'POST'])
def admin_register():
    if request.method == 'POST':
        username = request.form['username']
        password = hash_password(request.form['password'])

        # if username already exists, block
        if mongo.db.admins.find_one({'username': username}):
            flash('Admin username already exists')
            return render_template('auth/admin_register.html')

        # check if there is already a main admin
        existing_admin = mongo.db.admins.find_one({})

        if not existing_admin:
            # no admin exists yet -> first admin is main admin, auto-approved
            mongo.db.admins.insert_one({
                'username': username,
                'password': password,
                'status': 'approved',
            })
            flash('First admin registered. Please login.')
            return redirect(url_for('auth.admin_login'))

        # some admin already exists -> this is a NEW admin request (pending)
        new_admin_doc = {
            'username': username,
            'password': password,
            'status': 'pending',
        }
        mongo.db.admins.insert_one(new_admin_doc)

        # email the existing main admin (assume username is email)
        if existing_admin.get('username'):
            try:
                send_admin_new_admin_request_email(
                    to_email=existing_admin['username'],
                    new_admin_username=username,
                )
            except Exception:
                # do not break flow on email failure
                pass

        # email the new admin about pending status
        try:
            send_admin_registration_pending_email(to_email=username)
        except Exception:
            pass

        flash('Admin registration sent to the main admin for approval.', 'info')
        return redirect(url_for('auth.admin_login'))

    return render_template('auth/admin_register.html')


# ------------- ORGANIZER AUTH -------------
@auth_bp.route('/organizer/login', methods=['GET', 'POST'])
def organizer_login():
    # value passed from home buttons: event / hall / food
    next_action = request.args.get('next', 'event')

    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        org = mongo.db.organizers.find_one({'email': email})
        if org and verify_password(org['password'], password):
            session['user_id'] = str(org['_id'])
            session['role'] = 'organizer'
<<<<<<< HEAD
            session['entry_mode'] = next_action  # remember how user entered
=======
            session['entry_mode'] = next_action  # NEW: remember how user entered
>>>>>>> 9526daa4a4bae6cc394d967bb21c46d365c19ec4
            flash('user login successful')

            # redirect based on what user clicked on home page
            if next_action == 'hall':
                return redirect(url_for('organizer.halls_list'))
            elif next_action == 'food':
                return redirect(url_for('organizer.food_packages'))
            else:  # 'event' or anything else
                return redirect(url_for('organizer.dashboard'))

        flash('Invalid organizer credentials')

    return render_template('auth/organizer_login.html', next=next_action)


@auth_bp.route('/organizer/register', methods=['GET', 'POST'])
def organizer_register():
    if request.method == 'POST':
        data = {
            'name': request.form['name'],
            'phone': request.form['phone'],
            'email': request.form['email'],
            'password': hash_password(request.form['password']),
            'address': request.form['address']
        }
        if mongo.db.organizers.find_one({'email': data['email']}):
            flash('user email already exists')
        else:
            mongo.db.organizers.insert_one(data)
            flash('user registered. Please login.')
            return redirect(url_for('auth.organizer_login'))
    return render_template('auth/organizer_register.html')
