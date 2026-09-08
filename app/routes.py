from flask import Blueprint, render_template


main = Blueprint("main", __name__)


products = [
    {
        "id": 1,
        "name": "Herbal Hair Oil",
        "category": "Haircare",
        "price": 499,
        "original_price": 599,
        "rating": 4.8,
        "stock": 12,
        "description": "A nourishing herbal hair oil designed to support a simple and healthy haircare routine.",
        "ingredients": "Coconut Oil, Amla, Bhringraj, Neem, Hibiscus",
        "benefits": [
            "Helps nourish the scalp",
            "Supports softer, healthier-looking hair",
            "Inspired by traditional herbal care"
        ],
        "how_to_use": "Massage gently into the scalp and hair. Leave for a few hours or overnight, then wash."
    },
    {
        "id": 2,
        "name": "Nourishing Hair Mask",
        "category": "Haircare",
        "price": 549,
        "original_price": 649,
        "rating": 4.7,
        "stock": 8,
        "description": "A nourishing hair mask created for a relaxing and restorative haircare ritual.",
        "ingredients": "Aloe Vera, Hibiscus, Fenugreek, Coconut",
        "benefits": [
            "Helps condition hair",
            "Leaves hair feeling soft",
            "Suitable for regular care"
        ],
        "how_to_use": "Apply to clean, damp hair. Leave for 15–20 minutes and rinse thoroughly."
    },
    {
        "id": 3,
        "name": "Botanical Face Oil",
        "category": "Skincare",
        "price": 449,
        "original_price": 499,
        "rating": 4.9,
        "stock": 15,
        "description": "A lightweight botanical face oil for a simple, nourishing skincare ritual.",
        "ingredients": "Jojoba Oil, Rosehip Oil, Almond Oil, Vitamin E",
        "benefits": [
            "Helps moisturize the skin",
            "Leaves skin feeling soft",
            "Lightweight everyday care"
        ],
        "how_to_use": "Apply a few drops to clean skin and gently massage until absorbed."
    },
    {
        "id": 4,
        "name": "Herbal Face Pack",
        "category": "Skincare",
        "price": 299,
        "original_price": 349,
        "rating": 4.6,
        "stock": 20,
        "description": "A botanical face pack inspired by traditional Indian skincare rituals.",
        "ingredients": "Multani Mitti, Neem, Turmeric, Rose Powder",
        "benefits": [
            "Helps refresh the skin",
            "Inspired by traditional care",
            "Simple skincare ritual"
        ],
        "how_to_use": "Mix with water or rose water to form a paste. Apply evenly and rinse when partially dry."
    }
]


@main.route("/")
def home():
    return render_template("index.html")


@main.route("/shop")
def shop():
    return render_template("shop.html", products=products)


@main.route("/product/<int:product_id>")
def product_detail(product_id):

    product = next(
        (product for product in products if product["id"] == product_id),
        None
    )

    if product is None:
        return "Product not found", 404

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