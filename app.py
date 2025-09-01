from flask import Flask, render_template,session,request,flash,redirect,url_for , jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from flask_mysqldb import MySQL
from flask_apscheduler import APScheduler
from datetime import datetime, timedelta, date
from PIL import Image
import random, string
from io import BytesIO

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

@app.route('/')
def home():
    cursor = mysql.connection.cursor()
    cursor.execute("SELECT * FROM pizzas")
    pizzas = cursor.fetchall()
    return render_template('home.html', pizzas=pizzas)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = generate_password_hash(request.form['password'])

        cursor = mysql.connection.cursor()
        cursor.execute("INSERT INTO users (username, email, password) VALUES (%s, %s, %s)", (name, email, password))
        mysql.connection.commit()
        flash('Registration successful! Please log in.')
        return redirect(url_for('login'))
    return render_template('register.html')

import MySQLdb

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']  # Change from 'username' to 'email'
        password = request.form['password']

        # Use DictCursor to fetch rows as dictionaries
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
        user = cursor.fetchone()

        if user and check_password_hash(user['password'], password):
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['role'] = user['role']

            if user['role'] == 'admin':
                return redirect(url_for('admin_dashboard'))
            else:
                return redirect(url_for('home'))

        flash('Invalid credentials. Please try again.', 'danger')

    return render_template('login.html')

@app.route('/add_pizza', methods=['GET', 'POST'])
def add_pizza():
    if request.method == 'POST':
        name = request.form['pizza_name']
        description = request.form['description']
        price = float(request.form['price'])
        image_source = request.form['image_source']  # 'url' or 'upload'

        image_url = ''
        
        if image_source == 'url':
            image_url = request.form['image_url']  # Image URL from input
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


        cursor = mysql.connection.cursor()
        cursor.execute(
            'INSERT INTO pizzas (name, description, price, image_url) VALUES (%s, %s, %s, %s)',
            (name, description, price, image_url)
        )
        mysql.connection.commit()

        flash('Pizza added successfully!', 'success')
        return redirect(url_for('add_pizza'))

    return render_template('add_pizza.html')

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    flash('You have been logged out. Visit again!','info')
    return redirect(url_for('home'))

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

@app.route('/orders')
def orders():
    if 'user_id' not in session:
        flash("Please login first", "danger")
        return redirect(url_for('login'))

    user_id = session['user_id']
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

    cursor.execute("""
        SELECT o.id, p.name, o.size, o.quantity, o.total_price,
               o.status, o.payment_status, o.payment_method, o.created_at
        FROM orders o
        JOIN pizzas p ON o.pizza_id = p.id
        WHERE o.user_id = %s
        ORDER BY o.created_at DESC
    """, (user_id,))
    
    orders = cursor.fetchall()
    return render_template('orders.html', orders=orders)

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
        flash("Your customized pizza has been added to the cart!", "success")
        return redirect(url_for('view_cart'))

    return render_template('customize.html', pizza=pizza)

