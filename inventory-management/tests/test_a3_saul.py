from datetime import date
from unittest.mock import patch

import pytest

from app.models.purchase_order import PurchaseOrder


# ============================================================
#  Notification tests: failure and non-trigger paths
# ============================================================

def test_failed_notification_still_completes_transaction(client, monkeypatch):
    """Stub: when the notification service fails, the OUT transaction still
    succeeds and the response reports that the notification was not sent."""

    supplier = create_supplier(client)
    product = create_product(client, supplier["id"], quantity=10, threshold=5)

    # Stub: force the notification service to report a failure
    monkeypatch.setattr(
        "app.routes.transactions.send_notification",
        lambda recipient, subject, message: False,
    )

    response = create_transaction(client, product["id"], 6, "OUT")

    # Assert application response
    assert response.status_code == 201
    data = response.get_json()
    assert data["notification"] is False
    assert data["transaction"]["product_id"] == product["id"]
    assert data["transaction"]["quantity"] == 6
    assert data["transaction"]["type"] == "OUT"

    # Assert application state: stock was still reduced and transaction recorded
    assert get_product(client, product["id"])["quantity_on_hand"] == 4
    assert len(get_transactions(client)) == 1


def test_no_notification_when_stock_stays_at_threshold(client):
    """Mock: no notification is sent when stock does not drop below the
    threshold (boundary: ending exactly at the threshold)."""

    supplier = create_supplier(client)
    product = create_product(client, supplier["id"], quantity=10, threshold=5)

    with patch("app.routes.transactions.send_notification") as mock_send:
        response = create_transaction(client, product["id"], 5, "OUT")

    # Assert application response: no notification field in the result
    assert response.status_code == 201
    data = response.get_json()
    assert "notification" not in data
    assert data["transaction"]["quantity"] == 5

    # Assert application state
    assert get_product(client, product["id"])["quantity_on_hand"] == 5

    # Mock: the notification service must not be called
    mock_send.assert_not_called()


# ============================================================
#  Coverage-directed tests: PurchaseOrder.__init__
# ============================================================

def test_purchase_order_defaults():
    """A new purchase order defaults to pending, created today, not received."""
    po = PurchaseOrder(id=1, supplier_id=2, product_id=3, quantity_ordered=50)

    assert po.id == 1
    assert po.supplier_id == 2
    assert po.product_id == 3
    assert po.quantity_ordered == 50
    assert po.status == "pending"
    assert po.created_date == date.today()
    assert po.received_date is None


def test_purchase_order_explicit_values_are_kept():
    """Explicit status and dates override the defaults and serialize as ISO strings."""
    created = date(2026, 1, 15)
    received = date(2026, 1, 20)
    po = PurchaseOrder(
        id=7,
        supplier_id=1,
        product_id=1,
        quantity_ordered=10,
        status="received",
        created_date=created,
        received_date=received,
    )

    assert po.status == "received"
    assert po.created_date == created
    assert po.received_date == received
    assert po.to_dict() == {
        "id": 7,
        "supplier_id": 1,
        "product_id": 1,
        "quantity_ordered": 10,
        "status": "received",
        "created_date": "2026-01-15",
        "received_date": "2026-01-20",
    }


# ============================================================
#  Coverage-directed tests: product routes, missing product
# ============================================================

def test_update_missing_product_returns_404(client):
    """PUT on a product id that does not exist is rejected and changes nothing."""
    supplier = create_supplier(client)
    product = create_product(client, supplier["id"])

    response = client.put("/products/999", json={"name": "Renamed"})

    assert response.status_code == 404
    assert response.get_json() == {"error": "Product not found"}
    # Application state: the existing product is untouched
    assert get_product(client, product["id"])["name"] == "Test Product"


def test_delete_missing_product_returns_404(client):
    """DELETE on a product id that does not exist is rejected and deletes nothing."""
    supplier = create_supplier(client)
    product = create_product(client, supplier["id"])

    response = client.delete("/products/999")

    assert response.status_code == 404
    assert response.get_json() == {"error": "Product not found"}
    # Application state: the existing product is still there
    products = client.get("/products").get_json()
    assert [p["id"] for p in products] == [product["id"]]


# ============================================================
#  Coverage-directed tests: purchase order routes
# ============================================================

def test_list_purchase_orders_empty(client):
    """GET /purchase-orders returns an empty list when no orders exist."""
    response = client.get("/purchase-orders")

    assert response.status_code == 200
    assert response.get_json() == []


