from flask import Blueprint, render_template

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