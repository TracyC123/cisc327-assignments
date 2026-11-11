from unittest.mock import patch

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
