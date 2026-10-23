def test_list_all_suppliers(client):
    """| GET | `/suppliers` | List all suppliers |

    This is the test for creating and listing all suppliers. 
    It confirms the endpoint exists, responds with HTTP 200.
    """

    response = client.get("/suppliers")
    assert response.status_code == 200
    assert response.get_json() == []


def test_create_a_supplier(client):
    """| POST | `/suppliers` | Create a supplier |
    Create a supplier.

    This is the create-then-verify pattern: send a POST, then confirm the data 
    that test code used created is consistent with the data returned by the API.
    """

    """ Create a supplier first. """
    supplier = {
            "id": "1234",
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

def test_update_a_supplier(client):
    """| PUT | `/suppliers/<id>` | Update a supplier |
    Get a supplier from previous tests and update it.

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
    data = response.get_json()

    assert data["id"] == supplier_ID
    assert data["name"] == updated_supplier["name"]
    assert data["contact_email"] == updated_supplier["contact_email"]


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

    """ Retrieve the deleted supplier by ID. """
    response = client.get(f"/suppliers/{supplier_ID}")
    assert response.status_code == 404
    