# Unified payment route
@app.route('/payment', methods=['GET', 'POST'])
def payment():
    if 'user_id' not in session:
        flash("Login first", "danger")
        return redirect(url_for('login'))

    user_id = session['user_id']
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

    # Get cart items
    cursor.execute("SELECT * FROM cart WHERE user_id = %s", (user_id,))
    cart_items = cursor.fetchall()

    if not cart_items:
        flash("Your cart is empty!", "warning")
        return redirect(url_for('view_cart'))

    total_amount = sum(item['unit_price'] * item['quantity'] for item in cart_items)

    if request.method == 'POST':
        payment_method = request.form.get('payment_method')
        if not payment_method:
            flash("Please select a payment method.", "warning")
            return redirect(url_for('payment'))

        # Move cart items to orders
        for item in cart_items:
            cursor.execute("""
                INSERT INTO orders (
                    user_id, pizza_id, size, crust, cheese, toppings, extras, quantity, total_price, status, payment_method
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                user_id,
                item['pizza_id'],
                item['size'],
                item['crust'],
                item['cheese'],
                item['toppings'],
                item['extras'],
                item['quantity'],
                item['unit_price'] * item['quantity'],
                'paid',
                payment_method
            ))

        cursor.execute("DELETE FROM cart WHERE user_id = %s", (user_id,))
        mysql.connection.commit()

        flash(f"Payment of NPR {total_amount} successful! Your orders are being processed.", "success")
        return redirect(url_for('orders'))

    return render_template('payment.html', cart_items=cart_items, total=total_amount)

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
            SELECT o.id, u.username, o.address, p.name, o.size, o.quantity,
                   o.total_price, o.status, o.payment_status, o.created_at
            FROM orders o
            JOIN users u ON o.user_id = u.id
            JOIN pizzas p ON o.pizza_id = p.id
            WHERE u.username LIKE %s OR o.address LIKE %s OR p.name LIKE %s OR o.id LIKE %s
            ORDER BY o.created_at DESC
        '''
        cursor.execute(query, (like_pattern, like_pattern, like_pattern, like_pattern))
    else:
        query = '''
            SELECT o.id, u.username, o.address, p.name, o.size, o.quantity,
                   o.total_price, o.status, o.payment_status, o.created_at
            FROM orders o
            JOIN users u ON o.user_id = u.id
            JOIN pizzas p ON o.pizza_id = p.id
            ORDER BY o.created_at DESC
        '''
        cursor.execute(query)

    orders = cursor.fetchall()
    return render_template('admin_dashboard.html', orders=orders)

def auto_update_order_status():
    with app.app_context():
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute("SELECT id, created_at, status FROM orders")
        orders = cursor.fetchall()

        for order in orders:
            order_id, created_at, status = order['id'], order['created_at'], order['status']
            now = datetime.now()
            time_passed = now - created_at

            if status == 'pending' and time_passed >= timedelta(minutes=10):
                cursor.execute("UPDATE orders SET status = 'on process' WHERE id = %s", (order_id,))
            elif status == 'on process' and time_passed >= timedelta(minutes=35):
                cursor.execute("UPDATE orders SET status = 'delivered' WHERE id = %s", (order_id,))

        mysql.connection.commit()

#schedule it to run every 17 minutes
scheduler.add_job(id='AutoStatusUpdate', func=auto_update_order_status, trigger='interval', minutes=17)

@app.route('/update_order_status/<int:order_id>', methods=['POST'])
def update_status(order_id):
    if 'user_id' not in session or session.get('role') != 'admin':
        flash("Admin access required.", "danger")
        return redirect(url_for('login'))

    status = request.form.get('status')

    if status not in ['pending', 'completed', 'cancelled']:
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
    flash("Customized pizza added to cart!", "success")
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

@app.route('/remove-from-cart/<int:cart_id>', methods=['POST'])
def remove_from_cart(cart_id):
    cursor = mysql.connection.cursor()
    cursor.execute("DELETE FROM cart WHERE id = %s AND user_id = %s", (cart_id, session['user_id']))
    mysql.connection.commit()
    flash("Item removed from cart", "info")
    return redirect(url_for('view_cart'))

@app.route('/checkout-cart', methods=['POST'])
def checkout_cart():
    if 'user_id' not in session:
        flash("Login first", "danger")
        return redirect(url_for('login'))

    user_id = session['user_id']
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

    cursor.execute("SELECT * FROM cart WHERE user_id = %s", (user_id,))
    items = cursor.fetchall()

    if not items:
        flash("Your cart is empty!", "warning")
        return redirect(url_for('view_cart'))

    for item in items:
        cursor.execute("""
            INSERT INTO orders (
                user_id, pizza_id, size, crust, cheese, toppings, extras, quantity, total_price, status
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            user_id,
            item['pizza_id'],
            item['size'],
            item['crust'],
            item['cheese'],
            item['toppings'],
            item['extras'],
            item['quantity'],
            item['unit_price'] * item['quantity'],
            'pending'
        ))

    # Clear cart after checkout
    cursor.execute("DELETE FROM cart WHERE user_id = %s", (user_id,))
    mysql.connection.commit()

    flash("Order placed successfully from cart!", "success")
    return redirect(url_for('payment'))

@app.route('/spin')
def spin_wheel():
    if 'user_id' not in session:
        flash("Login to spin the wheel!", "danger")
        return redirect(url_for('login'))

    user_id = session['user_id']
    today = date.today()

    cursor = mysql.connection.cursor()
    cursor.execute("""
        SELECT COUNT(*) FROM spin_rewards
        WHERE user_id = %s AND DATE(created_at) = %s
    """, (user_id, today))
    count = cursor.fetchone()[0]

    if count >= 1:
        # User has already spun for today
        return render_template('spin.html', message="You have already spun today! Try again tomorrow.")
    
    # If user hasn't spun yet, show the wheel
    return render_template('spin.html', message=None)


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

    reward = random.choice(['Free Pizza', '50% Off', 'Extra Cheese', 'No Reward', 'Buy 1 Get 1'])
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
