from flask import Flask, render_template, request, redirect, url_for, session
import mysql.connector
import joblib
import numpy as np
import os
from werkzeug.utils import secure_filename
import datetime
from markupsafe import escape
import os
from flask import request, jsonify



app = Flask(__name__)

# Load ML model
model = joblib.load("algaemodel.pkl")

def get_db_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="root",
        database="co2nect"
    )


@app.route('/')
def home():
    conn = get_db_connection()
    cursor = conn.cursor()

    sql = "SELECT sum(credits) FROM transactions"
    cursor.execute(sql)
    sumcredits = cursor.fetchone()
    #print(sumcredits)

    cursor.close()
    conn.close()
    return render_template("home.html",sumcredits=sumcredits)


@app.route('/logout')
def logout():
    session.clear()
    return render_template("home.html")


@app.route('/login')
def login():
    return render_template("login.html")


@app.route('/farmer_login', methods=['GET', 'POST'])
def farmer_login():
    message = ""

    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        try:
            conn = get_db_connection()
            cursor = conn.cursor(dictionary=True)

            sql = "SELECT * FROM farmer WHERE email = %s AND password = %s"
            cursor.execute(sql, (email, password))
            farmer = cursor.fetchone()

            cursor.close()
            conn.close()

            if farmer:
                session['farmer_id'] = farmer['id']
                session['farmer_name'] = farmer['name']
                return redirect(url_for('farmer_dashboard'))
            else:
                message = "Invalid Email or Password!"

        except Exception as e:
            print("Login Error:", e)
            message = "Database Error!"

    return render_template("farmer/farmer_login.html", message=message)

@app.route('/farmer_dashboard')
def farmer_dashboard():
    if 'farmer_id' not in session:
        return redirect(url_for('farmer_login'))

    return render_template("farmer/farmer_dashboard.html",
                           name=session['farmer_name'])
    
@app.route('/farmer/ml_predict_growth', methods=['GET', 'POST'])
def ml_predict_growth():
    result = None
    form_data = {
        "light": "",
        "nitrate": "",
        "iron": "",
        "phosphate": "",
        "temperature": "",
        "ph": "",
        "co2": ""
    }

    if request.method == 'POST':

        # Reset button pressed → clear all fields
        if "reset" in request.form:
            return render_template("farmer/ml_predict_growth.html",
                                   result=None,
                                   form_data=form_data)

        try:
            # Save values so they remain in the form
            form_data["light"] = request.form['light']
            form_data["nitrate"] = request.form['nitrate']
            form_data["iron"] = request.form['iron']
            form_data["phosphate"] = request.form['phosphate']
            form_data["temperature"] = request.form['temperature']
            form_data["ph"] = request.form['ph']
            form_data["co2"] = request.form['co2']

            # Convert to numpy array
            features = np.array([[float(form_data["light"]),
                                  float(form_data["nitrate"]),
                                  float(form_data["iron"]),
                                  float(form_data["phosphate"]),
                                  float(form_data["temperature"]),
                                  float(form_data["ph"]),
                                  float(form_data["co2"])]])

            

            # Predict
            prediction = model.predict(features)
            result = round(float(prediction[0]), 2)

        except Exception as e:
            print("Prediction Error:", e)
            result = "Error processing prediction!"

    return render_template("farmer/ml_predict_growth.html",
                           result=result,
                           form_data=form_data)

@app.route('/farmer/manage_profile', methods=['GET', 'POST'])
def manage_profile():
    if 'farmer_id' not in session:
        return redirect(url_for('farmer_login'))

    message = ""

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    farmer_id = session['farmer_id']

    # Fetch current farmer details
    cursor.execute("SELECT * FROM farmer WHERE id = %s", (farmer_id,))
    farmer = cursor.fetchone()

    if request.method == 'POST':
        phone = request.form['phone']
        city = request.form['city']
        address = request.form['address']
        password = request.form['password']

        try:
            update_sql = """
                UPDATE farmer 
                SET phone=%s, city=%s, address=%s, password=%s 
                WHERE id=%s
            """

            cursor.execute(update_sql, (phone, city, address, password, farmer_id))
            conn.commit()

            message = "Credentials Updated Successfully!"

            # Reload data
            cursor.execute("SELECT * FROM farmer WHERE id = %s", (farmer_id,))
            farmer = cursor.fetchone()

        except Exception as e:
            print("Update Error:", e)
            message = "Error updating details!"

    cursor.close()
    conn.close()

    return render_template("farmer/manage_profile.html",
                           farmer=farmer,
                           message=message)
    

