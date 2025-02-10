from flask import render_template, redirect, flash, request, session, url_for
from werkzeug.security import generate_password_hash, check_password_hash
from flask_wtf.csrf import generate_csrf
from flask import current_app as app

from pkg.forms import Farmerlogform, Farmersignform, FarmerAddProductForm
from pkg.models import Farmer, db, Product, Category
from werkzeug.utils import secure_filename
import os
import secrets


@app.route('/signup/', methods=['GET', 'POST'])
def general_signup():
    return render_template("signup.html")


@app.route('/login/')
def login():
    return render_template('login.html')


@app.route('/farmer-signup/', methods=['GET', 'POST'])
def handle_farmer_signup():
    farmer = Farmersignform()

    print(request.method)
    if request.method == 'GET':
        return render_template('user_farmer/farmer_signup.html', farmer=farmer)
    else:
        if farmer.validate_on_submit():
            farm_name = request.form.get('farm_name')
            firstname = request.form.get('firstname')
            lastname = request.form.get('lastname')
            phone_number = request.form.get('phone_number')
            state = request.form.get('state')
            print(state)
            address = request.form.get('address')
            email = request.form.get('email')
            username = request.form.get('username')
            password = request.form.get('password')
            confirm_password = request.form.get('confirm_password')
            if password != confirm_password:
                flash('errormsg', 'Password mismatch please try again')
                return redirect('/farmer-signup/')
            else:
                hashed = generate_password_hash(password)
                push_to_db = Farmer(farm_name=farm_name,
                                    farmer_first_name=firstname,
                                    farmer_last_name=lastname,
                                    farmer_phone_number=phone_number,
                                    farmer_email=email,
                                    farmer_state_id=state,
                                    farmer_address=address,
                                    farmer_username=username,
                                    farmer_password=hashed)
                db.session.add(push_to_db)
                db.session.commit()
                flash('An account has been created for you', "feedback")
                return redirect('/farmer-login/')
    return render_template('user_farmer/farmer_signup.html', farmer=farmer)


@app.route('/farmer-login/', methods=['GET', 'POST'])
def farmer_login():
    farmer = Farmerlogform()
    if request.method == "GET":
        return render_template('user_farmer/farmer_login.html', farmer=farmer)
    else:
        if farmer.validate_on_submit():
            email = request.form.get('email')
            password = request.form.get('password')
            print(password)
            check_record = db.session.query(Farmer).filter(Farmer.farmer_email == email).first()
            print(check_record)
            if check_record:
                if check_record.farmer_account == "restricted":
                    flash('Sorry, you cannot log in. You can file a complaint at info@harvesthub.com.', 'errors')
                    return redirect('/farmer-login/')
                else:
                    hashed_password = check_record.farmer_password
                    print(hashed_password)
                    chk = check_password_hash(hashed_password, password)
                    print(chk)
                    if chk:
                        session["farmer_loggedin"] = check_record.farm_id
                        return redirect('/farmer-dashboard/')
                    else:
                        flash('Invalid Password', 'errors')
                        return redirect('/farmer-login/')
            else:
                flash('Invalid Email', 'errors')
                return redirect('/farmer-login/')

    return render_template('user_farmer/farmer_login.html', farmer=farmer)


@app.route('/farmer-dashboard/')
def farmer_dashboard():
    farmer_id = session.get("farmer_loggedin")
    if not farmer_id:
        flash('errors', 'You need to log in first!')
        return redirect('/farmer-login/')

    farmer = db.session.query(Farmer).filter(Farmer.farm_id == farmer_id).first()

    if not farmer:
        flash('errors', 'Cannot find farmer with this id!')
        return redirect('/farmer-login/')

    farmer_name = f"{farmer.farmer_first_name}"
    # Query to fetch products and join with category to get the category name
    products = db.session.query(
        Product,
        Category.category_name
    ).join(
        Category, Category.category_id == Product.pro_category_id
    ).filter(
        Product.farm_id == farmer_id
    ).all()
    return render_template(
        'user_farmer/farmer_view_products.html',
        farmer_name=farmer_name,
        products=products
    )


@app.route('/farmer-add-p/')
def farmer_add():
    farmer_id = session.get("farmer_loggedin")
    farmer = db.session.query(Farmer).filter(Farmer.farm_id == farmer_id).first()
    farmer_name = f"{farmer.farmer_first_name}"
    return render_template(
        'user_farmer/farmer_add_products.html',
        farmer_name=farmer_name
    )


@app.route('/farmer/profile/', methods=['GET'])
def farmer_show_profile():
    farmer_id = session.get('farmer_loggedin')
    if farmer_id:
        farm_deets = db.session.query(Farmer).get(farmer_id)
        csrf_token = generate_csrf()
        return render_template(
            'user_farmer/farmer_show_profile.html',
            farm_deets=farm_deets,
            csrf_token=csrf_token
        )
    else:
        flash('You must be logged in', 'errormsg')
        return redirect('/')


import secrets  # Ensure secrets module is imported


