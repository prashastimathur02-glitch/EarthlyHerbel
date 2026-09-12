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
                password_hash,
                is_admin
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
    row[2],
    row[4]
)

    login_user(user)
    if user.is_admin:
        return redirect(url_for("main.admin_dashboard"))
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
# =========================================================
# ADMIN DASHBOARD
# =========================================================

# =========================================================
# ADMIN DASHBOARD
# =========================================================

@main.route("/admin")
@login_required
def admin_dashboard():

    if not current_user.is_admin:
        return "Access denied", 403

    connection = get_db_connection()

    try:

        with connection.cursor() as cursor:

            # -------------------------------------------------
            # Products
            # -------------------------------------------------

            cursor.execute(
                """
                SELECT
                    id,
                    name,
                    category,
                    price,
                    original_price,
                    rating,
                    stock
                FROM products
                ORDER BY id DESC
                """
            )

            product_rows = cursor.fetchall()


            # -------------------------------------------------
            # Customers
            # -------------------------------------------------

            cursor.execute(
                """
                SELECT COUNT(*)
                FROM customers
                """
            )

            customer_count = cursor.fetchone()[0]


            # -------------------------------------------------
            # Orders
            # -------------------------------------------------

            cursor.execute(
                """
                SELECT
                    o.id,
                    c.name,
                    c.email,
                    o.total_amount,
                    o.status,
                    o.created_at
                FROM orders o
                JOIN customers c
                    ON o.customer_id = c.id
                ORDER BY o.created_at DESC
                """
            )

            orders = cursor.fetchall()


            # -------------------------------------------------
            # Order Count
            # -------------------------------------------------

            cursor.execute(
                """
                SELECT COUNT(*)
                FROM orders
                """
            )

            order_count = cursor.fetchone()[0]


            # -------------------------------------------------
            # Revenue
            # -------------------------------------------------

            cursor.execute(
                """
                SELECT COALESCE(
                    SUM(total_amount),
                    0
                )
                FROM orders
                WHERE status != 'Cancelled'
                """
            )

            revenue = cursor.fetchone()[0]


            # -------------------------------------------------
            # Low Stock Count
            # -------------------------------------------------

            cursor.execute(
                """
                SELECT COUNT(*)
                FROM products
                WHERE stock <= 5
                """
            )

            low_stock_count = cursor.fetchone()[0]


    finally:
        connection.close()


    # ---------------------------------------------------------
    # Convert product rows into dictionaries
    # ---------------------------------------------------------

    products = []

    for row in product_rows:

        products.append({

            "id": row[0],

            "name": row[1],

            "category": row[2],

            "price": float(row[3]),

            "original_price": float(row[4]),

            "rating": float(row[5]),

            "stock": row[6]

        })


    return render_template(

        "admin.html",

        products=products,

        orders=orders,

        customer_count=customer_count,

        order_count=order_count,

        revenue=float(revenue),

        low_stock_count=low_stock_count

    )

# =========================================================
# ADMIN - UPDATE ORDER STATUS
# =========================================================

@main.route(
    "/admin/orders/<int:order_id>/status",
    methods=["POST"]
)
@login_required
def admin_update_order_status(order_id):

    # Only admin users can update order status
    if not current_user.is_admin:
        return "Access denied", 403

    status = request.form.get("status", "").strip()

    allowed_statuses = [
        "Pending",
        "Confirmed",
        "Packed",
        "Shipped",
        "Delivered",
        "Cancelled"
    ]

    if status not in allowed_statuses:
        return "Invalid order status", 400

    connection = get_db_connection()

    try:

        with connection.cursor() as cursor:

            cursor.execute(
                """
                UPDATE orders
                SET status = %s
                WHERE id = %s
                """,
                (
                    status,
                    order_id
                )
            )

            if cursor.rowcount != 1:
                connection.rollback()
                return "Order not found", 404

        connection.commit()

    except Exception as error:

        connection.rollback()

        print(
            "Order status update error:",
            error
        )

        return "Unable to update order status", 500

    finally:
        connection.close()

    return redirect(
        url_for("main.admin_dashboard")
    )
# =========================================================
# ADMIN - ADD PRODUCT
# =========================================================

