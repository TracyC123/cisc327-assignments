from unittest.mock import patch

# ============================================================
#  Test cases for low-stock notification functionality
# ============================================================

def test_notification_send(client):
    """Test successful low-stock notification to the associated supplier."""

    supplier = create_supplier(client)
    product = create_product(client, supplier["id"], quantity=10, threshold=5)

    # Stub: simulate a successful notification and mock the function call
    with patch(
        "app.routes.transactions.send_notification",
        return_value = True
    ) as mock_send:

        response = create_transaction(client, product["id"], 6, "OUT")

        # Assert application response
        assert response.status_code == 201
        data = response.get_json()
        assert data["notification"] is True

        # Assert application state
        assert get_product(client, product["id"])["quantity_on_hand"] == 4

        # Mock: verify the notification was sent with the correct information
        mock_send.assert_called_once_with(
            "supplier@example.com",
            "Low Stock Alert: Test Product",
            "Test Product is below the threshold of 5. Please replenish the stock."
        )


# ============================================================
#  Test cases for Uncovered Behavior Table
# ============================================================

def test_get_supplier(client):
    """Test retrieving an existing supplier and handling a missing supplier."""

    supplier = create_supplier(client)

    # Test retrieving an existing supplier
    response = client.get(f"/suppliers/{supplier['id']}")

    assert response.status_code == 200
    assert response.get_json()["name"] == "Test Supplier"
    assert response.get_json()["contact_email"] == "supplier@example.com"

    # Test retrieving a supplier that does not exist
    response = client.get("/suppliers/999999")

    assert response.status_code == 404
    assert response.get_json()["error"] == "Supplier not found"


def test_update_supplier(client):
    """Test successfully updating a supplier's name and contact email."""

    supplier = create_supplier(client)

    response = client.put(
        f"/suppliers/{supplier['id']}",
        json={
            "name": "Updated Supplier",
            "contact_email": "updated@example.com",
        },
    )

    assert response.status_code == 200

    data = response.get_json()
    assert data["name"] == "Updated Supplier"
    assert data["contact_email"] == "updated@example.com"

    # Verify the updated supplier is stored
    response = client.get(f"/suppliers/{supplier['id']}")

    assert response.status_code == 200
    assert response.get_json()["name"] == "Updated Supplier"
    assert response.get_json()["contact_email"] == "updated@example.com"

    # Test updating a supplier that does not exist
    response = client.put(
        "/suppliers/999999",
        json={
            "name": "Non Existing Supplier",
            "contact_email": "missing@example.com",
        },
    )

    assert response.status_code == 404
    assert response.get_json()["error"] == "Supplier not found"


def test_supplier_products(client):
    """Test retrieving products received from a supplier through IN transactions."""

    supplier = create_supplier(client)
    product = create_product(client, supplier["id"])

    # Test supplier with no received products
    response = client.get(f"/suppliers/{supplier['id']}/products")

    assert response.status_code == 200
    assert response.get_json() == []

    # Create an incoming transaction associated with the supplier
    response = client.post(
        "/transactions",
        json={
            "product_id": product["id"],
            "supplier_id": supplier["id"],
            "quantity": 5,
            "type": "IN",
        },
    )

    assert response.status_code == 201

    # Test retrieving products received from the supplier
    response = client.get(f"/suppliers/{supplier['id']}/products")

    assert response.status_code == 200

    data = response.get_json()
    assert len(data) == 1
    assert data[0]["id"] == product["id"]

    # Test retrieving products for a nonexistent supplier
    response = client.get("/suppliers/999999/products")

    assert response.status_code == 404
    assert response.get_json()["error"] == "Supplier not found"


def test_products_page(client):
    """Test loading the products page and submitting its creation form."""

    supplier = create_supplier(client)

    # Test loading the products page
    response = client.get("/ui/products")

    assert response.status_code == 200

    # Test creating a product through the webpage
    response = client.post(
        "/ui/products",
        data={
            "name": "Web Test Product",
            "sku": "WEB-001",
            "unit_price": "15.00",
            "quantity_on_hand": "10",
            "threshold": "5",
            "supplier_id": str(supplier["id"]),
        },
    )

    assert response.status_code == 302
    assert response.headers["Location"].endswith("/ui/products")

    # Verify the product was created
    response = client.get("/products")

    assert response.status_code == 200
    products = response.get_json()

    assert len(products) == 1
    assert products[0]["name"] == "Web Test Product"


