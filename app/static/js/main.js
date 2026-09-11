// =========================================================
// MOBILE MENU
// =========================================================

const mobileMenuButton =
    document.getElementById("mobile-menu-button");

const mobileNav =
    document.getElementById("mobile-nav");


if (mobileMenuButton && mobileNav) {

    mobileMenuButton.addEventListener("click", () => {

        const isOpen =
            mobileNav.classList.toggle("active");

        mobileMenuButton.setAttribute(
            "aria-expanded",
            isOpen.toString()
        );

        mobileMenuButton.textContent =
            isOpen ? "✕" : "☰";
    });

}


// =========================================================
// ADD PRODUCT TO CART
// =========================================================

const addToCartButton =
    document.getElementById("add-to-cart");


if (addToCartButton) {

    addToCartButton.addEventListener("click", () => {

      const product = {
    id: Number(addToCartButton.dataset.productId),
    name: addToCartButton.dataset.productName,
    price: Number(addToCartButton.dataset.productPrice),
    originalPrice: Number(
        addToCartButton.dataset.productOriginalPrice
    ),
    quantity: getSelectedQuantity()
};


        if (product.quantity < 1) {

            alert("Please select a valid quantity.");

            return;
        }


        let cart =
            JSON.parse(
                localStorage.getItem(
                    "earthlyHerbelCart"
                )
            ) || [];


        const existingProduct =
            cart.find(
                item => item.id === product.id
            );


        if (existingProduct) {

            existingProduct.quantity +=
                product.quantity;

        } else {

            cart.push(product);

        }


        localStorage.setItem(
            "earthlyHerbelCart",
            JSON.stringify(cart)
        );


        updateCartCount();


        alert(
            `${product.name} added to cart!`
        );

    });

}


// =========================================================
// GET SELECTED QUANTITY
// =========================================================

function getSelectedQuantity() {

    const quantityInput =
        document.getElementById("quantity");


    if (!quantityInput) {
        return 1;
    }


    const quantity =
        parseInt(
            quantityInput.value
        );


    if (isNaN(quantity) || quantity < 1) {
        return 1;
    }


    return quantity;

}


// =========================================================
// UPDATE CART COUNT
// =========================================================

function updateCartCount() {

    const cart =
        JSON.parse(
            localStorage.getItem(
                "earthlyHerbelCart"
            )
        ) || [];


    const totalItems =
        cart.reduce(
            (total, item) =>
                total + item.quantity,
            0
        );


    const cartCount =
        document.getElementById(
            "cart-count"
        );


    const mobileCartCount =
        document.getElementById(
            "mobile-cart-count"
        );


    if (cartCount) {

        cartCount.textContent =
            totalItems;

    }


    if (mobileCartCount) {

        mobileCartCount.textContent =
            totalItems;

    }

}


// =========================================================
// INITIAL CART COUNT
// =========================================================

updateCartCount();