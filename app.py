from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
# from flask_mysqldb import MySQL
import pymysql
from functools import wraps
import uuid

app = Flask(__name__)
app.config['MYSQL_HOST'] = '127.0.0.1'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'password'
app.config['MYSQL_DB'] = 'dragondb'
app.secret_key = '12vl34ad'


def get_db_connection():
    try:
        connection = pymysql.connect(
            host=app.config['MYSQL_HOST'],
            user=app.config['MYSQL_USER'],
            password=app.config['MYSQL_PASSWORD'],
            db=app.config['MYSQL_DB'],
            cursorclass=pymysql.cursors.DictCursor  # Используем DictCursor
        )
        print("Подключение к базе данных успешно установлено")
        return connection
    except Exception as e:
        print(f"Ошибка при подключении к базе данных: {e}")
        return None


@app.route('/')
@app.route('/home')
def index():
    category = request.args.get('category', 'fiction')  # Получаем категорию из запроса, по умолчанию 'fiction'
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            sql = "SELECT * FROM product WHERE category = %s"
            cursor.execute(sql, (category,))
            products = cursor.fetchall()
    finally:
        connection.close()

    return render_template('index.html', products=products, category=category, user=session.get('username'), role=session.get('role'))


@app.route('/add_to_cart/<int:product_id>', methods=['POST'])
def add_to_cart(product_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    if 'cart' not in session:
        session['cart'] = []

    cart = session['cart']
    for item in cart:
        if item['product_id'] == product_id:
            item['quantity'] += 1
            break
    else:
        cart.append({'product_id': product_id, 'quantity': 1})

    session['cart'] = cart
    flash('Товар додано до кошика!', 'success')
    return redirect(url_for('view_cart'))

@app.route('/update_cart', methods=['POST'])
def update_cart():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    product_id = int(request.form['product_id'])
    action = request.form['action']

    cart = session.get('cart', [])
    for item in cart:
        if item['product_id'] == product_id:
            if action == 'increase':
                item['quantity'] += 1
            elif action == 'decrease' and item['quantity'] > 1:
                item['quantity'] -= 1
            break

    session['cart'] = cart
    return redirect(url_for('view_cart'))

@app.route('/remove_from_cart', methods=['POST'])
def remove_from_cart():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    product_id = int(request.form['product_id'])

    cart = session.get('cart', [])
    cart = [item for item in cart if item['product_id'] != product_id]

    session['cart'] = cart
    flash('Товар успішно видалений з кошика.', 'success')
    return redirect(url_for('view_cart'))

@app.route('/cart', methods=['GET', 'POST'])
def view_cart():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    cart = session.get('cart', [])
    if cart:
        connection = get_db_connection()
        try:
            with connection.cursor() as cursor:
                product_ids = [item['product_id'] for item in cart]
                sql = "SELECT * FROM product WHERE id IN ({})".format(', '.join(map(str, product_ids)))
                cursor.execute(sql)
                products = cursor.fetchall()

                cart_products = []
                for product in products:
                    for item in cart:
                        if product['id'] == item['product_id']:
                            product['quantity'] = item['quantity']
                            cart_products.append(product)
                            break
        finally:
            connection.close()
    else:
        cart_products = []

    total_amount = sum(product['price'] * product['quantity'] for product in cart_products)
    return render_template('cart.html', cart_products=cart_products, total_amount=total_amount)


@app.route('/product/<int:product_id>')
def product_detail(product_id):
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            sql = "SELECT * FROM product WHERE id = %s"
            cursor.execute(sql, (product_id,))
            product = cursor.fetchone()
    finally:
        connection.close()

    if product:
        return jsonify(product)
    else:
        return jsonify({'error': 'Product not found'}), 404


@app.route('/check_cart_availability', methods=['POST'])
def check_cart_availability():
    if 'user_id' not in session:
        return jsonify({'error': 'User not logged in'}), 403

    cart = session.get('cart', [])
    if not cart:
        return jsonify({'error': 'Cart is empty'}), 400

    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            product_ids = [item['product_id'] for item in cart]
            sql = "SELECT id, name, quantity FROM product WHERE id IN ({})".format(', '.join(map(str, product_ids)))
            cursor.execute(sql)
            products = cursor.fetchall()
    finally:
        connection.close()

    insufficient_products = []
    for item in cart:
        for product in products:
            if product['id'] == item['product_id'] and product['quantity'] < item['quantity']:
                insufficient_products.append({
                    'name': product['name'],
                    'available': product['quantity'],
                    'requested': item['quantity']
                })

    if insufficient_products:
        return jsonify({'error': 'Insufficient stock', 'products': insufficient_products}), 400

    return jsonify({'success': 'Stock is sufficient'}), 200

@app.route('/place_order', methods=['POST'])
def place_order():
    if 'user_id' not in session:
        return jsonify(success=False, message='Треба увійти до системи')

    user_id = session['user_id']
    cart = session.get('cart', [])
    if not cart:
        return jsonify(success=False, message='Корзина пуста!')

    name = request.form.get('name')
    email = request.form.get('email')
    phone = request.form.get('phone')
    delivery_format = request.form.get('format')
    delivery_service = request.form.get('delivery-service')
    delivery_city = request.form.get('city')
    delivery_office = request.form.get('office')

    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            # Check if order already exists with the same details
            sql = "SELECT id FROM `order` WHERE details = %s AND client_id = %s"
            details = f"Замовлення від {name}, тел: {phone}, email: {email}"
            cursor.execute(sql, (details, user_id))
            existing_order = cursor.fetchone()
            if existing_order:
                order_id = existing_order['id']
            else:
                # Insert into order table
                sql = "INSERT INTO `order` (updated, details, status_id, client_id) VALUES (NOW(), %s, 1, %s)"
                cursor.execute(sql, (details, user_id))
                order_id = cursor.lastrowid

            # Insert into product_cart table
            order_details = []
            for item in cart:
                order_details.append((item['quantity'], item['product_id'], order_id))

                # Update product quantity
                sql = "UPDATE product SET quantity = quantity - %s WHERE id = %s"
                cursor.execute(sql, (item['quantity'], item['product_id']))

            sql = "INSERT INTO product_cart (quantity, product_id, order_id) VALUES (%s, %s, %s)"
            cursor.executemany(sql, order_details)

            # Insert into delivery table if delivery is chosen
            if delivery_format == 'delivery':
                sql = "INSERT INTO delivery (name_sity, order_id, Number_Pochta, Type_Pochta) VALUES (%s, %s, %s, %s)"
                cursor.execute(sql, (delivery_city, order_id, delivery_office, delivery_service))

            # Update user details
            sql = "UPDATE client SET first_name = %s, last_name = %s, telephon = %s WHERE id = %s"
            cursor.execute(sql, (name.split()[0], name.split()[1], phone, user_id))

        connection.commit()
        session.pop('cart', None)
        return jsonify(success=True, message='Замовлення успішно оформлено!', order_id=order_id)
    finally:
        connection.close()


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        role = 'user'  # По умолчанию роль user

        if password == confirm_password:
            conn = get_db_connection()
            if conn:
                cursor = conn.cursor()
                cursor.execute('INSERT INTO client (login, password, email, first_name, last_name, telephon, role) VALUES (%s, %s, %s, %s, %s, %s, %s)',
                               (username, password, email, 'first_name', 'last_name', 'telephon', role))
                conn.commit()
                conn.close()
                return redirect(url_for('login'))
            else:
                return "Ошибка подключения к базе данных"
        else:
            return "Passwords do not match"
    return render_template('login.html')

# Декоратор для проверки аутентификации пользователя
def login_required(role=None):
    def wrapper(fn):
        @wraps(fn)
        def decorated_view(*args, **kwargs):
            if 'username' not in session:
                return redirect(url_for('login'))
            if role and session.get('role') != role:
                return redirect(url_for('unauthorized'))
            return fn(*args, **kwargs)
        return decorated_view
    return wrapper

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        connection = get_db_connection()
        try:
            with connection.cursor() as cursor:
                # Запрос для получения данных пользователя
                sql = "SELECT * FROM client WHERE login=%s AND password=%s"
                cursor.execute(sql, (username, password))
                user = cursor.fetchone()

                if user:
                    session['username'] = user['login']
                    session['role'] = user['role']
                    session['user_id'] = user['id']
                    session['cart'] = []
                    if user['role'] == 'admin':
                        return redirect(url_for('index'))
                    elif user['role'] == 'user':
                        return redirect(url_for('index'))
                else:
                    return "Invalid credentials"
        finally:
            connection.close()
    return render_template('login.html')


#@app.route('/admin_dashboard')
#@login_required('admin')
#def admin_dashboard():
#   return render_template('index.html', user=session.get('username'), role=session.get('role'))

#@app.route('/user_dashboard')
#@login_required('user')
#def user_dashboard():
#   return render_template('index.html', user=session.get('username'), role=session.get('role'))

#@app.route('/unauthorized')
#def unauthorized():
#    return render_template('unauthorized.html')

@app.route('/logout')
def logout():
    session.pop('username', None)
    session.pop('role', None)
    session.pop('user_id', None)
    session.pop('cart', None)  # Очищаем корзину при выходе
    return redirect(url_for('login'))

@app.context_processor
def inject_user():
    return dict(user=session.get('username'), role=session.get('role'))

@app.route('/add-product')
def add_product():
    return render_template("add-product.html")

@app.route('/add_item', methods=['POST'])
def add_item():
    if request.method == 'POST':
        name = request.form['name']
        author = request.form['author']
        genre = request.form['genre']
        page_count = request.form['page_count']
        category = request.form['category']
        publisher = request.form['publisher']
        publication_year = request.form['publication_year']
        cover_type = request.form['cover_type']
        format = request.form['format']
        language = request.form['language']
        stock_amount = request.form['stock_amount']
        isbn = request.form['isbn']
        price = request.form['price']
        description = request.form['description']
        img = request.files['img']
        # Сохраняем изображение на сервере
        img_filename = img.filename
        img.save(f'static/img/books/{img_filename}')
        connection = get_db_connection()
        try:
            with connection.cursor() as cursor:
                sql = """
                INSERT INTO product (name, price, img, quantity, description, pages, genre, category, publisher, year, format, cover, language, isbn, author)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """
                cursor.execute(sql, (name, price, img_filename, stock_amount, description, page_count, genre, category, publisher, publication_year, format, cover_type, language, isbn, author))
                connection.commit()
        finally:
            connection.close()
        return redirect(url_for('add_product'))


@app.route('/add-new-admin')
def add_new_admin():
    return render_template("add-new-admin.html")

@app.route('/search-user', methods=['POST'])
def search_user():
    id_or_username = request.form.get('id_or_username')
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            sql = "SELECT id, username, email, role FROM users WHERE id = %s OR username = %s"
            cursor.execute(sql, (id_or_username, id_or_username))
            user = cursor.fetchone()
            if user:
                return jsonify(success=True, user=user)
            else:
                return jsonify(success=False)
    finally:
        connection.close()

@app.route('/change-role', methods=['POST'])
def change_role():
    data = request.get_json()
    user_id = data['user_id']
    new_role = data['role']
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            sql = "UPDATE users SET role = %s WHERE id = %s"
            cursor.execute(sql, (new_role, user_id))
        connection.commit()
        return jsonify(success=True)
    finally:
        connection.close()


@app.route('/profile')
def profile():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user_id = session['user_id']
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            # Get user details
            sql = "SELECT first_name, last_name, email FROM client WHERE id = %s"
            cursor.execute(sql, (user_id,))
            user = cursor.fetchone()

            # Get user orders and corresponding products
            sql = """
                SELECT o.id as order_id, o.updated as order_date, o.status_id, s.name as status_name, 
                       pc.quantity, p.name as product_name, p.author, p.price, p.img
                FROM `order` o
                JOIN product_cart pc ON o.id = pc.order_id
                JOIN product p ON pc.product_id = p.id
                JOIN status s ON o.status_id = s.id
                WHERE o.client_id = %s
                ORDER BY o.updated DESC
            """
            cursor.execute(sql, (user_id,))
            orders = cursor.fetchall()

            # Organize orders by order_id
            organized_orders = {}
            for order in orders:
                if order['order_id'] not in organized_orders:
                    organized_orders[order['order_id']] = {
                        'order_id': order['order_id'],
                        'order_date': order['order_date'],
                        'status_id': order['status_id'],
                        'status_name': order['status_name'],
                        'books': [],
                        'total_price': 0
                    }
                organized_orders[order['order_id']]['books'].append({
                    'name': order['product_name'],
                    'author': order['author'],
                    'quantity': order['quantity'],
                    'price': order['price'],
                    'img': order['img']
                })
                organized_orders[order['order_id']]['total_price'] += order['price'] * order['quantity']

            organized_orders = list(organized_orders.values())

        return render_template("profile.html", user=user, orders=organized_orders)
    finally:
        connection.close()


@app.route('/pay_order', methods=['POST'])
def pay_order():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'User not logged in'})

    data = request.json
    order_id = data.get('order_id')
    user_id = session['user_id']

    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            # Check if the order belongs to the user and its current status
            sql = "SELECT status_id FROM `order` WHERE id = %s AND client_id = %s"
            cursor.execute(sql, (order_id, user_id))
            order = cursor.fetchone()

            if not order:
                return jsonify({'success': False, 'message': 'Order not found or does not belong to user'})

            if order['status_id'] in [2, 5, 6]:
                return jsonify({'success': False, 'message': 'Order status does not allow payment'})

            # Update the status of the order to 'paid'
            sql = "UPDATE `order` SET status_id = 2 WHERE id = %s"
            cursor.execute(sql, (order_id,))

        connection.commit()
        return jsonify({'success': True})
    finally:
        connection.close()