@app.route('/farmer/add_algae_growth', methods=['GET', 'POST'])
def add_algae_growth():
    if 'farmer_id' not in session:
        return redirect(url_for('farmer_login'))

    message = ""

    if request.method == 'POST':
        try:
            farmer_id = session['farmer_id']
            algae_kg = float(request.form['algae'])
            co2_tons = float(request.form['co2'])
            credits = float(request.form['credits'])

            conn = get_db_connection()
            cursor = conn.cursor()

            sql = """INSERT INTO algaegrowth (farmer_id, algae_kg, co2_tons, credits) 
                     VALUES (%s, %s, %s, %s)"""
            cursor.execute(sql, (farmer_id, algae_kg, co2_tons, credits))
            conn.commit()

            cursor.close()
            conn.close()

            message = "Algae Growth Data Added Successfully!"

        except Exception as e:
            print("DB Insert Error:", e)
            message = "Error saving data!"

    return render_template("farmer/add_algae_growth.html", message=message)

@app.route('/farmer/view_growth_data')
def view_growth_data():
    if 'farmer_id' not in session:
        return redirect(url_for('farmer_login'))

    farmer_id = session['farmer_id']

    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        sql = "SELECT * FROM algaegrowth WHERE farmer_id = %s ORDER BY created_at DESC"
        cursor.execute(sql, (farmer_id,))
        records = cursor.fetchall()

        cursor.close()
        conn.close()

    except Exception as e:
        print("DB Fetch Error:", e)
        records = []

    return render_template("farmer/view_growth_data.html", records=records)

@app.route('/farmer/sell_product', methods=['GET', 'POST'])
def sell_product():
    if 'farmer_id' not in session:
        return redirect(url_for('farmer_login'))

    message = ""

    if request.method == 'POST':
        try:
            farmer_id = session['farmer_id']
            product_name = request.form['product_name']
            quantity = request.form['quantity']
            price = request.form['price']

            # IMAGE HANDLING
            file = request.files['image']

            if file:
                filename = secure_filename(file.filename)
                image_path = os.path.join('static/products', filename)
                file.save(image_path)
            else:
                filename = None

            # INSERT INTO DB
            conn = get_db_connection()
            cursor = conn.cursor()

            sql = """
                INSERT INTO products (farmer_id, product_name, quantity, price, image)
                VALUES (%s, %s, %s, %s, %s)
            """

            cursor.execute(sql, (farmer_id, product_name, quantity, price, filename))
            conn.commit()

            cursor.close()
            conn.close()

            message = "Product Added Successfully!"

        except Exception as e:
            print("Product Insert Error:", e)
            message = "Error adding product!"

    return render_template("farmer/sell_product.html", message=message)

@app.route('/farmer/view_products')
def view_products():
    if 'farmer_id' not in session:
        return redirect(url_for('farmer_login'))

    farmer_id = session['farmer_id']

    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("SELECT * FROM products WHERE farmer_id=%s", (farmer_id,))
        products = cursor.fetchall()

        cursor.close()
        conn.close()

    except Exception as e:
        print("Fetch Products Error:", e)
        products = []

    return render_template("farmer/view_products.html", products=products)

@app.route('/farmer/delete_product/<int:product_id>')
def delete_product(product_id):

    if 'farmer_id' not in session:
        return redirect(url_for('farmer_login'))

    farmer_id = session['farmer_id']

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Delete only if product belongs to the logged-in farmer
        sql = "DELETE FROM products WHERE id=%s AND farmer_id=%s"
        cursor.execute(sql, (product_id, farmer_id))

        conn.commit()
        cursor.close()
        conn.close()

    except Exception as e:
        print("Delete Error:", e)

    return redirect(url_for('view_products'))




