# Test data for supplier endpoints, for resuable testing in test_tracy.py
testing_suppliers = [
    {
        "name": "WGT-001",
        "contact_email": "contact1@example.com",
    },
    {
        "name": "WGT-002",
        "contact_email": "contact2@example.com",
    },
]

invalid_suppliers = [
    {
        # Missing required name
        "contact_email": "missing-name@example.com",
    },
    {
        # Invalid email format
        "name": "WGT-003",
        "contact_email": "not-an-email",
    },
]

def test_list_all_suppliers(client):
    """| GET | `/suppliers` | List all suppliers |
    This is the test for creating and listing all suppliers.
    It confirms the endpoint exists and responds with HTTP 200.
    """

    # Check that the list of suppliers is empty initially
    response = client.get("/suppliers")
    assert response.status_code == 200
    assert response.get_json() == []

    # Create and check that the list contains 2 suppliers
    for supplier in testing_suppliers:
        create_response = client.post("/suppliers", json=supplier)
        assert create_response.status_code == 201

    response = client.get("/suppliers")
    assert response.status_code == 200

    data = response.get_json()
    assert len(data) == len(testing_suppliers)
    assert {item["name"] for item in data} == {
        supplier["name"] for supplier in testing_suppliers
    }


def test_create_a_supplier(client):
    """| POST | `/suppliers` | Create a supplier"""

    # Create and verify a valid supplier
    supplier = testing_suppliers[0]
    create_resp = client.post("/suppliers", json=supplier)

    assert create_resp.status_code == 201

    data = create_resp.get_json()
    assert data["id"] is not None
    assert data["name"] == supplier["name"]
    assert data["contact_email"] == supplier["contact_email"]

def test_create_supplier_missing_name(client):
    """POST /suppliers rejects a supplier with a missing name."""

    missing_name_supplier = invalid_suppliers[0]

    response = client.post("/suppliers", json=missing_name_supplier)

    assert response.status_code == 400

def test_create_supplier_invalid_email(client):
    """POST /suppliers rejects a supplier with an invalid email."""

    invalid_email_supplier = invalid_suppliers[1]

    suppliers_before = client.get("/suppliers").get_json()

    response = client.post("/suppliers", json=invalid_email_supplier)

    assert 400 <= response.status_code < 500

    suppliers_after = client.get("/suppliers").get_json()
    assert suppliers_after == suppliers_before

def test_get_one_supplier(client):
    """| GET | `/suppliers/<id>` | Get one supplier"""

    # Create a supplier first
    supplier = testing_suppliers[0]
    create_resp = client.post("/suppliers", json=supplier)
    assert create_resp.status_code == 201

    # Retrieve the supplier by ID
    supplier_ID = create_resp.get_json()["id"]
    response = client.get(f"/suppliers/{supplier_ID}")

    assert response.status_code == 200
    data = response.get_json()

    assert data["id"] == supplier_ID
    assert data["name"] == supplier["name"]
    assert data["contact_email"] == supplier["contact_email"]

    # Error case: nonexistent supplier ID
    response = client.get("/suppliers/999999")
    assert response.status_code == 404


def test_update_a_supplier(client):
    """| PUT | `/suppliers/<id>` | Update a supplier"""

    # Create a supplier first
    supplier = testing_suppliers[0]
    create_resp = client.post("/suppliers", json=supplier)
    assert create_resp.status_code == 201

    supplier_ID = create_resp.get_json()["id"]

    # Update using the second valid test supplier
    updated_supplier = testing_suppliers[1]
    update = client.put(
        f"/suppliers/{supplier_ID}",
        json=updated_supplier,
    )
    assert update.status_code == 200

    # Verify the updated supplier
    response = client.get(f"/suppliers/{supplier_ID}")
    assert response.status_code == 200

    data = response.get_json()
    assert data["id"] == supplier_ID
    assert data["name"] == updated_supplier["name"]
    assert data["contact_email"] == updated_supplier["contact_email"]

def test_update_supplier_missing_name(client):
    """PUT /suppliers rejects an update with a missing name."""

    supplier = testing_suppliers[0]
    create_resp = client.post("/suppliers", json=supplier)
    assert create_resp.status_code == 201

    supplier_ID = create_resp.get_json()["id"]

    suppliers_before = client.get("/suppliers").get_json()

    response = client.put(
        f"/suppliers/{supplier_ID}",
        json=invalid_suppliers[0],
    )

    assert response.status_code == 400

def test_update_supplier_invalid_email(client):
    """PUT /suppliers rejects an update with an invalid email."""

    supplier = testing_suppliers[0]
    create_resp = client.post("/suppliers", json=supplier)
    assert create_resp.status_code == 201

    supplier_ID = create_resp.get_json()["id"]
    suppliers_before = client.get("/suppliers").get_json()

    response = client.put(
        f"/suppliers/{supplier_ID}",
        json=invalid_suppliers[1],
    )

    assert 400 <= response.status_code < 500

    suppliers_after = client.get("/suppliers").get_json()
    assert suppliers_after == suppliers_before


def test_delete_a_supplier(client):
    """| DELETE | `/suppliers/<id>` | Delete a supplier"""

    # Create a supplier first
    supplier = testing_suppliers[0]
    create_resp = client.post("/suppliers", json=supplier)
    assert create_resp.status_code == 201

    supplier_ID = create_resp.get_json()["id"]

    # Delete the supplier
    delete_supplier = client.delete(f"/suppliers/{supplier_ID}")
    assert delete_supplier.status_code == 204

    # Verify the supplier was deleted
    response = client.get(f"/suppliers/{supplier_ID}")
    assert response.status_code == 404

    # Error case: nonexistent supplier ID
    response = client.delete("/suppliers/999999")
    assert response.status_code == 404