# Маршрут для страницы управления заказами администратора
@app.route('/admin/orders')
def admin_orders():
   # if session.get('user_type') != 'admin':
    #    return redirect(url_for('login'))

    connection = get_db_connection()
    orders = []  # Определение переменной orders перед блоком try

    try:
        with connection.cursor() as cursor:
            status_filter = request.args.get('status', 'all')
            # Получение статуса для сортировки
            #status_filter = request.args.get('status')

            # Формирование SQL-запроса в зависимости от выбранного статуса
            if status_filter == 'all':
                sql = """
                    SELECT DISTINCT o.id as order_id, o.updated as order_date, o.status_id, s.name as status_name,
                                    c.first_name, c.last_name
                    FROM `order` o
                    JOIN client c ON o.client_id = c.id
                    JOIN status s ON o.status_id = s.id
                    ORDER BY o.updated DESC
                """
                cursor.execute(sql)
                orders = cursor.fetchall()
            else:
                sql = """
                    SELECT DISTINCT o.id as order_id, o.updated as order_date, o.status_id, s.name as status_name,
                                    c.first_name, c.last_name
                    FROM `order` o
                    JOIN client c ON o.client_id = c.id
                    JOIN status s ON o.status_id = s.id
                    WHERE o.status_id = %s
                    ORDER BY o.updated DESC
                """
                cursor.execute(sql, (status_filter,))
                orders = cursor.fetchall()

            # Для каждого заказа получаем все книги, относящиеся к этому заказу
            for order in orders:
                sql_books = """
                    SELECT pc.quantity, p.name as product_name, p.author, p.price, p.img
                    FROM product_cart pc
                    JOIN product p ON pc.product_id = p.id
                    WHERE pc.order_id = %s
                """
                cursor.execute(sql_books, (order['order_id'],))
                order['books'] = cursor.fetchall()

    finally:
        connection.close()

    return render_template("order-control.html", orders=orders)




# Маршрут для обновления статуса заказа администратором
@app.route('/admin/update_order_status', methods=['POST'])
def update_order_status():
   # if session.get('user_type') != 'admin':
    #    return jsonify({'success': False, 'message': 'Admin not logged in'})

    data = request.json
    order_id = data.get('order_id')
    new_status_id = data.get('status_id')

    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            # Обновление статуса заказа в базе данных
            sql = "UPDATE `order` SET status_id = %s WHERE id = %s"
            cursor.execute(sql, (new_status_id, order_id))

        connection.commit()
        return jsonify({'success': True})
    finally:
        connection.close()



if __name__ == "__main__":
    app.run(debug=True)