@app.route('/farmer_signup', methods=['GET', 'POST'])
def farmer_signup():
    msg = ""   # message to show on page

    if request.method == 'POST':

        name = request.form['name']
        email = request.form['email']
        phone = request.form['phone']
        city = request.form['city']
        address = request.form['address']
        password = request.form['password']

        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM farmer WHERE email = %s", (email,))
            email_exists = cursor.fetchone()

            if email_exists:
                msg = "Email already exists!"
                return render_template("farmer/farmer_signup.html", message=msg)
            cursor.execute("SELECT * FROM farmer WHERE phone = %s", (phone,))
            phone_exists = cursor.fetchone()

            if phone_exists:
                msg = "Phone number already exists!"
                return render_template("farmer/farmer_signup.html", message=msg)

            # --------------------------------
            # 3. INSERT NEW RECORD
            # --------------------------------
            sql = """INSERT INTO farmer 
                     (name, email, phone, city, address, password) 
                     VALUES (%s, %s, %s, %s, %s, %s)"""

            values = (name, email, phone, city, address, password)

            cursor.execute(sql, values)
            conn.commit()

            cursor.close()
            conn.close()

            return redirect(url_for('farmer_login'))

        except Exception as e:
            print("Error:", e)
            return "Database Error Occurred!"

    return render_template("farmer/farmer_signup.html")

@app.route('/industrial_login', methods=['GET', 'POST'])
def industrial_login():
    message = None

    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        try:
            conn = get_db_connection()
            cursor = conn.cursor(dictionary=True)

            # Check if industrialist exists
            sql = "SELECT * FROM industrial WHERE email=%s AND password=%s"
            cursor.execute(sql, (email, password))
            industrial = cursor.fetchone()

            cursor.close()
            conn.close()

            if industrial:
                # SET SESSION
                session['industrial_id'] = industrial['id']
                session['industrial_name'] = industrial['company_name']

                return redirect(url_for('industrial_dashboard'))
            else:
                message = "Invalid email or password!"
                return render_template("industrial/industrial_login.html", message=message)

        except Exception as e:
            print("Login Error:", e)
            return render_template("industrial/industrial_login.html",
                                   message="Database Error Occurred!")

    return render_template("industrial/industrial_login.html")


@app.route('/industrial_signup', methods=['GET', 'POST'])
def industrial_signup():
    message = None

    if request.method == 'POST':

        company_name = request.form['company_name']
        email = request.form['email']
        phone = request.form['phone']
        city = request.form['city']
        address = request.form['address']
        password = request.form['password']

        try:
            conn = get_db_connection()
            cursor = conn.cursor(dictionary=True)

            # Check if email exists
            cursor.execute("SELECT * FROM industrial WHERE email=%s", (email,))
            email_exist = cursor.fetchone()

            if email_exist:
                message = "Email already registered!"
                cursor.close()
                conn.close()
                return render_template("industrial/industrial_signup.html", message=message)

            # Check if phone exists
            cursor.execute("SELECT * FROM industrial WHERE phone=%s", (phone,))
            phone_exist = cursor.fetchone()

            if phone_exist:
                message = "Phone number already registered!"
                cursor.close()
                conn.close()
                return render_template("industrial/industrial_signup.html", message=message)

            # Insert new industrialist
            sql = """INSERT INTO industrial 
                    (company_name, email, phone, city, address, password) 
                    VALUES (%s, %s, %s, %s, %s, %s)"""

            values = (company_name, email, phone, city, address, password)
            cursor.execute(sql, values)
            conn.commit()

            cursor.close()
            conn.close()

            return redirect(url_for('industrial_login'))

        except Exception as e:
            print("Error:", e)
            return render_template("industrial/industrial_signup.html", 
                                   message="Database Error Occurred!")

    # GET request
    return render_template("industrial/industrial_signup.html")

@app.route('/industrial_dashboard')
def industrial_dashboard():
    if 'industrial_id' not in session:
        return redirect(url_for('industrial_login'))

    industrial_id = session['industrial_id']
    name = session['industrial_name']

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT COALESCE(SUM(credits),0) FROM transactions WHERE industrialist_id=%s",
                       (industrial_id,))
        total_credits = cursor.fetchone()[0]

        cursor.close()
        conn.close()

    except:
        total_credits = 0

    return render_template("industrial/industrial_dashboard.html",
                           name=name,
                           total_credits=total_credits)




