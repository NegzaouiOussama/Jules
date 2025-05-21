// Sample Product Data
const products = [
    { id: 1, name: "T-Shirt Classique", image: "https://via.placeholder.com/150/FF0000/FFFFFF?Text=TShirt1", price: 20.00 },
    { id: 2, name: "Jean Slim", image: "https://via.placeholder.com/150/0000FF/FFFFFF?Text=Jean2", price: 55.50 },
    { id: 3, name: "Baskets Mode", image: "https://via.placeholder.com/150/00FF00/FFFFFF?Text=Baskets3", price: 78.90 },
    { id: 4, name: "Casquette Logo", image: "https://via.placeholder.com/150/FFFF00/000000?Text=Casquette4", price: 15.25 }
];

// Cart
let cart = [];

// --- Cart Functions ---
function loadCart() {
    const cartData = localStorage.getItem('shoppingCart');
    if (cartData) {
        cart = JSON.parse(cartData);
    }
    console.log("Cart loaded:", cart);
}

function saveCart() {
    localStorage.setItem('shoppingCart', JSON.stringify(cart));
    console.log("Cart saved:", cart);
}

function addToCart(productId) {
    const productIdNum = parseInt(productId);
    const productToAdd = products.find(p => p.id === productIdNum);

    if (!productToAdd) {
        console.error("Product not found:", productIdNum);
        return;
    }

    const cartItem = cart.find(item => item.id === productIdNum);

    if (cartItem) {
        cartItem.quantity += 1;
    } else {
        cart.push({ ...productToAdd, quantity: 1 });
    }

    saveCart();
    alert(`${productToAdd.name} a été ajouté au panier!`);
}

// --- Product Display Functions (index.html) ---
function displayProducts() {
    const productListContainer = document.querySelector('.product-list');
    if (!productListContainer) {
        return; // Not on the product page or container not found
    }

    productListContainer.innerHTML = ''; // Clear placeholder or existing products

    products.forEach(product => {
        const productCardHTML = `
            <article class="product-card" data-product-id="${product.id}">
                <h2>${product.name}</h2>
                <img src="${product.image}" alt="${product.name}">
                <p>Prix: €${product.price.toFixed(2)}</p>
                <button class="add-to-cart-btn" data-id="${product.id}">Ajouter au panier</button>
            </article>
        `;
        productListContainer.innerHTML += productCardHTML;
    });
}

// --- Cart Display Functions (cart.html) ---
function displayCartItems() {
    const cartItemsContainer = document.querySelector('.cart-items');
    if (!cartItemsContainer) {
        return; // Not on the cart page or container not found
    }

    // The first child of cart-items is <h2>, preserve it. Clear previous items.
    const h2Element = cartItemsContainer.querySelector('h2');
    cartItemsContainer.innerHTML = ''; // Clear everything
    if (h2Element) {
        cartItemsContainer.appendChild(h2Element); // Add back the h2
    }


    if (cart.length === 0) {
        cartItemsContainer.innerHTML += '<p>Votre panier est vide.</p>'; // Append message after h2
    } else {
        cart.forEach(item => {
            const cartItemHTML = `
                <article class="cart-item" data-product-id="${item.id}">
                    <span class="product-name">${item.name}</span>
                    <span class="product-price">€${item.price.toFixed(2)}</span>
                    <span class="product-quantity">Quantité: ${item.quantity}</span>
                </article>
            `;
            cartItemsContainer.innerHTML += cartItemHTML;
        });
    }
}

function updateCartTotal() {
    const cartTotalElement = document.querySelector('.cart-total p'); // Targets the <p> inside .cart-total
    if (!cartTotalElement) {
        return; // Not on the cart page or element not found
    }

    let total = 0;
    if (cart.length > 0) {
        total = cart.reduce((sum, item) => sum + (item.price * item.quantity), 0);
    }
    
    cartTotalElement.textContent = `Total: €${total.toFixed(2)}`;
}


// --- Event Listeners ---
function setupEventListeners() {
    // Event delegation for "Add to Cart" buttons on the product page
    const productListContainer = document.querySelector('.product-list');
    if (productListContainer) {
        productListContainer.addEventListener('click', function(event) {
            if (event.target.classList.contains('add-to-cart-btn')) {
                const productId = event.target.dataset.id;
                addToCart(productId);
            }
        });
    }

    // Event listener for "Validate Order" button on the cart page
    const validateOrderButton = document.getElementById('validate-order');
    if (validateOrderButton) {
        validateOrderButton.addEventListener('click', () => {
            alert('Commande validée! (Simulation)');
            cart = []; // Clear the cart array
            saveCart(); // Clear cart in localStorage
            displayCartItems(); // Update the displayed cart items
            updateCartTotal(); // Update the displayed total
        });
    }
}


// --- Initial Load ---
document.addEventListener('DOMContentLoaded', () => {
    loadCart(); // Load cart from localStorage first

    // Page-specific logic
    if (document.querySelector('.product-list')) { // Check if we are on index.html
        displayProducts();
    }
    
    if (document.querySelector('.cart-items')) { // Check if we are on cart.html
        displayCartItems();
        updateCartTotal();
    }

    setupEventListeners(); // Setup all event listeners after DOM is ready
});
