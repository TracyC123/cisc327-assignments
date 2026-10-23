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
