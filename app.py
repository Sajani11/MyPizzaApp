from flask import Flask, render_template,session,request,flash,redirect,url_for
from werkzeug.security import generate_password_hash, check_password_hash
from flask_mysqldb import MySQL
from flask_apscheduler import APScheduler
from datetime import datetime, timedelta

from config import Config ,ConfigScheduler

app = Flask(__name__)
app.config.from_object(Config)
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
    cursor = None
    try:
        if request.method == 'POST':
            name = request.form.get('pizza_name', '').strip()
            description = request.form.get('description', '').strip()
            price_raw = request.form.get('price', '').strip()
            image_url = request.form.get('image_url', '').strip()

            if not all([name, description, price_raw, image_url]):
                flash('All fields are required.', 'warning')
                return render_template('add_pizza.html')

            try:
                price = float(price_raw)
            except ValueError:
                flash('Invalid price format.', 'warning')
                return render_template('add_pizza.html')

            cursor = mysql.connection.cursor()
            cursor.execute(
                'INSERT INTO pizzas (name, description, price, image_url) VALUES (%s, %s, %s, %s)',
                (name, description, price, image_url)
            )
            mysql.connection.commit()
            flash('Pizza added successfully!', 'success')
            return redirect(url_for('add_pizza')) 

    except Exception as e:
        print(f"Error adding pizza: {e}")
        flash('Failed to add pizza. Please try again.', 'danger') 

    finally:
        if cursor:
            cursor.close()

    return render_template('add_pizza.html')


@app.route('/logout')
def logout():
    session.pop('user_id', None)
    flash('You have been logged out. Visit again!','info')
    return redirect(url_for('home'))

@app.route('/choose-auth')
def choose_auth():
    return render_template('choose_auth.html')

@app.route('/order/<int:pizza_id>', methods=['GET', 'POST'])
def order_pizza(pizza_id):
    if 'user_id' not in session:
        flash("Please login first", "danger")
        return redirect(url_for('choose_auth'))

    cursor = mysql.connection.cursor()
    cursor.execute("SELECT * FROM pizzas WHERE id = %s", (pizza_id,))
    pizza = cursor.fetchone()

    if not pizza:
        flash("Pizza not found!", "danger")
        return redirect(url_for('home'))

    if request.method == 'POST':
        size = request.form['size']
        quantity = int(request.form['quantity'])
        user_id = session['user_id']

        # Price logic
        base_price = pizza[3]  # 3rd index corresponds to 'price'
        if size == 'medium':
            price = base_price + 100
        elif size == 'large':
            price = base_price + 200
        else:
            price = base_price  # small

        total_price = price * quantity

        # Insert into orders table (with size, quantity, and total price)
        cursor.execute("""
            INSERT INTO orders (user_id, pizza_id, size, quantity, total_price, status)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (user_id, pizza_id, size, quantity, total_price, 'pending'))
        order_id = cursor.lastrowid
        mysql.connection.commit()

        flash("Your order has been placed successfully!", "success")
        return redirect(url_for('payment',order_id= order_id))

    return render_template('order.html', pizza=pizza)

@app.route('/orders')
def orders():
    if 'user_id' not in session:
        flash("Please login first", "danger")
        return redirect(url_for('choose_auth'))

    user_id = session['user_id']
    cursor = mysql.connection.cursor()

    cursor.execute("""
        SELECT o.id, p.name, o.size, o.quantity, o.total_price, o.status, o.created_at
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
    cursor = mysql.connection.cursor()
    cursor.execute("SELECT * FROM pizzas WHERE id = %s", (pizza_id,))
    pizza = cursor.fetchone()

    if not pizza:
        flash("Pizza not found!", "danger")
        return redirect(url_for('home'))

    if request.method == 'POST':
        size = request.form['size']
        quantity = int(request.form['quantity'])
        crust = request.form['crust']
        cheese = request.form['cheese']
        toppings = request.form.getlist('toppings')
        extras = request.form.get('extras', '').strip()

        base_price = pizza[3]  # The pizza price from the database

        # Apply size-based price adjustments
        if size == 'medium':
            price = base_price + 100
        elif size == 'large':
            price = base_price + 200
        else:
            price = base_price  # small size

        # Apply extra cheese price adjustment
        if cheese == 'extra':
            price += 50

        total_price = price * quantity

        # Store the customized pizza in the orders table or show on the payment page
        user_id = session['user_id']
        cursor.execute("""
            INSERT INTO orders (user_id, pizza_id, size, quantity, crust, cheese, toppings, extras, total_price, status)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (user_id, pizza_id, size, quantity, crust, cheese, ', '.join(toppings), extras, total_price, 'pending'))
        order_id = cursor.lastrowid 
        mysql.connection.commit()

        flash("Your customized pizza has been added to the cart!", "success")
        return redirect(url_for('payment', order_id=order_id))  # Assuming insert_id() gives the latest order ID

    return render_template('customize.html', pizza=pizza)

@app.route('/payment/<int:order_id>', methods=['GET', 'POST'])
def payment(order_id):
    cursor = mysql.connection.cursor()
    cursor.execute("SELECT * FROM orders WHERE id = %s AND user_id = %s", (order_id, session['user_id']))
    order = cursor.fetchone()

    if not order:
        flash("Order not found!", "danger")
        return redirect(url_for('home'))

    if request.method == 'POST':
        payment_method = request.form['payment_method']
        cursor.execute("UPDATE orders SET payment_method = %s, status = %s WHERE id = %s", (payment_method, 'paid', order_id))
        mysql.connection.commit()
        flash("Payment successful! Your order is being processed.", "success")
        return redirect(url_for('orders'))

    return render_template('payment.html', order=order)


@app.route('/admin/dashboard')
def admin_dashboard():
    if 'user_id' not in session or session.get('role') != 'admin':
        flash("Admin access required.", "danger")
        return redirect(url_for('login'))

    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)  # Using DictCursor
    query = '''
        SELECT o.id, u.username, p.name, o.size, o.quantity, o.total_price, 
               o.status, o.created_at
        FROM orders o
        JOIN users u ON o.user_id = u.id
        JOIN pizzas p ON o.pizza_id = p.id
        ORDER BY o.created_at DESC
    '''
    cursor.execute(query)
    orders = cursor.fetchall()  # This will now return a list of dictionaries
    return render_template('admin_dashboard.html', orders=orders)

def auto_update_order_status():
    with app.app_context():  # to use db inside job
        cursor = mysql.connection.cursor()
        cursor.execute("SELECT id, created_at, status FROM orders")
        orders = cursor.fetchall()

        for order in orders:
            order_id, created_at, status = order
            now = datetime.now()
            time_passed = now - created_at

            if status == 'pending' and time_passed >= timedelta(minutes=10):
                cursor.execute("UPDATE orders SET status = 'on process' WHERE id = %s", (order_id,))
            elif status == 'on process' and time_passed >= timedelta(minutes=35):
                cursor.execute("UPDATE orders SET status = 'delivered' WHERE id = %s", (order_id,))

        mysql.connection.commit()

# Schedule it to run every 17 minutes
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


if __name__ == '__main__':
    app.run(debug=True, port=5000)