@app.route('/industrial/manage_profile', methods=['GET', 'POST'])
def industrial_manage_profile():
    if 'industrial_id' not in session:
        return redirect(url_for('industrial_login'))

    industrial_id = session['industrial_id']
    message = None

    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        # GET REQUEST → Fetch existing details
        if request.method == 'GET':
            cursor.execute("SELECT * FROM industrial WHERE id=%s", (industrial_id,))
            data = cursor.fetchone()
            cursor.close()
            conn.close()
            return render_template("industrial/manage_profile.html", data=data)

        # POST REQUEST → Update modified fields
        if request.method == 'POST':
            phone = request.form['phone']
            city = request.form['city']
            address = request.form['address']
            password = request.form['password']

            sql = """
                UPDATE industrial
                SET phone=%s, city=%s, address=%s, password=%s
                WHERE id=%s
            """
            cursor.execute(sql, (phone, city, address, password, industrial_id))
            conn.commit()

            cursor.close()
            conn.close()

            message = "Profile Updated Successfully!"

            # Fetch updated details
            conn = get_db_connection()
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT * FROM industrial WHERE id=%s", (industrial_id,))
            data = cursor.fetchone()
            cursor.close()
            conn.close()

            return render_template("industrial/manage_profile.html", data=data, message=message)

    except Exception as e:
        print("Error:", e)
        return "Database Error Occurred!"

@app.route('/industrial/request_credits')
def industrial_request_credits():
    # ensure logged in
    if 'industrial_id' not in session:
        return redirect(url_for('industrial_login'))

    industrial_id = session['industrial_id']

    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        # get industrialist city (make sure to handle None)
        cursor.execute("SELECT city FROM industrial WHERE id = %s", (industrial_id,))
        row = cursor.fetchone()
        if not row or not row.get('city'):
            cursor.close()
            conn.close()
            return render_template("industrial/request_credits.html", records=[], message="Your city not set in profile.")

        industrial_city = row['city'].strip().lower()

        # fetch algaegrowth rows where farmer city matches industrial city (case-insensitive)
        sql = """
            SELECT a.id AS algaegrowth_id, a.farmer_id, a.algae_kg, a.co2_tons, a.credits, a.created_at,
                   f.name as farmer_name, f.city as farmer_city
            FROM algaegrowth a
            JOIN farmer f ON a.farmer_id = f.id
            WHERE LOWER(TRIM(f.city)) = %s
            ORDER BY a.created_at DESC
        """
        cursor.execute(sql, (industrial_city,))
        records = cursor.fetchall()

        cursor.close()
        conn.close()

    except Exception as e:
        print("Request Credits Error:", e)
        records = []
        message = "Database Error Occurred!"

    return render_template("industrial/request_credits.html", records=records, message=None)