def test_delete_product_page(client):
    """Test deleting an existing product through the webpage."""

    supplier = create_supplier(client)
    product = create_product(client, supplier["id"])

    # Test deleting the product
    response = client.post(
        f"/ui/products/{product['id']}/delete"
    )

    assert response.status_code == 302
    assert response.headers["Location"].endswith("/ui/products")

    # Verify the product no longer exists
    response = client.get(f"/products/{product['id']}")

    assert response.status_code == 404

    # Test deleting a nonexistent product
    response = client.post("/ui/products/999999/delete")

    assert response.status_code == 302
    assert response.headers["Location"].endswith("/ui/products")


def test_suppliers_page(client):
    """Test loading the suppliers page and submitting its creation form."""

    # Test loading the suppliers page
    response = client.get("/ui/suppliers")

    assert response.status_code == 200

    # Test creating a supplier through the webpage
    response = client.post(
        "/ui/suppliers",
        data={
            "name": "Web Test Supplier",
            "contact_email": "websupplier@example.com",
        },
    )

    assert response.status_code == 302
    assert response.headers["Location"].endswith("/ui/suppliers")

    # Verify the supplier was created
    response = client.get("/suppliers")

    assert response.status_code == 200
    suppliers = response.get_json()

    assert len(suppliers) == 1
    assert suppliers[0]["name"] == "Web Test Supplier"
    assert suppliers[0]["contact_email"] == "websupplier@example.com"


def test_delete_supplier_page(client):
    """Test deleting an existing supplier through the webpage."""

    supplier = create_supplier(client)

    # Test deleting the supplier
    response = client.post(
        f"/ui/suppliers/{supplier['id']}/delete"
    )

    assert response.status_code == 302
    assert response.headers["Location"].endswith("/ui/suppliers")

    # Verify the supplier no longer exists
    response = client.get(f"/suppliers/{supplier['id']}")

    assert response.status_code == 404

    # Test deleting a nonexistent supplier
    response = client.post("/ui/suppliers/999999/delete")

    assert response.status_code == 302
    assert response.headers["Location"].endswith("/ui/suppliers")


def test_transactions_page(client):
    """Test loading the transactions page and submitting transactions."""

    supplier = create_supplier(client)
    product = create_product(
        client,
        supplier["id"],
        quantity=10,
        threshold=5,
    )

    # Test loading the transactions page
    response = client.get("/ui/transactions")

    assert response.status_code == 200

    # Test creating an incoming transaction through the webpage
    response = client.post(
        "/ui/transactions",
        data={
            "product_id": str(product["id"]),
            "type": "IN",
            "quantity": "5",
            "supplier_id": str(supplier["id"]),
        },
    )

    assert response.status_code == 302
    assert response.headers["Location"].endswith("/ui/transactions")

    # Verify the product quantity was updated
    updated_product = get_product(client, product["id"])
    assert updated_product["quantity_on_hand"] == 15

    # Verify the transaction was stored
    response = client.get("/transactions")

    assert response.status_code == 200
    transactions = response.get_json()

    assert len(transactions) == 1
    assert transactions[0]["product_id"] == product["id"]
    assert transactions[0]["type"] == "IN"
    assert transactions[0]["quantity"] == 5

    # Test submitting a transaction for a nonexistent product
    response = client.post(
        "/ui/transactions",
        data={
            "product_id": "999999",
            "type": "IN",
            "quantity": "5",
            "supplier_id": str(supplier["id"]),
        },
    )

    assert response.status_code == 302
    assert response.headers["Location"].endswith("/ui/transactions")


# ============================================================
#  Functions from test_tracy.py for testing purposes
# ============================================================

def create_supplier(client):
    response = client.post(
        "/suppliers",
        json={
            "name": "Test Supplier",
            "contact_email": "supplier@example.com",
        },
    )
    assert response.status_code == 201
    return response.get_json()


def create_product(client, supplier_id, quantity=10, threshold=5):
    response = client.post(
        "/products",
        json={
            "name": "Test Product",
            "sku": "TEST-001",
            "unit_price": 10.0,
            "quantity_on_hand": quantity,
            "threshold": threshold,
            "supplier_id": supplier_id,
        },
    )
    assert response.status_code == 201
    return response.get_json()


def create_transaction(client, product_id, quantity, tx_type):
    return client.post(
        "/transactions",
        json={
            "product_id": product_id,
            "quantity": quantity,
            "type": tx_type,
        },
    )

def get_product(client, product_id):
    response = client.get(f"/products/{product_id}")
    assert response.status_code == 200
    return response.get_json()
