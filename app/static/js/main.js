const mobileMenuButton = document.getElementById("mobile-menu-button");
const mobileNav = document.getElementById("mobile-nav");

if (mobileMenuButton && mobileNav) {
    mobileMenuButton.addEventListener("click", () => {
        const isOpen = mobileNav.classList.toggle("active");

        mobileMenuButton.setAttribute(
            "aria-expanded",
            isOpen.toString()
        );

        mobileMenuButton.textContent = isOpen ? "✕" : "☰";
    });
}
// Add product to cart
const addToCartButton = document.getElementById("add-to-cart");

if (addToCartButton) {
    addToCartButton.addEventListener("click", () => {

        const product = {
            id: Number(addToCartButton.dataset.productId),
            name: addToCartButton.dataset.productName,
            price: Number(addToCartButton.dataset.productPrice),
            quantity: 1
        };

        let cart = JSON.parse(localStorage.getItem("earthlyHerbelCart")) || [];

        const existingProduct = cart.find(
            item => item.id === product.id
        );

        if (existingProduct) {
            existingProduct.quantity += 1;
        } else {
            cart.push(product);
        }

        localStorage.setItem(
            "earthlyHerbelCart",
            JSON.stringify(cart)
        );

        alert(`${product.name} added to cart!`);
    });
}
// Update cart count
function updateCartCount() {
    const cart = JSON.parse(
        localStorage.getItem("earthlyHerbelCart")
    ) || [];

    const totalItems = cart.reduce(
        (total, item) => total + item.quantity,
        0
    );

    const cartCount = document.getElementById("cart-count");
    const mobileCartCount = document.getElementById("mobile-cart-count");

    if (cartCount) {
        cartCount.textContent = totalItems;
    }

    if (mobileCartCount) {
        mobileCartCount.textContent = totalItems;
    }
}

updateCartCount();