@app.route('/industrial/pay/<int:algaegrowth_id>', methods=['GET', 'POST'])
def industrial_pay(algaegrowth_id):
    if 'industrial_id' not in session:
        return redirect(url_for('industrial_login'))

    industrial_id = session['industrial_id']
    farmer_id = request.args.get('farmer_id', type=int)
    credits_query = request.args.get('credits', type=float)

    # Validate the algaegrowth record belongs to the farmer and match city constraint is handled earlier,
    # but we still fetch the algaegrowth row for display & safety.
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT a.*, f.name as farmer_name, f.city as farmer_city
            FROM algaegrowth a
            JOIN farmer f ON a.farmer_id = f.id
            WHERE a.id = %s
        """, (algaegrowth_id,))
        rec = cursor.fetchone()
        cursor.close()
        conn.close()
    except Exception as e:
        print("Payment page fetch error:", e)
        rec = None

    if not rec:
        return "Record not found", 404

    # Use credits from query if present, else from record
    credits = credits_query if credits_query is not None else rec.get('credits', 0)
    try:
        credits = float(credits)
    except:
        credits = float(rec.get('credits', 0))

    amount = round(credits * 800.0, 2)  # 1 credit = 800 Rs

    # POST -> perform "payment" (dummy) and store in transactions
    if request.method == 'POST':
        transaction_type = request.form.get('payment_type')  # 'card' or 'upi'
        try:
            # You can validate card/upi fields here as needed
            # Insert transaction record
            conn = get_db_connection()
            cursor = conn.cursor()
            insert_sql = """
                INSERT INTO transactions
                (industrialist_id, farmer_id, algaegrowth_id, credits, amount, transaction_type)
                VALUES (%s, %s, %s, %s, %s, %s)
            """
            cursor.execute(insert_sql, (industrial_id, rec['farmer_id'], algaegrowth_id, credits, amount, transaction_type))
            conn.commit()
            
            cursor.execute("delete from algaegrowth where id=%s",(algaegrowth_id,))
            conn.commit()
            cursor.close()
            conn.close()

            # After successful insert, render a page that shows a processing animation then success
            return render_template("industrial/payment_result.html",
                                   status="success",
                                   amount=amount,
                                   credits=credits,
                                   farmer_name=rec['farmer_name'],
                                   transaction_type=transaction_type)

        except Exception as e:
            print("Transaction Insert Error:", e)
            return render_template("industrial/payment_result.html",
                                   status="error",
                                   error=str(e))

    # GET -> show payment form
    return render_template("industrial/industrial_pay.html",
                           rec=rec,
                           credits=credits,
                           amount=amount)


@app.route('/industrial/credit_transactions')
def industrial_credit_transactions():
    if 'industrial_id' not in session:
        return redirect(url_for('industrial_login'))

    industrial_id = session['industrial_id']

    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        sql = """
            SELECT t.*, 
                   f.name AS farmer_name, 
                   f.phone AS farmer_phone,
                   f.email AS farmer_email
            FROM transactions t
            JOIN farmer f ON t.farmer_id = f.id
            WHERE t.industrialist_id = %s
            ORDER BY t.created_at DESC
        """
        cursor.execute(sql, (industrial_id,))
        transactions = cursor.fetchall()

        cursor.close()
        conn.close()

    except Exception as e:
        print("Transaction Fetch Error:", e)
        transactions = []

    return render_template("industrial/credit_transactions.html", transactions=transactions)

@app.route('/consumer_signup', methods=['GET', 'POST'])
def consumer_signup():
    message = None

    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        phone = request.form['phone']
        city = request.form['city']
        address = request.form['address']
        password = request.form['password']

        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            # Check for duplicate email or phone
            cursor.execute("SELECT * FROM consumer WHERE email=%s", (email,))
            if cursor.fetchone():
                return render_template("customer/customer_signup.html",
                                       message="Email already exists!")

            cursor.execute("SELECT * FROM consumer WHERE phone=%s", (phone,))
            if cursor.fetchone():
                return render_template("customer/customer_signup.html",
                                       message="Phone number already exists!")

            # Insert new customer
            sql = """
                INSERT INTO consumer (name, email, phone, city, address, password)
                VALUES (%s, %s, %s, %s, %s, %s)
            """

            cursor.execute(sql, (name, email, phone, city, address, password))
            conn.commit()

            cursor.close()
            conn.close()

            return redirect(url_for('consumer_login'))

        except Exception as e:
            print("Error:", e)
            return render_template("customer/customer_signup.html",
                                   message="Database Error Occurred!")

    return render_template("customer/customer_signup.html")

@app.route('/consumer_login', methods=['GET', 'POST'])
def consumer_login():
    message = None

    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        try:
            conn = get_db_connection()
            cursor = conn.cursor(dictionary=True)

            cursor.execute("SELECT * FROM consumer WHERE email=%s AND password=%s", 
                           (email, password))
            user = cursor.fetchone()

            cursor.close()
            conn.close()

            if user:
                session['consumer_id'] = user['id']
                session['consumer_name'] = user['name']
                return redirect(url_for('consumer_dashboard'))
            else:
                message = "Invalid email or password!"

        except Exception as e:
            print("Login Error:", e)
            message = "Database Error Occurred!"

    return render_template("customer/customer_login.html", message=message)

@app.route('/consumer_dashboard')
def consumer_dashboard():
    if 'consumer_id' not in session:
        return redirect(url_for('consumer_login'))

    return render_template("customer/customer_dashboard.html",
                           name=session['consumer_name'])


@app.route('/customer/manage_profile', methods=['GET', 'POST'])
def customer_manage_profile():
    if 'consumer_id' not in session:
        return redirect('/customer_login')

    cid = session['consumer_id']
    print("cid  ",cid)
    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)

    # Fetch customer details
    cur.execute("SELECT * FROM consumer WHERE id=%s", (cid,))
    customer = cur.fetchone()

    if request.method == "POST":
        phone = request.form['phone']
        city = request.form['city']
        address = request.form['address']
        password = request.form['password']

        cur.execute("""
            UPDATE consumer 
            SET phone=%s, city=%s, address=%s, password=%s 
            WHERE id=%s
        """, (phone, city, address, password, cid))
        conn.commit()

        return render_template(
            "customer/manage_profile.html",
            data=customer,
            message="Profile Updated Successfully!"
        )

    return render_template("customer/manage_profile.html", data=customer)


@app.route('/customer/view_products')
def customer_view_products():
    if 'consumer_id' not in session:
        return redirect('/customer_login')

    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)
    cur.execute("SELECT * FROM products")
    products = cur.fetchall()

    return render_template("customer/view_products.html", products=products)

@app.route('/customer/add_to_cart/<int:pid>')
def add_to_cart(pid):
    if 'consumer_id' not in session:
        return redirect('/customer_login')

    cid = session['consumer_id']
    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)

    # Check if already added
    cur.execute("SELECT * FROM cart WHERE customer_id=%s AND product_id=%s", (cid, pid))
    exists = cur.fetchone()

    if exists:
        return redirect("/customer/view_products?msg=exists")

    # Insert into cart table
    cur.execute("INSERT INTO cart (customer_id, product_id) VALUES (%s, %s)", (cid, pid))
    conn.commit()

    return redirect("/customer/view_products?msg=added")

@app.route('/customer/cart')
def customer_cart():
    if 'consumer_id' not in session:
        return redirect(url_for('consumer_login'))

    cid = session['consumer_id']
    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)

    # Fetch cart items for this customer, join product info
    cur.execute("""
        SELECT c.id as cart_id, p.id as product_id, p.product_name, p.quantity, p.price, p.image
        FROM cart c
        JOIN products p ON c.product_id = p.id
        WHERE customer_id = %s
        ORDER BY c.created_at DESC
    """, (cid,))
    items = cur.fetchall()

    # Calculate total price
    total = sum(item['price'] for item in items) if items else 0.0

    return render_template('customer/cart.html', items=items, total=round(total,2))


# REMOVE FROM CART
@app.route('/customer/remove_from_cart/<int:cart_id>')
def remove_from_cart(cart_id):
    if 'consumer_id' not in session:
        return redirect(url_for('consumer_login'))

    cid = session['consumer_id']
    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)

    # Ensure the cart row belongs to this customer
    cur.execute("SELECT * FROM cart WHERE id=%s AND customer_id=%s", (cart_id, cid))
    row = cur.fetchone()
    if not row:
        return redirect(url_for('customer_cart'))

    cur.execute("DELETE FROM cart WHERE id=%s", (cart_id,))
    conn.commit()

    return redirect(url_for('customer_cart', msg='removed'))


# CHECKOUT / PAYMENT page (GET shows form, POST processes payment)
@app.route('/customer/checkout', methods=['GET', 'POST'])
def customer_checkout():
    if 'consumer_id' not in session:
        return redirect(url_for('consumer_login'))

    cid = session['consumer_id']
    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)

    # Fetch cart items
    cur.execute("""
        SELECT c.id as cart_id, p.id as product_id, p.product_name, p.price
        FROM cart c
        JOIN products p ON c.product_id = p.id
        WHERE c.customer_id = %s
    """, (cid,))
    items = cur.fetchall()

    if not items:
        return redirect(url_for('customer_cart'))

    total = round(sum(item['price'] for item in items), 2)

    if request.method == 'POST':
        payment_type = request.form.get('payment_type')  # 'card' or 'upi'
        # For card: card_name, card_number, card_cvv, card_expiry
        # For upi: upi_id
        # NOTE: this is dummy; do not store raw card info in production.
        try:
            # Save each purchased product as a row in purchases
            for it in items:
                cur.execute("""
                    INSERT INTO purchases (customer_id, product_id, price)
                    VALUES (%s, %s, %s)
                """, (cid, it['product_id'], it['price']))

            # Remove these items from cart
            cur.execute("DELETE FROM cart WHERE customer_id=%s", (cid,))
            conn.commit()
            
            cur.execute("DELETE FROM products WHERE id=%s", (it['product_id'],))
            conn.commit()

            # Render processing page then success
            return render_template('customer/payment_result.html',
                                   status='success',
                                   total=total,
                                   payment_type=payment_type,
                                   items=items)
        except Exception as e:
            print("Checkout Error:", e)
            return render_template('customer/payment_result.html',
                                   status='error',
                                   error=str(e))

    # GET
    return render_template('customer/checkout.html', items=items, total=total)

@app.route('/customer/my_purchases')
def customer_my_purchases():
    if 'consumer_id' not in session:
        return redirect('/customer_login')

    cid = session['consumer_id']
    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)

    # Fetch purchases joined with product details
    cur.execute("""
        SELECT p.product_name, p.image, pur.price, pur.created_at
        FROM purchases pur
        JOIN products p ON pur.product_id = p.id
        WHERE pur.customer_id = %s
        ORDER BY pur.created_at DESC
    """, (cid,))
    
    purchases = cur.fetchall()

    return render_template("customer/my_purchases.html", purchases=purchases)


if __name__ == "__main__":
    app.run(debug=True)