@main.route("/admin/products/add", methods=["GET", "POST"])
@login_required
def admin_add_product():

    if not current_user.is_admin:
        return "Access denied", 403

    if request.method == "GET":

        return render_template(
            "admin_add_product.html"
        )

    name = request.form.get("name", "").strip()
    category = request.form.get("category", "").strip()
    price = request.form.get("price", "0")
    original_price = request.form.get("original_price", "0")
    rating = request.form.get("rating", "0")
    stock = request.form.get("stock", "0")
    description = request.form.get("description", "").strip()
    ingredients = request.form.get("ingredients", "").strip()
    benefits = request.form.get("benefits", "").strip()
    how_to_use = request.form.get("how_to_use", "").strip()

    if not name or not category or not description:
        return "Please fill all required fields", 400

    connection = get_db_connection()

    try:

        with connection.cursor() as cursor:

            cursor.execute(
                """
                INSERT INTO products
                (
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
                )
                VALUES
                (
                    %s, %s, %s, %s, %s,
                    %s, %s, %s, %s, %s
                )
                """,
                (
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
                )
            )

        connection.commit()

    except Exception as error:

        connection.rollback()

        print("Add product error:", error)

        return f"Database error: {error}", 500

    finally:
        connection.close()

    return redirect(
        url_for("main.admin_dashboard")
    )


# =========================================================
# ADMIN - EDIT PRODUCT
# =========================================================

@main.route(
    "/admin/products/edit/<int:product_id>",
    methods=["GET", "POST"]
)
@login_required
def admin_edit_product(product_id):

    if not current_user.is_admin:
        return "Access denied", 403

    connection = get_db_connection()

    try:

        with connection.cursor() as cursor:

            if request.method == "GET":

                cursor.execute(
                    """
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
                    """,
                    (product_id,)
                )

                product = cursor.fetchone()

                if product is None:
                    return "Product not found", 404

                return render_template(
                    "admin_edit_product.html",
                    product=product
                )


            name = request.form.get("name", "").strip()
            category = request.form.get("category", "").strip()
            price = request.form.get("price", "0")
            original_price = request.form.get(
                "original_price",
                "0"
            )
            rating = request.form.get(
                "rating",
                "0"
            )
            stock = request.form.get(
                "stock",
                "0"
            )
            description = request.form.get(
                "description",
                ""
            ).strip()
            ingredients = request.form.get(
                "ingredients",
                ""
            ).strip()
            benefits = request.form.get(
                "benefits",
                ""
            ).strip()
            how_to_use = request.form.get(
                "how_to_use",
                ""
            ).strip()

            if not name or not category or not description:
                return "Please fill all required fields", 400

            cursor.execute(
                """
                UPDATE products
                SET
                    name = %s,
                    category = %s,
                    price = %s,
                    original_price = %s,
                    rating = %s,
                    stock = %s,
                    description = %s,
                    ingredients = %s,
                    benefits = %s,
                    how_to_use = %s
                WHERE id = %s
                """,
                (
                    name,
                    category,
                    price,
                    original_price,
                    rating,
                    stock,
                    description,
                    ingredients,
                    benefits,
                    how_to_use,
                    product_id
                )
            )

            if cursor.rowcount != 1:
                connection.rollback()
                return "Product not found", 404

        connection.commit()

    except Exception as error:

        connection.rollback()

        print("Edit product error:", error)

        return f"Database error: {error}", 500

    finally:
        connection.close()

    return redirect(
        url_for("main.admin_dashboard")
    )
# =========================================================
# ADMIN - DELETE PRODUCT
# =========================================================

@main.route(
    "/admin/products/delete/<int:product_id>",
    methods=["POST"]
)
@login_required
def admin_delete_product(product_id):

    if not current_user.is_admin:
        return "Access denied", 403

    connection = get_db_connection()

    try:

        with connection.cursor() as cursor:

            # Check whether the product has been used in any order
            cursor.execute(
                """
                SELECT 1
                FROM order_items
                WHERE product_id = %s
                LIMIT 1
                """,
                (product_id,)
            )

            existing_order_item = cursor.fetchone()

            if existing_order_item:

                connection.rollback()

                return (
                    "This product cannot be deleted because "
                    "it already exists in an order.",
                    400
                )

            # Delete the product
            cursor.execute(
                """
                DELETE FROM products
                WHERE id = %s
                """,
                (product_id,)
            )

            if cursor.rowcount != 1:

                connection.rollback()

                return "Product not found", 404

        connection.commit()

    except Exception as error:

        connection.rollback()

        print(
            "Delete product error:",
            error
        )

        return "Unable to delete product", 500

    finally:
        connection.close()

    return redirect(
        url_for("main.admin_dashboard")
    )