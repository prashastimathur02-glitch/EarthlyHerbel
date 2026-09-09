from flask import Blueprint, render_template, request, jsonify, redirect, url_for

from werkzeug.security import generate_password_hash, check_password_hash

from flask_login import (
    login_user,
    logout_user,
    login_required,
    current_user
)

from app.database import get_db_connection
from app import User


main = Blueprint("main", __name__)


@main.route("/")
def home():
    return render_template("index.html")


@main.route("/shop")
def shop():

    connection = get_db_connection()

    try:
        with connection.cursor() as cursor:

            cursor.execute("""
                SELECT
                    id,
                    name,
                    category,
                    price,
                    original_price,
                    rating,
                    stock,
                    description,
                    ingredients,
                    benefits,
                    how_to_use
                FROM products
                ORDER BY id
            """)

            rows = cursor.fetchall()

    finally:
        connection.close()

    products = []

    for row in rows:
        products.append({
            "id": row[0],
            "name": row[1],
            "category": row[2],
            "price": float(row[3]),
            "original_price": float(row[4]),
            "rating": float(row[5]),
            "stock": row[6],
            "description": row[7],
            "ingredients": row[8],
            "benefits": row[9].split(" | ") if row[9] else [],
            "how_to_use": row[10]
        })

    return render_template(
        "shop.html",
        products=products
    )


@main.route("/cart")
def cart():
    return render_template("cart.html")


@main.route("/checkout")
def checkout():
    return render_template("checkout.html")


@main.route("/product/<int:product_id>")
def product_detail(product_id):

    connection = get_db_connection()

    try:
        with connection.cursor() as cursor:

            cursor.execute("""
                SELECT
                    id,
                    name,
                    category,
                    price,
                    original_price,
                    rating,
                    stock,
                    description,
                    ingredients,
                    benefits,
                    how_to_use
                FROM products
                WHERE id = %s
            """, (product_id,))

            row = cursor.fetchone()

    finally:
        connection.close()

    if row is None:
        return "Product not found", 404

    product = {
        "id": row[0],
        "name": row[1],
        "category": row[2],
        "price": float(row[3]),
        "original_price": float(row[4]),
        "rating": float(row[5]),
        "stock": row[6],
        "description": row[7],
        "ingredients": row[8],
        "benefits": row[9].split(" | ") if row[9] else [],
        "how_to_use": row[10]
    }

    discount = round(
        (
            (product["original_price"] - product["price"])
            / product["original_price"]
        ) * 100
    )

    return render_template(
        "product.html",
        product=product,
        discount=discount
    )


@main.route("/register", methods=["GET", "POST"])
@main.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "GET":
        return render_template("register.html")

    name = request.form.get("name", "").strip()
    email = request.form.get("email", "").strip().lower()
    phone = request.form.get("phone", "").strip()
    password = request.form.get("password", "")

    if not name or not email or not password:
        return render_template(
            "register.html",
            error="Name, email and password are required."
        )

    if len(password) < 8:
        return render_template(
            "register.html",
            error="Password must be at least 8 characters."
        )

    password_hash = generate_password_hash(password)

    connection = get_db_connection()

    try:

        with connection.cursor() as cursor:

            cursor.execute(
                """
                SELECT id, password_hash
                FROM customers
                WHERE email = %s
                """,
                (email,)
            )

            existing_customer = cursor.fetchone()

            if existing_customer:

                customer_id = existing_customer[0]
                existing_password_hash = existing_customer[1]

                if existing_password_hash:
                    return render_template(
                        "register.html",
                        error="An account with this email already exists."
                    )

                cursor.execute(
                    """
                    UPDATE customers
                    SET
                        name = %s,
                        phone = %s,
                        password_hash = %s
                    WHERE id = %s
                    """,
                    (
                        name,
                        phone,
                        password_hash,
                        customer_id
                    )
                )

            else:

                cursor.execute(
                    """
                    INSERT INTO customers
                        (name, email, phone, password_hash)
                    VALUES
                        (%s, %s, %s, %s)
                    RETURNING id
                    """,
                    (
                        name,
                        email,
                        phone,
                        password_hash
                    )
                )

                customer_id = cursor.fetchone()[0]

        connection.commit()

    except Exception as error:

        connection.rollback()

        print("Registration error:", error)

        return render_template(
            "register.html",
            error="Unable to create account right now."
        )

    finally:
        connection.close()

    user = User(
        customer_id,
        name,
        email
    )

    login_user(user)

    return redirect(url_for("main.account"))

@main.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "GET":
        return render_template("login.html")

    email = request.form.get("email", "").strip().lower()
    password = request.form.get("password", "")

    if not email or not password:
        return render_template(
            "login.html",
            error="Email and password are required."
        )

    connection = get_db_connection()

    try:

        with connection.cursor() as cursor:

            cursor.execute(
                """
                SELECT
                    id,
                    name,
                    email,
                    password_hash
                FROM customers
                WHERE email = %s
                """,
                (email,)
            )

            row = cursor.fetchone()

    finally:
        connection.close()

    if row is None or not row[3]:

        return render_template(
            "login.html",
            error="Invalid email or password."
        )

    if not check_password_hash(row[3], password):

        return render_template(
            "login.html",
            error="Invalid email or password."
        )

    user = User(
        row[0],
        row[1],
        row[2]
    )

    login_user(user)

    return redirect(url_for("main.account"))


@main.route("/logout")
@login_required
def logout():

    logout_user()

    return redirect(url_for("main.home"))