@app.route('/profile/<farm_id>/update/', methods=['GET', 'POST'])
def update_profile(farm_id):
    farmer_id = session.get('farmer_loggedin')
    print("Session loggedin value:", farmer_id)

    # Ensure the logged-in user is updating their own profile
    if not farmer_id:
        flash('You must be logged in', 'errormsg')
        return redirect("/farmer-login/")

    if str(farmer_id) != str(farm_id):
        flash("Unauthorized access.", "errormsg")
        return redirect("/farmer/profile/")

    farm_deets = db.session.query(Farmer).get(farm_id)

    if not farm_deets:
        flash("Farmer profile not found", "errormsg")
        return redirect("/farmer/profile/")

    if request.method == 'POST':
        farm_name = request.form.get("farm_name")
        farmer_phone_number = request.form.get("farmer_phone_number")
        farmer_address = request.form.get("farmer_address")
        farmer_email = request.form.get("farmer_email")

        # Retrieve file data
        file = request.files.get('farmer_image')
        allowed_ext = ['.jpg', '.jpeg', '.png', '.gif']
        filename = farm_deets.farmer_image

        if file and file.filename:
            _, ext = os.path.splitext(file.filename)
            if ext.lower() in allowed_ext:
                rand_str = secrets.token_hex(10)
                filename = f'{rand_str}{ext}'
                file_path = os.path.join("pkg/static/uploaded", filename)
                file.save(file_path)
            else:
                flash("Your cover image must be an image file", "errormsg")
                return redirect('/farmer/profile/')

        # Update the farm details
        farm_deets.farm_name = farm_name
        farm_deets.farmer_phone_number = farmer_phone_number
        farm_deets.farmer_address = farmer_address
        farm_deets.farmer_email = farmer_email
        farm_deets.farmer_image = filename

        try:
            db.session.flush()  # Ensure changes are prepared
            db.session.commit()
            flash('Profile details updated successfully', 'feedback')
        except Exception as e:
            db.session.rollback()  # Rollback in case of failure
            print("Error updating profile:", str(e))
            flash("An error occurred while updating your profile", "errormsg")

        return redirect('/farmer/profile/')

    return redirect('/farmer/profile/')


@app.route("/farmer-logout/")
def farmer_logout():
    session.pop('farmer_loggedin', None)
    return redirect('/')


@app.route('/farmer-add-product/', methods=["GET", "POST"])
def farmer_add_product():
    farmer_id = session.get("farmer_loggedin")
    if not farmer_id or not db.session.query(
            Farmer).filter(Farmer.farm_id == farmer_id).first():
        flash('You need to log in first!', 'error')
        return redirect('/farmer-login/')

    form = FarmerAddProductForm()
    form.populate_categories()

    if request.method == "GET" or not form.validate_on_submit():
        return render_template(
            'user_farmer/farmer_add_products.html',
            form=form)

    # Handle form submission
    new_product = Product(
        pro_name=form.pro_name.data,
        pro_category_id=form.pro_category_id.data,
        qua_avail=form.qua_avail.data,
        price_per_unit=form.price_per_unit.data,
        farm_id=farmer_id
    )

    if form.pro_picture.data:
        upload_folder = os.path.join(app.root_path, 'static', 'uploaded')
        filename = secure_filename(form.pro_picture.data.filename)
        file_path = os.path.join(upload_folder, filename)
        form.pro_picture.data.save(file_path)
        new_product.pro_picture = filename

    db.session.add(new_product)
    db.session.commit()

    flash('success', 'Product added successfully!')
    return redirect("/farmer-add-product/")


@app.route('/farmer-update-product/<int:pro_id>/', methods=["GET", "POST"])
def farmer_update_product(pro_id):
    product = Product.query.get_or_404(pro_id)
    categories = Category.query.all()
    if request.method == 'POST':
        # Update product details from the form
        product.pro_name = request.form['pro_name']
        product.pro_category_id = request.form['pro_category_id']
        product.qua_avail = float(request.form['qua_avail'])
        product.price_per_unit = float(request.form['price_per_unit'])
        print("about to upload picture")
        # Check for picture file upload
        if 'pro_picture' in request.files:
            file = request.files.get('pro_picture')
            allowed_ext = ['.jpg', '.jpeg', '.png', '.gif']
            filename = product.pro_picture
            if file and file.filename:
                _, ext = os.path.splitext(file.filename)
                if ext.lower() in allowed_ext:
                    rand_str = secrets.token_hex(10)
                    filename = f'{rand_str}{ext}'
                    upload_folder = os.path.join("pkg", "static", "uploaded")
                    os.makedirs(upload_folder, exist_ok=True)
                    file_path = os.path.join(upload_folder, filename)
                    file.save(file_path)
                    print('product updated successfully ')
        db.session.commit()
        flash('Product updated successfully!', 'success')
        return redirect(url_for(f'farmer_update_product', pro_id=pro_id, product=product))
    # Pass the product details and categories to the template
    return render_template('user_farmer/farmer_update_product.html', product=product, categories=categories)


@app.route('/farmer-remove-product/<int:pro_id>/', methods=["GET", "POST"])
def farmer_remove_product(pro_id):
    product = Product.query.get_or_404(pro_id)

    new_status = request.form.get('status')

    if new_status in ['published', 'unpublished']:
        product.pro_status = new_status
        db.session.commit()
        flash(f"Product status updated to {new_status.capitalize()}!", "success")
    else:
        flash("Invalid status provided.", "danger")

    return redirect(url_for('farmer_dashboard'))