def test_create_purchase_order(client):
    """POST /purchase-orders creates a pending order that appears in the list."""
    supplier = create_supplier(client)
    product = create_product(client, supplier["id"])

    response = create_purchase_order(client, supplier["id"], product["id"], 25)

    assert response.status_code == 201
    data = response.get_json()
    assert data == {
        "id": 1,
        "supplier_id": supplier["id"],
        "product_id": product["id"],
        "quantity_ordered": 25,
        "status": "pending",
        "created_date": date.today().isoformat(),
        "received_date": None,
    }
    # Application state: the order is listed
    assert client.get("/purchase-orders").get_json() == [data]

def test_create_purchase_order_unknown_supplier(client):
    """An order for a supplier that does not exist is rejected and not stored."""
    supplier = create_supplier(client)
    product = create_product(client, supplier["id"])

    response = create_purchase_order(client, 999, product["id"], 25)

    assert response.status_code == 404
    assert response.get_json() == {"error": "Supplier not found"}
    assert client.get("/purchase-orders").get_json() == []


def test_create_purchase_order_unknown_product(client):
    """An order for a product that does not exist is rejected and not stored."""
    supplier = create_supplier(client)

    response = create_purchase_order(client, supplier["id"], 999, 25)

    assert response.status_code == 404
    assert response.get_json() == {"error": "Product not found"}
    assert client.get("/purchase-orders").get_json() == []


def test_get_purchase_order(client):
    """GET /purchase-orders/<id> returns the stored order."""
    supplier = create_supplier(client)
    product = create_product(client, supplier["id"])
    created = create_purchase_order(client, supplier["id"], product["id"], 25).get_json()

    response = client.get(f"/purchase-orders/{created['id']}")

    assert response.status_code == 200
    assert response.get_json() == created

def test_receive_purchase_order(client):
    """Receiving a pending order marks it received today and records an IN transaction."""
    supplier = create_supplier(client)
    product = create_product(client, supplier["id"])
    created = create_purchase_order(client, supplier["id"], product["id"], 25).get_json()

    response = client.put(f"/purchase-orders/{created['id']}/receive")

    assert response.status_code == 200
    data = response.get_json()
    assert data["status"] == "received"
    assert data["received_date"] == date.today().isoformat()

    # Application state: the stored order is updated
    stored = client.get(f"/purchase-orders/{created['id']}").get_json()
    assert stored["status"] == "received"

    # Application state: one IN transaction was recorded for the delivery
    transactions = get_transactions(client)
    assert len(transactions) == 1
    assert transactions[0]["product_id"] == product["id"]
    assert transactions[0]["supplier_id"] == supplier["id"]
    assert transactions[0]["type"] == "IN"
    assert transactions[0]["quantity"] == 25

@pytest.mark.xfail(
    reason="Known defect: receiving a purchase order records an IN transaction "
    "but never increases the product's quantity_on_hand.",
    strict=True,
)
def test_receive_purchase_order_increases_stock(client):
    """Receiving a purchase order should add the ordered quantity to stock."""
    supplier = create_supplier(client)
    product = create_product(client, supplier["id"], quantity=10)
    created = create_purchase_order(client, supplier["id"], product["id"], 25).get_json()

    client.put(f"/purchase-orders/{created['id']}/receive")

    assert get_product(client, product["id"])["quantity_on_hand"] == 35

# ============================================================
#  Coverage-directed tests: transaction routes, invalid input
# ============================================================

def test_create_transaction_invalid_input_rejected(client):
    """Unknown product, non-positive quantity, and an unknown type are each
    rejected, and none of them change stock or record a transaction."""
    supplier = create_supplier(client)
    product = create_product(client, supplier["id"], quantity=10, threshold=5)

    invalid_cases = [
        # (product_id, quantity, type, expected status, expected error)
        (999, 5, "IN", 404, "Product not found"),
        (product["id"], 0, "IN", 400, "Quantity must be greater than 0"),
        (product["id"], 5, "SIDEWAYS", 400, "type must be IN or OUT"),
    ]

    for product_id, quantity, tx_type, status, error in invalid_cases:
        response = create_transaction(client, product_id, quantity, tx_type)

        assert response.status_code == status
        assert response.get_json() == {"error": error}

    # Application state: nothing was recorded and stock is unchanged
    assert get_transactions(client) == []
    assert get_product(client, product["id"])["quantity_on_hand"] == 10


# ============================================================
#  Helpers (adapted from test_a3_tracy.py)
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


def create_purchase_order(client, supplier_id, product_id, quantity_ordered):
    return client.post(
        "/purchase-orders",
        json={
            "supplier_id": supplier_id,
            "product_id": product_id,
            "quantity_ordered": quantity_ordered,
        },
    )


def get_transactions(client):
    response = client.get("/transactions")
    assert response.status_code == 200
    return response.get_json()