@main.route("/account")
@login_required
def account():

    connection = get_db_connection()

    try:

        with connection.cursor() as cursor:

            cursor.execute(
                """
                SELECT
                    id,
                    total_amount,
                    status,
                    shipping_address,
                    created_at
                FROM orders
                WHERE customer_id = %s
                ORDER BY created_at DESC
                """,
                (int(current_user.id),)
            )

            rows = cursor.fetchall()

    finally:
        connection.close()

    orders = []

    for row in rows:

        orders.append({
            "id": row[0],
            "total_amount": float(row[1]),
            "status": row[2],
            "shipping_address": row[3],
            "created_at": row[4]
        })

    return render_template(
        "account.html",
        orders=orders
    )


@main.route("/api/orders", methods=["POST"])
def create_order():

    data = request.get_json(silent=True) or {}

    name = data.get("name", "").strip()
    email = data.get("email", "").strip().lower()
    phone = data.get("phone", "").strip()
    address = data.get("address", "").strip()
    items = data.get("items", [])

    if not name or not email or not phone or not address:

        return jsonify({
            "success": False,
            "message": "All customer details are required."
        }), 400

    if not isinstance(items, list) or not items:

        return jsonify({
            "success": False,
            "message": "Your cart is empty."
        }), 400

    requested_items = {}

    try:

        for item in items:

            product_id = int(item["id"])
            quantity = int(item["quantity"])

            if quantity <= 0:
                raise ValueError

            requested_items[product_id] = (
                requested_items.get(product_id, 0) + quantity
            )

    except (KeyError, TypeError, ValueError):

        return jsonify({
            "success": False,
            "message": "Invalid cart items."
        }), 400

    connection = get_db_connection()

    try:

        with connection.cursor() as cursor:

            product_ids = list(requested_items.keys())

            cursor.execute(
                """
                SELECT
                    id,
                    name,
                    price,
                    stock
                FROM products
                WHERE id = ANY(%s)
                FOR UPDATE
                """,
                (product_ids,)
            )

            rows = cursor.fetchall()

            products_by_id = {
                row[0]: {
                    "name": row[1],
                    "price": float(row[2]),
                    "stock": row[3]
                }
                for row in rows
            }

            for product_id in product_ids:

                if product_id not in products_by_id:

                    return jsonify({
                        "success": False,
                        "message": "One or more products are unavailable."
                    }), 400

            subtotal = 0
            order_items = []

            for product_id, quantity in requested_items.items():

                product = products_by_id[product_id]

                if quantity > product["stock"]:

                    return jsonify({
                        "success": False,
                        "message": (
                            f"Only {product['stock']} "
                            f"unit(s) of {product['name']} "
                            f"are available."
                        )
                    }), 400

                unit_price = product["price"]

                subtotal += unit_price * quantity

                order_items.append({
                    "product_id": product_id,
                    "quantity": quantity,
                    "unit_price": unit_price
                })

            delivery = 0 if subtotal >= 999 else 50
            total = subtotal + delivery

            cursor.execute(
                """
                INSERT INTO customers
                    (name, email, phone)
                VALUES
                    (%s, %s, %s)
                ON CONFLICT (email)
                DO UPDATE SET
                    name = EXCLUDED.name,
                    phone = EXCLUDED.phone
                RETURNING id
                """,
                (
                    name,
                    email,
                    phone
                )
            )

            customer_id = cursor.fetchone()[0]

            cursor.execute(
                """
                INSERT INTO orders
                    (customer_id, total_amount, status, shipping_address)
                VALUES
                    (%s, %s, %s, %s)
                RETURNING id
                """,
                (
                    customer_id,
                    total,
                    "Pending",
                    address
                )
            )

            order_id = cursor.fetchone()[0]

            for item in order_items:

                cursor.execute(
                    """
                    INSERT INTO order_items
                        (order_id, product_id, quantity, unit_price)
                    VALUES
                        (%s, %s, %s, %s)
                    """,
                    (
                        order_id,
                        item["product_id"],
                        item["quantity"],
                        item["unit_price"]
                    )
                )

            for item in order_items:

                cursor.execute(
                    """
                    UPDATE products
                    SET stock = stock - %s
                    WHERE id = %s
                    """,
                    (
                        item["quantity"],
                        item["product_id"]
                    )
                )

        connection.commit()

    except Exception as error:

        connection.rollback()

        print("Order creation failed:", error)

        return jsonify({
            "success": False,
            "message": "Unable to place the order right now."
        }), 500

    finally:
        connection.close()

    return jsonify({
        "success": True,
        "order_id": order_id,
        "total": total
    })


@main.route("/order-success/<int:order_id>")
def order_success(order_id):

    connection = get_db_connection()

    try:

        with connection.cursor() as cursor:

            cursor.execute(
                """
                SELECT
                    o.id,
                    o.total_amount,
                    o.status,
                    o.created_at,
                    c.name
                FROM orders o
                JOIN customers c
                    ON o.customer_id = c.id
                WHERE o.id = %s
                """,
                (order_id,)
            )

            row = cursor.fetchone()

    finally:
        connection.close()

    if row is None:
        return "Order not found", 404

    order = {
        "id": row[0],
        "total_amount": float(row[1]),
        "status": row[2],
        "created_at": row[3]
    }

    customer = {
        "name": row[4]
    }

    return render_template(
        "order_success.html",
        order=order,
        customer=customer
    )