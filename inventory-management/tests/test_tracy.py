def test_list_all_suppliers(client):
    """| GET | `/suppliers` | List all suppliers |

    This is the test for creating and listing all suppliers.
    It confirms the endpoint exists, responds with HTTP 200.
    """

    # Check that the list of suppliers is empty initially
    response = client.get("/suppliers")
    assert response.status_code == 200
    assert response.get_json() == []

    # Check boundaries and error cases, such as nonexistent IDs, missing fields, zero quantities, or repeated actions.
    # Create and check that the list of suppliers is with 2 suppliers
    supplier1 = {
        "name": "WGT-001",
        "contact_email": "contact1@example.com",
    }
    supplier2 = {
        "name": "WGT-002",
        "contact_email": "contact2@example.com",
    }

    create_resp1 = client.post("/suppliers", json=supplier1)
    create_resp2 = client.post("/suppliers", json=supplier2)

    assert create_resp1.status_code == 201
    assert create_resp2.status_code == 201

    response = client.get("/suppliers")
    assert response.status_code == 200

    data = response.get_json()
    assert len(data) == 2
    assert {item["name"] for item in data} == {
        "WGT-001",
        "WGT-002",
    }


def test_create_a_supplier(client):
    """| POST | `/suppliers` | Create a supplier |
    Create a supplier.

    This is the create-then-verify pattern: send a POST, then confirm the data
    that test code used created is consistent with the data returned by the API.
    """

    """ Create a supplier first. """
    supplier = {
        "name": "WGT-001",
        "contact_email": "contact@example.com",
    }
    create_resp = client.post("/suppliers", json=supplier)
    assert create_resp.status_code == 201

    """ Retrieve the supplier by ID, make sure there is something created. """
    data = create_resp.get_json()
    assert data["id"] is not None
    assert data["name"] == supplier["name"]
    assert data["contact_email"] == supplier["contact_email"]

    """ Failing tests: Python raises a KeyError instead of returning the expected HTTP 400 response. """

    # Error case: Create a supplier with missing field(s) and check for 400 Bad Request
    # API implementation in app/routes/suppliers.py accesses data["name"] directly
    missing_field_supplier = {
        "contact_email": "missing-name@example.com",
    }
    response = client.post("/suppliers", json=missing_field_supplier)
    assert response.status_code == 400

    # Error case: Create a supplier with an invalid email format and check for 400 Bad Request
    invalid_email_supplier = {
        "name": "WGT-003",
        "contact_email": "not-an-email",
    }
    response = client.post("/suppliers", json=invalid_email_supplier)
    assert response.status_code == 400


def test_get_one_supplier(client):
    """| GET | `/suppliers/<id>` | Get one supplier |
    Get a supplier from previous tests and retrieve it.

    This is the create-then-verify pattern: send a POST, use the returned id
    to make a follow-up GET, and confirm the data is consistent.
    """

    """ Create a supplier first. """
    supplier = {
        "name": "WGT-001",
        "contact_email": "contact@example.com",
    }
    create_resp = client.post("/suppliers", json=supplier)
    assert create_resp.status_code == 201

    """ Retrieve the supplier by ID. """
    supplier_ID = create_resp.get_json()["id"]
    response = client.get(f"/suppliers/{supplier_ID}")

    assert response.status_code == 200
    data = response.get_json()

    assert data["id"] == supplier_ID
    assert data["name"] == supplier["name"]
    assert data["contact_email"] == supplier["contact_email"]

    # Error case: Retrieve a supplier with a nonexistent ID and check for 404 Not Found
    response = client.get("/suppliers/999999")
    assert response.status_code == 404


def test_update_a_supplier(client):
    """| PUT | `/suppliers/<id>` | Update a supplier |
    Get a supplier from previous tests and update it.   Supplier cannot be updated with user interface.

    This is the create-then-verify pattern: send a POST, update with PUT,
    and use the returned id to make a follow-up GET, that confirm the data is consistent.
    """

    """ Create a supplier first. """
    supplier = {
        "name": "WGT-001",
        "contact_email": "contact@example.com",
    }
    create_resp = client.post("/suppliers", json=supplier)
    assert create_resp.status_code == 201

    """ Retrieve the supplier by ID. """
    supplier_ID = create_resp.get_json()["id"]
    response = client.get(f"/suppliers/{supplier_ID}")
    assert response.status_code == 200

    """ Update the supplier's name and contact email. """
    updated_supplier = {
        "name": "WGT-002",
        "contact_email": "contact@gmail.com",
    }

    update = client.put(f"/suppliers/{supplier_ID}", json=updated_supplier)
    assert update.status_code == 200

    """ Retrieve the updated supplier by ID. """
    response = client.get(f"/suppliers/{supplier_ID}")
    assert response.status_code == 200
    data = response.get_json()

    assert data["id"] == supplier_ID
    assert data["name"] == updated_supplier["name"]
    assert data["contact_email"] == updated_supplier["contact_email"]

    # Error case: Update a supplier with a nonexistent ID and check for 404 Not Found
    response = client.put(
        "/suppliers/999999",
        json=updated_supplier,
    )
    assert response.status_code == 404

    """ Failing test: Python accepted the request (status code == 200) instead of returning the expected HTTP 400 response. """

    # Error case: Update a supplier with missing field(s) and check for 400 Bad Request
    missing_field_supplier = {
        "contact_email": "updated@example.com",
    }
    response = client.put(
        f"/suppliers/{supplier_ID}",
        json=missing_field_supplier,
    )
    assert response.status_code == 400

    # Error case: Update a supplier with an invalid email format and check for 400 Bad Request
    invalid_email_supplier = {
        "name": "WGT-003",
        "contact_email": "not-an-email",
    }
    response = client.put(
        f"/suppliers/{supplier_ID}",
        json=invalid_email_supplier,
    )
    assert response.status_code == 400


def test_delete_a_supplier(client):
    """| DELETE | `/suppliers/<id>` | Delete a supplier |
    Get a supplier from previous tests and delete it.
    """

    """ Create a supplier first. """
    supplier = {
        "name": "WGT-001",
        "contact_email": "contact@example.com",
    }
    create_resp = client.post("/suppliers", json=supplier)
    assert create_resp.status_code == 201

    """ Retrieve the supplier by ID. """
    supplier_ID = create_resp.get_json()["id"]

    """ Delete the supplier by ID. """
    delete_supplier = client.delete(f"/suppliers/{supplier_ID}")
    assert delete_supplier.status_code == 204

    """ Retrieve the deleted supplier by ID. """
    response = client.get(f"/suppliers/{supplier_ID}")
    assert response.status_code == 404

    # Error case: Delete a supplier with a nonexistent ID and check for 404 Not Found
    response = client.delete("/suppliers/999999")
    assert response.status_code == 404