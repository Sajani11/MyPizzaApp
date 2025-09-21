from flask import Flask, render_template,session,request,flash,redirect,url_for , jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from flask_mysqldb import MySQL
from flask_apscheduler import APScheduler
from datetime import datetime, timedelta, date
from PIL import Image
import random
from decimal import Decimal
from email_validator import validate_email, EmailNotValidError

from config import Config ,ConfigScheduler

import os
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config.from_object(Config)


UPLOAD_FOLDER = 'static/images'
ALLOWED_EXTENSIONS = {'jpg', 'jpeg'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def allowed_file(file_storage):
    filename = file_storage.filename
    if '.' in filename:
        ext = filename.rsplit('.', 1)[1].lower()
        if ext in ALLOWED_EXTENSIONS:
            try:
                image = Image.open(file_storage.stream)
                image.verify()
                return True
            except Exception:
                return False
    return False

mysql = MySQL(app)

app.config.from_object(ConfigScheduler)
scheduler = APScheduler()
scheduler.init_app(app)
scheduler.start()
import MySQLdb

@app.route('/')
def home():
    cursor = mysql.connection.cursor()
    cursor.execute("SELECT * FROM pizzas")
    pizzas = cursor.fetchall()
    return render_template('home.html', pizzas=pizzas)


@app.route('/register', methods=['GET','POST'])
def register():
    if request.method == 'POST':
        name = request.form['username']
        email = request.form['email']
        password = request.form['password']

        try:
            # Validate email format & domain
            validate_email(email)
        except EmailNotValidError as e:
            flash(str(e), "danger")
            return redirect(url_for('register'))

        password = generate_password_hash(password)
        cursor = mysql.connection.cursor()

        cursor.execute("SELECT id FROM users WHERE email=%s", (email,))
        if cursor.fetchone():
            flash("Email already registered.", "danger")
            return redirect(url_for('register'))

        cursor.execute(
            "INSERT INTO users (username, email, password, role) VALUES (%s, %s, %s, 'customer')",
            (name, email, password)
        )
        mysql.connection.commit()
        cursor.close()

        flash("Registration successful! Please login.", "success")
        return redirect(url_for("login"))

    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email_or_username = request.form['email']  # input can be email or username
        password = request.form['password']

        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

        # Login using the users table only
        cursor.execute(
            "SELECT * FROM users WHERE email=%s OR username=%s",
            (email_or_username, email_or_username)
        )
        user = cursor.fetchone()

        if user and check_password_hash(user['password'], password):
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['role'] = user['role']  # 'admin' or 'customer'
            flash(f"Welcome to our pizza shop, {user['username']}! Have a great day 🎉", "success")
            
            if user['role'] == 'admin':
                return redirect(url_for('admin_dashboard'))
            return redirect(url_for('home'))

        flash("Invalid credentials. Please try again.", "danger")
   
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    flash('You have been logged out. Visit again!','info')
    return redirect(url_for('home'))

@app.route('/add_pizza', methods=['GET', 'POST'])
def add_pizza():
    if request.method == 'POST':
        name = request.form['pizza_name'].strip()
        description = request.form['description'].strip()
        price = request.form['price'].strip()
        image_source = request.form['image_source']  # 'url' or 'upload'

        if not name or not description or not price:
            flash('Please fill all fields.', 'warning')
            return redirect(url_for('add_pizza'))

        try:
            price = float(price)
        except ValueError:
            flash('Invalid price format.', 'danger')
            return redirect(url_for('add_pizza'))

        cursor = mysql.connection.cursor()

        # Check if pizza with the same name already exists
        cursor.execute("SELECT id FROM pizzas WHERE name=%s", (name,))
        if cursor.fetchone():
            flash(f'A pizza named "{name}" already exists!', 'danger')
            return redirect(url_for('add_pizza'))

        image_url = ''
        if image_source == 'url':
            image_url = request.form.get('image_url', '').strip()
        elif image_source == 'upload':
            image_file = request.files.get('image_file')
            if image_file and allowed_file(image_file):
                filename = secure_filename(image_file.filename)
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                image_file.save(file_path)
                image_url = '/' + file_path.replace("\\", "/")
            else:
                flash('Invalid image file. Please upload a valid .jpg or .jpeg file.', 'danger')
                return redirect(url_for('add_pizza'))

        cursor.execute(
            'INSERT INTO pizzas (name, description, price, image_url) VALUES (%s, %s, %s, %s)',
            (name, description, price, image_url)
        )
        mysql.connection.commit()
        cursor.close()

        flash('Pizza added successfully!', 'success')
        return redirect(url_for('add_pizza'))

    return render_template('add_pizza.html')

@app.route('/delete-pizza/<int:pizza_id>', methods=['POST'])
def delete_pizza(pizza_id):
   

    cursor = mysql.connection.cursor()
    # Delete pizza (also deletes from cart if foreign key ON DELETE CASCADE is set)
    cursor.execute("DELETE FROM pizzas WHERE id = %s", (pizza_id,))
    mysql.connection.commit()

    flash("Pizza deleted successfully!", "success")
    return redirect(url_for('home'))

@app.route('/edit-pizza/<int:pizza_id>', methods=['POST'])
def edit_pizza(pizza_id):
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

    # Get data from form
    name = request.form['name'].strip()
    price = request.form['price'].strip()
    description = request.form['description'].strip()

    
    try:
        price = float(price)
    except ValueError:
        flash('Invalid price format.', 'danger')
        return redirect(url_for('home'))  # Redirect back to home if invalid

    cursor.execute(
        "UPDATE pizzas SET name=%s, price=%s, description=%s WHERE id=%s",
        (name, price, description, pizza_id)
    )
    mysql.connection.commit()
    cursor.close()

    flash("Pizza updated successfully!", "success")
    return redirect(url_for('home'))

@app.route('/admin/reports')
def admin_reports():
    if 'user_id' not in session or session.get('role') != 'admin':
        flash("Admin access required.", "danger")
        return redirect(url_for('login'))

    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

    # Revenue by date
    cursor.execute("""
        SELECT DATE(created_at) as order_date, 
               SUM(total_price) as revenue
        FROM orders
        WHERE payment_status = 'paid'
        GROUP BY DATE(created_at)
        ORDER BY order_date DESC
        LIMIT 10
    """)
    sales_by_date = cursor.fetchall()

    # Orders by status
    cursor.execute("""
        SELECT status, COUNT(*) as count
        FROM orders
        GROUP BY status
    """)
    sales_by_status = cursor.fetchall()

    # Top pizzas (by quantity sold)
    cursor.execute("""
        SELECT p.name, SUM(o.quantity) as total_sold
        FROM orders o
        JOIN pizzas p ON o.pizza_id = p.id
        WHERE o.status != 'cancelled'
        GROUP BY p.id
        ORDER BY total_sold DESC
        LIMIT 5
    """)
    top_pizzas = cursor.fetchall()

    cursor.close()

    return render_template(
        'admin_reports.html',
        sales_by_date=sales_by_date,
        sales_by_status=sales_by_status,
        top_pizzas=top_pizzas
    )

@app.route('/choose-auth')
def choose_auth():
    return render_template('choose_auth.html')

@app.route('/order/<int:pizza_id>', methods=['GET','POST'])
def order_pizza(pizza_id):
    if 'user_id' not in session:
        flash('Login first', 'warning')
        return redirect(url_for('login'))

    cursor = mysql.connection.cursor()
    cursor.execute("SELECT * FROM pizzas WHERE id=%s", (pizza_id,))
    pizza = cursor.fetchone()
    if not pizza:
        flash('Pizza not found', 'danger')
        return redirect(url_for('home'))

    if request.method == 'POST':
        size = request.form.get('size', 'small')
        crust = request.form.get('crust', 'thin')
        cheese = request.form.get('cheese', 'normal')
        toppings = ','.join(request.form.getlist('toppings')) or None
        extras = request.form.get('extras') or None
        quantity = int(request.form.get('quantity', 1))

        # Calculate unit_price
        unit_price = float(pizza['price'])
        if size == 'medium':
            unit_price += 100
        elif size == 'large':
            unit_price += 200
        if cheese == 'extra':
            unit_price += 50

        # Insert into cart (with customizations)
        cursor.execute("""
            INSERT INTO cart(user_id, pizza_id, size, crust, cheese, toppings, extras, quantity, unit_price)
            VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s)
            ON DUPLICATE KEY UPDATE quantity=quantity+VALUES(quantity)
        """, (session['user_id'], pizza_id, size, crust, cheese, toppings, extras, quantity, unit_price))

        mysql.connection.commit()
        flash('Added to cart', 'success')
        return redirect(url_for('view_cart'))

    return render_template('customization.html', pizza=pizza)

#place all the pizza 
@app.route('/place-order', methods=['GET', 'POST'])
def place_order():
    if 'user_id' not in session:
        flash("Login first", "danger")
        return redirect(url_for('login'))

    user_id = session['user_id']
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

    # Get cart items
    cursor.execute("""
        SELECT c.*, p.name, (c.unit_price * c.quantity) AS subtotal
        FROM cart c
        JOIN pizzas p ON c.pizza_id = p.id
        WHERE c.user_id = %s
    """, (user_id,))
    cart_items = cursor.fetchall()

    if not cart_items:
        flash("No items in cart to place order.", "warning")
        return redirect(url_for('view_cart'))

    # Calculate subtotal
    subtotal = sum(item['subtotal'] for item in cart_items)

    # Base delivery fee
    BASE_DELIVERY_FEE = 50
    delivery_fee = BASE_DELIVERY_FEE

    # Check spin reward
    today = date.today()
    cursor.execute("""
        SELECT reward FROM spin_rewards
        WHERE user_id = %s AND DATE(created_at) = %s
        ORDER BY created_at DESC LIMIT 1
    """, (user_id, today))
    reward_row = cursor.fetchone()
    reward = reward_row['reward'] if reward_row else None

    # Apply reward
    total_price = subtotal 
    if reward == "10% Off":
        total_price *= Decimal('0.9')
    elif reward == "Buy 1 Get 1":
        total_price *= Decimal('0.5')
    if reward == "Free Delivery":
        delivery_fee = 0
    total_price_with_fee = total_price + delivery_fee

    if request.method == 'POST':
        contact_number = request.form.get('contact_number')
        address = request.form.get('address')
        payment_method = request.form.get('payment_method')

        if not contact_number or not address or not payment_method:
            flash("Please fill contact number, address and payment method.", "warning")
            return redirect(url_for('place_order'))

        # Insert order (master row)
        cursor.execute("""
            INSERT INTO orders (
                user_id, total_price, delivery_fee, contact_number, address,
                status, payment_method, payment_status, reward, created_at
            ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,NOW())
        """, (
            user_id, total_price_with_fee, delivery_fee, contact_number, address,
            'pending', payment_method, 'paid' if payment_method != 'cod' else 'unpaid', reward
        ))
        order_id = cursor.lastrowid

        # Insert each pizza into order_items
        for item in cart_items:
            cursor.execute("""
                INSERT INTO order_items (
                    order_id, pizza_id, size, crust, cheese, toppings, extras, quantity, price
                ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
            """, (
                order_id,
                item['pizza_id'],
                item['size'],
                item['crust'],
                item['cheese'],
                item['toppings'],
                item['extras'],
                item['quantity'],
                item['subtotal']
            ))

        # Clear cart
        cursor.execute("DELETE FROM cart WHERE user_id = %s", (user_id,))
        mysql.connection.commit()
        flash("Order placed successfully! 🎉", "success")
        return redirect(url_for('orders'))

    return render_template(
        'order.html',
        cart_items=cart_items,
        total_price=total_price_with_fee,
        delivery_fee=delivery_fee,
        reward=reward
    )

    if 'user_id' not in session:
        flash("Login first", "danger")
        return redirect(url_for('login'))

    user_id = session['user_id']
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

    cursor.execute("""
        SELECT c.*, p.name, (c.unit_price * c.quantity) AS subtotal
        FROM cart c
        JOIN pizzas p ON c.pizza_id = p.id
        WHERE c.id = %s AND c.user_id = %s
    """, (cart_id, user_id))
    item = cursor.fetchone()

    if not item:
        flash("Cart item not found.", "warning")
        return redirect(url_for('view_cart'))

    # Base delivery fee
    BASE_DELIVERY_FEE = 50
    delivery_fee = BASE_DELIVERY_FEE
    subtotal = item['subtotal']

    # Spin reward
    today = date.today()
    cursor.execute("""
        SELECT reward FROM spin_rewards
        WHERE user_id = %s AND DATE(created_at) = %s
        ORDER BY created_at DESC LIMIT 1
    """, (user_id, today))
    reward_row = cursor.fetchone()
    reward = reward_row['reward'] if reward_row else None

    # Apply reward
    total_price = subtotal 
    if reward == "10% Off":
        total_price *= Decimal('0.9')
    elif reward == "Buy 1 Get 1":
        total_price *= Decimal('0.5')

    if reward == "Free Delivery":
        delivery_fee = 0   

    total_price_with_fee = total_price + delivery_fee

    if request.method == 'POST':
        contact_number = request.form.get('contact_number')
        address = request.form.get('address')
        payment_method = request.form.get('payment_method')

        if not contact_number or not address or not payment_method:
            flash("Please fill contact number, address and payment method.", "warning")
            return redirect(url_for('place_single_order', cart_id=cart_id))

        # Insert order
        cursor.execute("""
            INSERT INTO orders (user_id, total_price, delivery_fee, contact_number, address, status, payment_method, payment_status, reward, created_at)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,NOW())
        """, (
            user_id, total_price_with_fee, delivery_fee, contact_number, address,
            'pending', payment_method, 'paid' if payment_method != 'cod' else 'unpaid', reward
        ))
        order_id = cursor.lastrowid

        # Insert single item
        cursor.execute("""
            INSERT INTO order_items (order_id, pizza_id, size, crust, cheese, toppings, extras, quantity, price)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
        """, (
            order_id,
            item['pizza_id'],
            item['size'],
            item['crust'],
            item['cheese'],
            item['toppings'],
            item['extras'],
            item['quantity'],
            item['subtotal']
        ))

        # Remove from cart
        cursor.execute("DELETE FROM cart WHERE id = %s", (cart_id,))
        mysql.connection.commit()
        flash("Pizza ordered successfully! 🎉", "success")
        return redirect(url_for('orders'))

    return render_template(
        'order.html',
        cart_items=[item],
        total_price=total_price_with_fee,
        delivery_fee=delivery_fee,
        reward=reward
    )

@app.route('/place-order/<int:cart_id>', methods=['GET','POST'])
def place_single_order(cart_id):
    if 'user_id' not in session:
        flash("Login first", "danger")
        return redirect(url_for('login'))

    user_id = session['user_id']
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

    cursor.execute("""
        SELECT c.*, p.name, (c.unit_price * c.quantity) AS subtotal
        FROM cart c
        JOIN pizzas p ON c.pizza_id = p.id
        WHERE c.id = %s AND c.user_id = %s
    """, (cart_id, user_id))
    item = cursor.fetchone()

    if not item:
        flash("Cart item not found.", "warning")
        return redirect(url_for('view_cart'))

    # Base delivery fee
    BASE_DELIVERY_FEE = 50
    delivery_fee = BASE_DELIVERY_FEE
    subtotal = item['subtotal']

    # Spin reward
    today = date.today()
    cursor.execute("""
        SELECT reward FROM spin_rewards
        WHERE user_id = %s AND DATE(created_at) = %s
        ORDER BY created_at DESC LIMIT 1
    """, (user_id, today))
    reward_row = cursor.fetchone()
    reward = reward_row['reward'] if reward_row else None

    # Apply reward
    total_price = subtotal 
    if reward == "10% Off":
        total_price *= Decimal('0.9')
    elif reward == "Buy 1 Get 1":
        total_price *= Decimal('0.5')
    if reward == "Free Delivery":
        delivery_fee = 0   

    total_price_with_fee = total_price + delivery_fee

    if request.method == 'POST':
        contact_number = request.form.get('contact_number')
        address = request.form.get('address')
        payment_method = request.form.get('payment_method')

        if not contact_number or not address or not payment_method:
            flash("Please fill contact number, address and payment method.", "warning")
            return redirect(url_for('place_single_order', cart_id=cart_id))

        # Insert order
        cursor.execute("""
            INSERT INTO orders (
                user_id, total_price, delivery_fee, contact_number, address,
                status, payment_method, payment_status, reward, created_at
            ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,NOW())
        """, (
            user_id, total_price_with_fee, delivery_fee, contact_number, address,
            'pending', payment_method, 'paid' if payment_method != 'cod' else 'unpaid', reward
        ))
        order_id = cursor.lastrowid

        # Insert the pizza into order_items
        cursor.execute("""
            INSERT INTO order_items (
                order_id, pizza_id, size, crust, cheese, toppings, extras, quantity, price
            ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
        """, (
            order_id,
            item['pizza_id'],
            item['size'],
            item['crust'],
            item['cheese'],
            item['toppings'],
            item['extras'],
            item['quantity'],
            item['subtotal']
        ))

        # Remove from cart
        cursor.execute("DELETE FROM cart WHERE id = %s", (cart_id,))
        mysql.connection.commit()
        flash("Pizza ordered successfully! 🎉", "success")
        return redirect(url_for('orders'))

    return render_template(
        'order.html',
        cart_items=[item],
        total_price=total_price_with_fee,
        delivery_fee=delivery_fee,
        reward=reward
    )

@app.route('/orders')
def orders():
    if 'user_id' not in session:
        flash("Please login first", "danger")
        return redirect(url_for('login'))

    user_id = session['user_id']
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

    cursor.execute("""
        SELECT o.id AS order_id,
               o.total_price,
               o.status,
               o.payment_status,
               o.payment_method,
               o.created_at,
               i.size,
               i.quantity,
               i.crust,
               i.cheese,
               i.toppings,
               i.extras,
               p.name AS pizza_name,
               o.reward
        FROM orders o
        JOIN order_items i ON o.id = i.order_id
        JOIN pizzas p ON i.pizza_id = p.id
        WHERE o.user_id = %s
        ORDER BY o.created_at DESC
    """, (user_id,))
    
    orders_data = cursor.fetchall()
    return render_template('orders.html', orders=orders_data)

@app.route('/cancel-order/<int:order_id>', methods=['POST'])
def cancel_order(order_id):
    if 'user_id' not in session:
        flash("Please login first", "danger")
        return redirect(url_for('login'))

    cursor = mysql.connection.cursor()
    cursor.execute("SELECT created_at, status FROM orders WHERE id = %s AND user_id = %s", (order_id, session['user_id']))
    result = cursor.fetchone()

    if not result:
        flash("Order not found.", "danger")
        return redirect(url_for('orders'))

    order_time, status = result

    if status != 'pending':
        flash("Only pending orders can be cancelled.", "warning")
        return redirect(url_for('orders'))

    if datetime.now() - order_time <= timedelta(minutes=7):
        cursor.execute("UPDATE orders SET status = %s WHERE id = %s", ('cancelled', order_id))
        mysql.connection.commit()
        flash("Order cancelled successfully!", "success")
    else:
        flash("Cancellation window expired (7 minutes).", "danger")

    return redirect(url_for('orders'))

@app.route('/customize/<int:pizza_id>', methods=['GET', 'POST'])
def customize_pizza(pizza_id):
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute("SELECT * FROM pizzas WHERE id = %s", (pizza_id,))
    pizza = cursor.fetchone()

    if not pizza:
        flash("Pizza not found!", "danger")
        return redirect(url_for('home'))

    if request.method == 'POST':
        size = request.form['size']
        crust = request.form['crust']
        cheese = request.form['cheese']
        toppings = ','.join(request.form.getlist('toppings')) or None
        extras = request.form.get('extras') or None
        quantity = int(request.form.get('quantity', 1))

        # Calculate price
        unit_price = float(pizza['price'])
        if size == 'medium':
            unit_price += 100
        elif size == 'large':
            unit_price += 200
        if cheese == 'extra':
            unit_price += 50

        # Add to cart instead of orders
        cursor.execute("""
            INSERT INTO cart(user_id, pizza_id, size, crust, cheese, toppings, extras, quantity, unit_price)
            VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s)
        """, (session['user_id'], pizza_id, size, crust, cheese, toppings, extras, quantity, unit_price))

        mysql.connection.commit()
        flash("Your Customized pizza has been added to the cart!", "success")
        return redirect(url_for('view_cart'))

    return render_template('customize.html', pizza=pizza)

@app.route('/admin/dashboard')
def admin_dashboard():
    if 'user_id' not in session or session.get('role') != 'admin':
        flash("Admin access required.", "danger")
        return redirect(url_for('login'))

    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    search_query = request.args.get('q', '').strip()

    if search_query:
        like_pattern = f"%{search_query}%"
        query = '''
            SELECT o.id AS order_id, u.username, o.contact_number, o.address,
                   p.name AS pizza_name, oi.size, oi.quantity, oi.price AS total_price,
                   o.status, o.payment_status, o.created_at
            FROM orders o
            JOIN users u ON o.user_id = u.id
            JOIN order_items oi ON oi.order_id = o.id
            JOIN pizzas p ON p.id = oi.pizza_id
            WHERE u.username LIKE %s OR o.contact_number LIKE %s 
                  OR o.address LIKE %s OR p.name LIKE %s OR o.id LIKE %s
            ORDER BY o.created_at DESC
        '''
        cursor.execute(query, (like_pattern, like_pattern, like_pattern, like_pattern, like_pattern))
    else:
        query = '''
            SELECT o.id AS order_id, u.username, o.contact_number, o.address,
                   p.name AS pizza_name, oi.size, oi.quantity, oi.price AS total_price,
                   o.status, o.payment_status, o.created_at
            FROM orders o
            JOIN users u ON o.user_id = u.id
            JOIN order_items oi ON oi.order_id = o.id
            JOIN pizzas p ON p.id = oi.pizza_id
            ORDER BY o.created_at DESC
        '''
        cursor.execute(query)

    orders = cursor.fetchall()
    return render_template('admin_dashboard.html', orders=orders)

@app.route('/update_order_status/<int:order_id>', methods=['POST'])
def update_status(order_id):
    if 'user_id' not in session or session.get('role') != 'admin':
        flash("Admin access required.", "danger")
        return redirect(url_for('login'))

    status = request.form.get('status')

    if status not in ['pending', 'on process', 'delivered']:
        flash("Invalid status.", "danger")
        return redirect(url_for('admin_dashboard'))

    cursor = mysql.connection.cursor()
    cursor.execute("UPDATE orders SET status = %s WHERE id = %s", (status, order_id))
    mysql.connection.commit()

    flash("Order status updated successfully!", "success")
    return redirect(url_for('admin_dashboard'))  # Adjust this to where you want to redirect after updating

@app.route('/add-to-cart/<int:pizza_id>', methods=['POST'])
def add_to_cart(pizza_id):
    if 'user_id' not in session:
        flash("Please login first", "danger")
        return redirect(url_for('login'))

    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute("SELECT * FROM pizzas WHERE id=%s", (pizza_id,))
    pizza = cursor.fetchone()
    if not pizza:
        flash("Pizza not found!", "danger")
        return redirect(url_for('home'))

    # Get customization data
    size = request.form.get('size', 'small')
    crust = request.form.get('crust', 'thin')
    cheese = request.form.get('cheese', 'normal')
    toppings = ','.join(request.form.getlist('toppings')) or None
    extras = request.form.get('extras') or None
    quantity = int(request.form.get('quantity', 1))

    # Calculate unit price
    unit_price = float(pizza['price'])
    if size == 'medium':
        unit_price += 100
    elif size == 'large':
        unit_price += 200
    if cheese == 'extra':
        unit_price += 50

    # Insert as a new row every time (no merging)
    cursor.execute("""
        INSERT INTO cart(user_id, pizza_id, size, crust, cheese, toppings, extras, quantity, unit_price)
        VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s)
    """, (session['user_id'], pizza_id, size, crust, cheese, toppings, extras, quantity, unit_price))

    mysql.connection.commit()
    flash("Pizza added to cart!", "success")
    return redirect(url_for('view_cart'))

@app.route('/cart')
def view_cart():

    if 'user_id' not in session:
        flash("Login to view your cart", "warning")
        return redirect(url_for('login'))

    user_id = session['user_id']
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute("""
    SELECT 
        c.id AS cart_id,
        p.id AS pizza_id,
        p.name,
        p.price AS base_price,
        c.size,
        c.crust,
        c.cheese,
        c.toppings,
        c.extras,
        c.quantity,
        c.unit_price,
        (c.unit_price * c.quantity) AS subtotal
    FROM cart c
    JOIN pizzas p ON c.pizza_id = p.id
    WHERE c.user_id = %s
""", (user_id,))

    cart_items = cursor.fetchall()
    total = sum([item['subtotal'] for item in cart_items]) if cart_items else 0

    return render_template('cart.html', cart_items=cart_items, total=total)

@app.route('/cart/update/<int:cart_id>', methods=['POST'])
def update_cart_quantity(cart_id):
    if 'user_id' not in session:
        flash("Login first", "warning")
        return redirect(url_for('login'))

    new_qty = request.form.get('quantity', type=int)
    if new_qty < 1:
        flash("Quantity must be at least 1", "warning")
        return redirect(url_for('view_cart'))

    user_id = session['user_id']
    cursor = mysql.connection.cursor()
    cursor.execute("""
        UPDATE cart
        SET quantity = %s
        WHERE id = %s AND user_id = %s
    """, (new_qty, cart_id, user_id))
    mysql.connection.commit()
    flash("Cart updated successfully!", "success")
    return redirect(url_for('view_cart'))

@app.route('/remove-from-cart/<int:cart_id>', methods=['POST'])
def remove_from_cart(cart_id):
    cursor = mysql.connection.cursor()
    cursor.execute("DELETE FROM cart WHERE id = %s AND user_id = %s", (cart_id, session['user_id']))
    mysql.connection.commit()
    flash("Item removed from cart", "info")
    return redirect(url_for('view_cart'))

@app.route('/checkout-single/<int:cart_id>', methods=['POST'])
def checkout_single(cart_id):
    if 'user_id' not in session:
        flash("Login first", "danger")
        return redirect(url_for('login'))

    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute("SELECT * FROM cart WHERE id = %s AND user_id = %s", (cart_id, session['user_id']))
    item = cursor.fetchone()

    if not item:
        flash("Cart item not found", "warning")
        return redirect(url_for('view_cart'))

    # Check spin usage
    user_id = session['user_id']
    today = date.today()
    cursor.execute("""SELECT COUNT(*) FROM spin_rewards WHERE user_id = %s AND DATE(created_at) = %s""",
                   (user_id, today))
    count = cursor.fetchone()['COUNT(*)']

    # redirect to spin first if not spun today, else go to order page
    if count >= 1:
        return redirect(url_for('place_single_order', cart_id=cart_id))
    else:
        # pass the cart_id so spin can redirect back to single order
        return redirect(url_for('spin_wheel', next='single', cart_id=cart_id))

@app.route('/checkout-cart', methods=['POST'])
def checkout_cart():
    if 'user_id' not in session:
        flash("Login first", "danger")
        return redirect(url_for('login'))

    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute("SELECT * FROM cart WHERE user_id = %s", (session['user_id'],))
    items = cursor.fetchall()

    if not items:
        flash("Your cart is empty!", "warning")
        return redirect(url_for('view_cart'))

    # Check spin usage
    user_id = session['user_id']
    today = date.today()
    cursor.execute("""
        SELECT COUNT(*) FROM spin_rewards 
        WHERE user_id = %s AND DATE(created_at) = %s
    """, (user_id, today))
    count = cursor.fetchone()['COUNT(*)']

    if count >= 1:
        # already spun today → skip spin
        return redirect(url_for('place_order'))
    else:
        # allow spin before placing order
        return redirect(url_for('spin_wheel'))

@app.route('/spin', methods=['GET', 'POST'])
def spin_wheel():
    if 'user_id' not in session:
        flash("Login to spin the wheel!", "danger")
        return redirect(url_for('login'))

    user_id = session['user_id']
    today = date.today()
    cursor = mysql.connection.cursor()
    cursor.execute("""SELECT COUNT(*) FROM spin_rewards WHERE user_id = %s AND DATE(created_at) = %s""",
                   (user_id, today))
    count = cursor.fetchone()[0]

    message = "You have already spun today! Continue to payment." if count >= 1 else None

    # get optional query parameters for redirect
    next_action = request.args.get('next')
    cart_id = request.args.get('cart_id')

    # decide where to go after spin
    if next_action == 'single' and cart_id:
        redirect_after_spin = url_for('place_single_order', cart_id=cart_id)
    else:
        redirect_after_spin = url_for('place_order')

    return render_template('spin.html', message=message, redirect_after_spin=redirect_after_spin)

@app.route('/get-spin-reward')
def get_spin_reward():
    if 'user_id' not in session:
        return jsonify({'error': 'Login required'}), 403

    user_id = session['user_id']
    today = date.today()

    cursor = mysql.connection.cursor()
    cursor.execute("""
        SELECT COUNT(*) FROM spin_rewards 
        WHERE user_id = %s AND DATE(created_at) = %s
    """, (user_id, today))
    count = cursor.fetchone()[0]

    if count >= 1:
        return jsonify({'reward': 'Already Spun Today'})

    reward = random.choice(['Free Delivery', '10% Off', 'Extra Cheese', 'No Reward', 'Buy 1 Get 1'])
    cursor.execute("INSERT INTO spin_rewards (user_id, reward) VALUES (%s, %s)", (user_id, reward))
    mysql.connection.commit()

    return jsonify({'reward': reward})

@app.route('/my-rewards')
def view_rewards():
    if 'user_id' not in session:
        flash("Login required", "danger")
        return redirect(url_for('login'))

    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute("SELECT reward, created_at FROM spin_rewards WHERE user_id = %s ORDER BY created_at DESC",
                   (session['user_id'],))
    rewards = cursor.fetchall()

    return render_template("rewards.html", rewards=rewards)

@app.route('/admin/spin-rewards')
def admin_spin_rewards():
    if 'user_id' not in session or session.get('role') != 'admin':
        flash("Admin access only.", "danger")
        return redirect(url_for('login'))

    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute("""
        SELECT sr.id, u.username, sr.reward, sr.created_at
        FROM spin_rewards sr
        JOIN users u ON sr.user_id = u.id
        ORDER BY sr.created_at DESC
    """)
    rewards = cursor.fetchall()

    return render_template("admin_spin_rewards.html", rewards=rewards)

if __name__ == '__main__':
    app.run(debug=True, port=5000)
