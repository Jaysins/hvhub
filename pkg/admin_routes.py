from flask import render_template, redirect, flash, session, request, url_for, jsonify
from werkzeug.security import check_password_hash
from flask import current_app as app
from pkg.models import db, Farmer, Restaurant, Admin, Category, Product, Payment
from pkg.forms import AdminLoginForm, CategoryForm


# Route for admin login
@app.route('/admin/', methods=['GET', 'POST'])
def admin_login():
    admin = AdminLoginForm()
    if admin.validate_on_submit():  # This ensures the form is submitted and valid
        username = request.form.get('username')
        password = request.form.get('password')
        print(username, password)
        check_record = db.session.query(Admin).filter_by(admin_username=username).first()
        print(check_record)
        if check_record:
            hashed_password = check_record.admin_password
            if check_password_hash(hashed_password, password):
                session['admin_loggedin'] = check_record.admin_id
                return redirect(url_for('admin'))
            else:
                flash("errors", "Invalid Password")
        else:
            flash("errors", "Invalid Username", )

        return redirect(url_for('admin_login'))

    return render_template('admin/admin_login.html', admin=admin)


@app.route('/admin-dashboard/')
def admin():
    adminn_id = session.get("admin_loggedin")

    if not adminn_id:
        flash("errors", "Please log in to access the dashboard.")
        return redirect(url_for('admin_login'))

    admin = db.session.query(Admin).filter(Admin.admin_id == adminn_id).first()
    if not admin:
        flash("errors", "Invalid session. Please log in again.", )
        return redirect(url_for('admin_login'))

    admin_name = f"{admin.admin_username}"
    farmers_deets = db.session.query(Farmer).all()
    rest_deets = db.session.query(Restaurant).all()
    paydeets = db.session.query(Payment).filter(Payment.pay_status == 'paid').all()
    category = db.session.query(Category).all()
    return render_template(
        'admin/admin.html',
        admin_name=admin_name,
        farmers_deets=farmers_deets,
        rest_deets=rest_deets,
        category=category, paydeets=paydeets,
    )


@app.route('/admin/restrict/', methods=['GET', 'POST'])
def toggle_farmer_account():
    if request.method == 'POST':
        farmer_id = request.form.get('farmer_id')

        if not farmer_id:
            flash('Farmer ID is missing!', 'danger')
            return redirect(url_for('admin'))

        # Retrieve the farmer from the database
        farmer = Farmer.query.filter_by(farm_id=farmer_id).first()
        print(farmer.farmer_account)

        if farmer:
            if farmer.farmer_account == "activated":
                farmer.farmer_account = "restricted"
                flash('Account has been deactivated.', 'success')
            else:
                farmer.farmer_account = "activated"
                flash('Account has been activated.', 'success')
            db.session.commit()

            return redirect(url_for('admin'))  # Redirect to the dashboard
        else:
            flash('Farmer not found.', 'errors')
            return redirect(url_for('admin'))
    else:
        return redirect('/admin-dashboard/')


@app.route('/admin/restrict/rest/', methods=['GET', 'POST'])
def toggle_rest_account():
    if request.method == 'POST':
        rest_id = request.form.get('rest_id')
        if not rest_id:
            flash('Restaurant ID is missing!', 'danger')
            return redirect('/admin-dashboard/#restaurant')

        # Retrieve the restaurant from the database
        restaurant = Restaurant.query.filter_by(rest_id=rest_id).first()
        if restaurant:
            if restaurant.rest_account == "activated":
                restaurant.rest_account = "restricted"
                flash(f"Restaurant ID {rest_id}'s account has been restricted.", 'errors')
                redirect('/admin-dashboard/#restaurants')
            else:
                restaurant.rest_account = "activated"
                flash(f"Restaurant ID {rest_id}'s account has been activated.", 'success')
                redirect('/admin-dashboard/#restaurants')

            # Save changes
            db.session.commit()
        else:
            flash("Restaurant not found.", 'danger')

        return redirect('/admin-dashboard/#restaurants')
    else:
        return redirect('/admin-dashboard/#restaurants')


@app.route('/add-category/', methods=['POST'])
def add_category():
    category_name = request.form['category_name']
    new_category = Category(category_name=category_name)
    try:
        db.session.add(new_category)
        db.session.commit()
        flash('Category added successfully!', 'success')
        return jsonify({"success": True})
    except:
        db.session.rollback()
        flash('Error adding category.', 'danger')
        return jsonify({"success": False})



@app.route("/admin-logout/")
def admin_logout():
    session.pop('admin_loggedin', None)
    return redirect('/')
