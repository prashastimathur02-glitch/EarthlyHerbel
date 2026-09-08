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