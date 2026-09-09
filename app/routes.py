from flask import Blueprint, render_template, request, jsonify

from app.database import get_db_connection


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


@main.route("/api/orders", methods=["POST"])
def create_order():

    data = request.get_json(silent=True) or {}

    name = data.get("name", "").strip()
    email = data.get("email", "").strip()
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
                (name, email, phone)
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
        "total_amount": row[1],
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