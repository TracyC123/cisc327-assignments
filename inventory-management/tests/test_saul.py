#Tests for the products, transactions and accounts endpoints

import base64

import pytest

# ============================================================
# TEST DATA
# ============================================================

#The below items must be of the correct type and not generate server errors. The first post product test
#assumes the below is valid, and so will fail if there are problems
#ids must be 1, 2, 3... in order, since the server assigns ids in creation order
testing_products = [
    {"id": 1, "name": "Widget", "sku": "WID-001", "unit_price": 9.99, "quantity_on_hand": 100},
    {"id": 2, "name": "Gadget", "sku": "GAD-002", "unit_price": 24.50, "quantity_on_hand": 40},
    {"id": 3, "name": "Doohickey", "sku": "DOO-003", "unit_price": 3.75, "quantity_on_hand": 0},
]

#Each of the below items has one problem and should be rejected by the server
invalid_products = [
    {"sku": "NON-001", "unit_price": 1.00, "quantity_on_hand": 5},                       # missing name
    {"name": "No Sku", "unit_price": 1.00, "quantity_on_hand": 5},                       # missing sku
    {"name": "", "sku": "EMP-001", "unit_price": 1.00, "quantity_on_hand": 5},           # empty name
    {"name": "Empty Sku", "sku": "", "unit_price": 1.00, "quantity_on_hand": 5},         # empty sku
    {"name": "Neg Price", "sku": "NEG-001", "unit_price": -5.00, "quantity_on_hand": 5}, # negative price
    {"name": "Str Price", "sku": "STR-001", "unit_price": "free", "quantity_on_hand": 5},# price not a number
    {"name": "Neg Qty", "sku": "NEG-002", "unit_price": 1.00, "quantity_on_hand": -3},   # negative quantity
    {"name": "Frac Qty", "sku": "FRC-001", "unit_price": 1.00, "quantity_on_hand": 2.5}, # quantity not an integer
]

#Valid stock movements against items in testing_products
transactions = [
    {"product_id": 1, "type": "IN", "quantity": 100}
    ]

#Valid suppliers, ids must be 1, 2, 3... in order like testing_products
testing_suppliers = [
    {"id": 1, "name": "Acme", "contact_email": "sales@acme.example"},
]

#Returns the i-th item of testing_products, wrapping around if the list is shorter.
#Must stay above the edit lists below, since they call it when the file loads
def product_at(i):
    return testing_products[i % len(testing_products)]

#Valid edits to existing items in testing_products
#Built from testing_products so they always target real items, whatever that list contains
testing_edits = [
    {"id": product_at(0)["id"], "name": product_at(0)["name"] + " Edited"},
    {"id": product_at(1)["id"], "sku": product_at(1)["sku"] + "-EDIT"},
    {"id": product_at(2)["id"], "unit_price": product_at(2)["unit_price"] + 1.00},
    {"id": product_at(3)["id"], "quantity_on_hand": product_at(3)["quantity_on_hand"] + 10},
]

#Each of the below edits has one problem and should be rejected by the server
invalid_edits = [
    {"id": "abc", "name": "Str Id"},                                              # id is a string
    {"id": max(p["id"] for p in testing_products) + 1, "name": "Missing"},        # id doesn't exist
    {"id": product_at(0)["id"], "name": 123},                                     # name is an int
    {"id": product_at(1)["id"], "name": ""},                                      # empty name
    {"id": product_at(2)["id"], "sku": 456},                                      # sku is an int
    {"id": product_at(3)["id"], "sku": ""},                                       # empty sku
    {"id": product_at(4)["id"], "unit_price": -5.00},                             # negative price
    {"id": product_at(5)["id"], "unit_price": "free"},                            # price not a number
    {"id": product_at(6)["id"], "quantity_on_hand": -3},                          # negative quantity
    {"id": product_at(7)["id"], "quantity_on_hand": 2.5},                         # quantity not an integer
]

#Each of the below transactions has one problem and should be rejected by the server
#Everything else in each one is valid, so the rejection can only be caused by that problem
valid_product_id = product_at(0)["id"]
valid_supplier_id = testing_suppliers[0]["id"]
invalid_transactions = [
    {"type": "IN", "quantity": 5, "supplier_id": valid_supplier_id},                                  # missing product_id
    {"product_id": max(p["id"] for p in testing_products) + 1, "type": "IN", "quantity": 5,
     "supplier_id": valid_supplier_id},                                                               # product doesn't exist
    {"product_id": "abc", "type": "IN", "quantity": 5, "supplier_id": valid_supplier_id},             # product_id is a string
    {"product_id": valid_product_id, "quantity": 5, "supplier_id": valid_supplier_id},                # missing type
    {"product_id": valid_product_id, "type": "SIDEWAYS", "quantity": 5, "supplier_id": valid_supplier_id}, # type not IN/OUT
    {"product_id": valid_product_id, "type": 1, "quantity": 5, "supplier_id": valid_supplier_id},     # type is an int
    {"product_id": valid_product_id, "type": "IN", "supplier_id": valid_supplier_id},                 # missing quantity
    {"product_id": valid_product_id, "type": "IN", "quantity": 0, "supplier_id": valid_supplier_id},  # zero quantity
    {"product_id": valid_product_id, "type": "IN", "quantity": -5, "supplier_id": valid_supplier_id}, # negative quantity
    {"product_id": valid_product_id, "type": "IN", "quantity": 2.5, "supplier_id": valid_supplier_id},# quantity not an integer
    {"product_id": valid_product_id, "type": "IN", "quantity": "five", "supplier_id": valid_supplier_id}, # quantity is a string
    {"product_id": valid_product_id, "type": "OUT", "quantity": product_at(0)["quantity_on_hand"] + 1,
     "supplier_id": valid_supplier_id},                                                               # OUT more than in stock
    {"product_id": valid_product_id, "type": "IN", "quantity": 5,
     "supplier_id": max(s["id"] for s in testing_suppliers) + 1},                                     # supplier doesn't exist
    {"product_id": valid_product_id, "type": "IN", "quantity": 5, "supplier_id": "abc"},              # supplier_id is a string
    [{"product_id": valid_product_id, "type": "IN", "quantity": 5, "supplier_id": valid_supplier_id}],# body is a list, not a dict
]


#Basic auth header for an account
#Must stay above the account lists below, since they call it when the file loads
def login(username, password):
    credentials = base64.b64encode((username + ":" + password).encode()).decode()
    return {"Authorization": "Basic " + credentials}

#The baked-in account the app creates on startup. It is always id 1 and has every permission
admin_login = login("ADMIN", "123")
admin_account = {
    "id": 1,
    "username": "ADMIN",
    "permissions": [
        "accounts:read", "accounts:write",
        "products:read", "products:write",
        "purchase_orders:read", "purchase_orders:write",
        "suppliers:read", "suppliers:write",
        "transactions:read", "transactions:write",
    ],
}

#Valid accounts. ids must be 2, 3, 4... in order, since ADMIN is always id 1
#Permissions are kept sorted, since the server returns them sorted
testing_accounts = [
    {"id": 2, "username": "reader", "password": "readpass", "permissions": ["products:read", "suppliers:read"]},
    {"id": 3, "username": "clerk", "password": "clerk:pass",
     "permissions": ["products:read", "products:write", "transactions:read", "transactions:write"]},  # password has a colon
    {"id": 4, "username": "manager", "password": "managepass", "permissions": ["accounts:read", "accounts:write"]},
    {"id": 5, "username": "nobody", "password": "nopass", "permissions": []},
]

#Each of the below accounts has one problem and should be rejected by the server
invalid_accounts = [
    {"password": "pw", "permissions": []},                                       # missing username
    {"username": "", "password": "pw", "permissions": []},                       # empty username
    {"username": 123, "password": "pw", "permissions": []},                      # username is an int
    {"username": "has:colon", "password": "pw", "permissions": []},              # username has a colon (breaks basic auth)
    {"username": "ADMIN", "password": "pw", "permissions": []},                  # username already taken
    {"username": "nopw", "permissions": []},                                     # missing password
    {"username": "emptypw", "password": "", "permissions": []},                  # empty password
    {"username": "intpw", "password": 123, "permissions": []},                   # password is an int
    {"username": "badperm", "password": "pw", "permissions": ["fly:read"]},      # unknown permission
    {"username": "strperm", "password": "pw", "permissions": "products:read"},   # permissions not a list
    {"username": "intperm", "password": "pw", "permissions": [1]},               # permission is an int
    {"username": "dictperm", "password": "pw", "permissions": [{"a": 1}]},       # permission is a dict
    [{"username": "listbody", "password": "pw", "permissions": []}],             # body is a list, not a dict
]

#Each of the below password changes has one problem and should be rejected by the server
invalid_password_changes = [
    {},                    # missing password
    {"password": ""},      # empty password
    {"password": 123},     # password is an int
]

#Every API endpoint and the permission it needs. Ids in paths don't exist, so no request
#changes any data, and a missing item only gives a 404 after the permission check passes
missing_id = "999"
endpoint_permissions = [
    ("GET", "/products", "products:read"),
    ("GET", "/products/low-stock", "products:read"),
    ("GET", "/products/" + missing_id, "products:read"),
    ("GET", "/products/" + missing_id + "/stock-level", "products:read"),
    ("POST", "/products", "products:write"),
    ("PUT", "/products/" + missing_id, "products:write"),
    ("DELETE", "/products/" + missing_id, "products:write"),
    ("GET", "/suppliers", "suppliers:read"),
    ("GET", "/suppliers/" + missing_id, "suppliers:read"),
    ("GET", "/suppliers/" + missing_id + "/products", "suppliers:read"),
    ("POST", "/suppliers", "suppliers:write"),
    ("PUT", "/suppliers/" + missing_id, "suppliers:write"),
    ("DELETE", "/suppliers/" + missing_id, "suppliers:write"),
    ("GET", "/transactions", "transactions:read"),
    ("POST", "/transactions", "transactions:write"),
    ("GET", "/purchase-orders", "purchase_orders:read"),
    ("GET", "/purchase-orders/" + missing_id, "purchase_orders:read"),
    ("POST", "/purchase-orders", "purchase_orders:write"),
    ("PUT", "/purchase-orders/" + missing_id + "/receive", "purchase_orders:write"),
    ("GET", "/accounts", "accounts:read"),
    ("POST", "/accounts", "accounts:write"),
    ("PUT", "/accounts/" + missing_id + "/password", "accounts:write"),
    ("DELETE", "/accounts/" + missing_id, "accounts:write"),
]

#Each of the below should be refused as not logged in (401)
invalid_logins = [
    {},                                             # no Authorization header
    login("ADMIN", "wrong"),                        # wrong password
    login("ADMIN", ""),                             # empty password
    login("ghost", "123"),                          # account doesn't exist
    login("admin", "123"),                          # usernames are case sensitive
    login(testing_accounts[0]["username"], "wrong"),# wrong password for a created account
    {"Authorization": "Bearer admin-token"},        # old token scheme no longer works
    {"Authorization": "Basic !!!"},                 # not valid base64
    {"Authorization": "Basic"},                     # no credentials
]


# ============================================================
# PRODUCT TESTS
# ============================================================

def test_get_empty_product(client):
    """Products endpoint returns an empty list when no products have been added.

    This is the simplest possible test — it confirms the endpoint exists,
    responds with HTTP 200, and that the store starts clean for every test
    (thanks to the reset() call in conftest.py).
    """
    response = client.get("/products")
    assert response.status_code == 200
    print(response)
    assert response.get_json() == []

def test_create_product(client):
    """Product endpoint functions to add products.

    Adds products generated in above list, asserts they worked, and asserts the items are saved.
    """
    for new_product in testing_products:
        response = client.post("/products", json=new_product)
        assert response.status_code == 201

    response = client.get("/products")

    #remove reorder-level property since we aren't expected to use it as per README
    assert without_reorder_level(response.get_json()) == testing_products

def test_create_invalid_product_rejected(client):
    """Product endpoint rejects invalid products.

    Adds the valid products, then posts each invalid product. Asserts the server responds
    with a 4xx error for each, and that the stored products are unchanged.
    """
    for new_product in testing_products:
        client.post("/products", json=new_product)

    for bad_product in invalid_products:
        response = client.post("/products", json=bad_product)
        assert 400 <= response.status_code < 500

    #none of the invalid products should have been saved
    response = client.get("/products")
    assert without_reorder_level(response.get_json()) == testing_products


def test_get_product_by_id(client):
    """Product endpoint returns a single product by its id.

    Adds the valid products, then fetches each one by id. Asserts each request succeeds
    and returns the matching product.
    """
    for new_product in testing_products:
        client.post("/products", json=new_product)

    for item in testing_products:
        response = client.get("/products/" + str(item["id"]))
        assert response.status_code == 200
        assert without_reorder_level([response.get_json()]) == [item]

def test_edit_product(client):
    """Product endpoint applies valid edits.

    Adds the valid products, then puts each edit in testing_edits. Asserts each request succeeds
    and the returned product matches a local copy with the same edits applied.
    """
    for new_product in testing_products:
        client.post("/products", json=new_product)

    #copy so edits don't change testing_products for other tests
    expected_products = [dict(product) for product in testing_products]

    for edit in testing_edits:
        response = client.put("/products/" + str(edit["id"]), json=edit)
        assert response.status_code == 200

        #apply the same edit locally, then compare with what the server returned
        item = next(product for product in expected_products if product["id"] == edit["id"])
        item.update(edit)
        assert without_reorder_level([response.get_json()]) == [item]

def test_edit_invalid_product_rejected(client):
    """Product endpoint rejects invalid edits.

    Adds the valid products, then puts each invalid edit. Asserts the server responds
    with a 4xx error for each, and that the stored products are unchanged.
    """
    for new_product in testing_products:
        client.post("/products", json=new_product)

    for bad_edit in invalid_edits:
        response = client.put("/products/" + str(bad_edit["id"]), json=bad_edit)
        assert 400 <= response.status_code < 500

        #checked after every edit so a failure points to the edit that got through
        response = client.get("/products")
        assert without_reorder_level(response.get_json()) == testing_products

def test_item_delete(client):
    """Product endpoint deletes a product.

    Adds the valid products, then deletes the first one. Asserts the request succeeds
    and only the remaining products are still stored.
    """
    for new_product in testing_products:
        client.post("/products", json=new_product)

    #nothing to delete
    if len(testing_products) == 0:
        return

    to_be_deleted = testing_products[0]

    #delete returns 204 No Content on success
    response = client.delete("/products/" + str(to_be_deleted["id"]))
    assert response.status_code == 204

    #slice instead of pop so testing_products isn't changed for other tests
    assert without_reorder_level(client.get("/products").get_json()) == testing_products[1:]


# ============================================================
# TRANSACTION TESTS
# ============================================================

def test_transactions(client):
    """Transaction endpoint records stock movements.

    Adds the valid products, then posts each transaction. Asserts each request succeeds,
    the product's stock changes by the right amount, and stock never goes negative.
    """
    for new_product in testing_products:
        client.post("/products", json=new_product)

    #copy so transactions don't change testing_products for other tests
    expected_products = [dict(product) for product in testing_products]

    for transaction in transactions:
        response = client.post("/transactions", json=transaction)
        assert response.status_code == 201

        #compare the stored product with a local copy that has the same transaction applied
        edited_stored_transaction = client.get("/products/" + str(transaction["product_id"])).get_json()
        edited_local_transaction = updated_copy(transaction, expected_products)
        assert [edited_local_transaction] == without_reorder_level([edited_stored_transaction])
        assert edited_stored_transaction["quantity_on_hand"] >= 0

def test_invalid_transactions_rejected(client):
    """Transaction endpoint rejects invalid transactions.

    Adds the valid products and suppliers, then posts each invalid transaction. Asserts the server
    responds with a 4xx error for each, that no stock levels changed, and that no transaction was recorded.
    """
    for new_product in testing_products:
        client.post("/products", json=new_product)

    for new_supplier in testing_suppliers:
        client.post("/suppliers", json=new_supplier)

    for bad_transaction in invalid_transactions:
        response = client.post("/transactions", json=bad_transaction)
        assert 400 <= response.status_code < 500

        #checked after every transaction so a failure points to the one that got through
        response = client.get("/products")
        assert without_reorder_level(response.get_json()) == testing_products

        response = client.get("/transactions")
        assert response.get_json() == []

def test_get_transactions(client):
    """Transaction endpoint filters by product and supplier.

    Adds the valid products and transactions, then looks up transactions by product id,
    by product and supplier id together, and by supplier id. Asserts each result matches
    the transactions list filtered the same way.
    """
    for new_product in testing_products:
        client.post("/products", json=new_product)

    for transaction in transactions:
        response = client.post("/transactions", json=transaction)
        assert response.status_code == 201

    #every distinct supplier id used in transactions (transactions without a supplier are skipped)
    supplier_ids = {transaction.get("supplier_id") for transaction in transactions} - {None}

    for testing_product in testing_products:
        product_id = testing_product["id"]

        #filter by product id only
        response = client.get("/transactions?product_id=" + str(product_id))
        expected = [t for t in transactions if t["product_id"] == product_id]
        assert transaction_fields(response.get_json()) == transaction_fields(expected)

        #filter by product id and supplier id together
        for supplier_id in supplier_ids:
            response = client.get("/transactions?product_id=" + str(product_id) + "&supplier_id=" + str(supplier_id))
            expected = [t for t in transactions if t["product_id"] == product_id and t.get("supplier_id") == supplier_id]
            assert transaction_fields(response.get_json()) == transaction_fields(expected)

    #filter by supplier id only
    for supplier_id in supplier_ids:
        response = client.get("/transactions?supplier_id=" + str(supplier_id))
        expected = [t for t in transactions if t.get("supplier_id") == supplier_id]
        assert transaction_fields(response.get_json()) == transaction_fields(expected)


# ============================================================
# ACCOUNT TESTS
# ============================================================

#These tests log in themselves on every request instead of using the ADMIN login that
#conftest.py adds by default, so they exercise the real authentication
@pytest.fixture
def unauthed_client(client):
    client.environ_base.pop("HTTP_AUTHORIZATION", None)
    return client

def test_admin_account_exists(unauthed_client):
    """ADMIN account is created when the app starts.

    Lists accounts as ADMIN. Asserts ADMIN is the only account and has every permission.
    """
    response = unauthed_client.get("/accounts", headers=admin_login)
    assert response.status_code == 200
    assert response.get_json() == [admin_account]

def test_admin_can_use_every_endpoint(unauthed_client):
    """ADMIN passes the permission check on every endpoint.

    Calls each read endpoint as ADMIN. Asserts none are refused with 401 or 403.
    Only GETs are called, since the write endpoints don't handle an empty body.
    """
    for method, path, permission in endpoint_permissions:
        if method != "GET":
            continue
        response = unauthed_client.open(path, method=method, headers=admin_login)
        assert response.status_code not in (401, 403), method + " " + path

def test_create_account(unauthed_client):
    """Account endpoint creates accounts.

    Posts each account in testing_accounts as ADMIN. Asserts each request succeeds, never
    returns the password, and that the stored accounts are ADMIN followed by the new accounts.
    """
    for new_account in testing_accounts:
        response = unauthed_client.post("/accounts", json=new_account, headers=admin_login)
        assert response.status_code == 201
        assert "password" not in response.get_json()
        assert response.get_json() == account_fields(new_account)

    response = unauthed_client.get("/accounts", headers=admin_login)
    assert response.get_json() == [admin_account] + [account_fields(a) for a in testing_accounts]

def test_create_invalid_account_rejected(unauthed_client):
    """Account endpoint rejects invalid accounts.

    Posts each invalid account as ADMIN. Asserts the server responds with a 4xx error
    for each, and that ADMIN is still the only account.
    """
    for bad_account in invalid_accounts:
        response = unauthed_client.post("/accounts", json=bad_account, headers=admin_login)
        assert 400 <= response.status_code < 500

        #checked after every account so a failure points to the one that got through
        response = unauthed_client.get("/accounts", headers=admin_login)
        assert response.get_json() == [admin_account]

def test_new_accounts_can_log_in(unauthed_client):
    """Created accounts can log in with their passwords.

    Creates the accounts, then has each one list accounts. Asserts the login is accepted:
    200 if the account has accounts:read, otherwise 403 (logged in but not allowed).
    """
    create_accounts(unauthed_client)

    for account in testing_accounts:
        response = unauthed_client.get("/accounts", headers=account_login(account))
        assert response.status_code == (200 if "accounts:read" in account["permissions"] else 403)

def test_list_accounts_by_permission(unauthed_client):
    """Account endpoint filters by permission.

    Creates the accounts, then lists accounts by each permission, and by two permissions together.
    Asserts each result is exactly the accounts holding all of those permissions.
    """
    create_accounts(unauthed_client)
    all_accounts = [admin_account] + [account_fields(a) for a in testing_accounts]

    for permission in admin_account["permissions"]:
        response = unauthed_client.get("/accounts?permission=" + permission, headers=admin_login)
        expected = [a for a in all_accounts if permission in a["permissions"]]
        assert response.get_json() == expected

    #more than one filter means the account needs all of them
    response = unauthed_client.get("/accounts?permission=products:read&permission=transactions:write",
                                   headers=admin_login)
    expected = [a for a in all_accounts
                if "products:read" in a["permissions"] and "transactions:write" in a["permissions"]]
    assert response.get_json() == expected

    #a permission nobody has gives an empty list
    response = unauthed_client.get("/accounts?permission=fly:read", headers=admin_login)
    assert response.get_json() == []

def test_change_password(unauthed_client):
    """Account endpoint changes passwords.

    Creates the accounts, then changes each one's password as ADMIN. Asserts each request succeeds,
    the old password is refused (401), and the new password is accepted.
    """
    create_accounts(unauthed_client)

    for account in testing_accounts:
        new_password = account["password"] + "-new"
        response = unauthed_client.put("/accounts/" + str(account["id"]) + "/password",
                                       json={"password": new_password}, headers=admin_login)
        assert response.status_code == 200
        assert response.get_json() == account_fields(account)

        #401 means the login failed, anything else means it worked
        response = unauthed_client.get("/accounts", headers=account_login(account))
        assert response.status_code == 401
        response = unauthed_client.get("/accounts", headers=login(account["username"], new_password))
        assert response.status_code != 401

def test_change_password_invalid_rejected(unauthed_client):
    """Account endpoint rejects invalid password changes.

    Creates the accounts, then sends each invalid password change. Asserts the server responds
    with a 4xx error for each and the old password still works. Also asserts changing the
    password of an account that doesn't exist gives a 404.
    """
    create_accounts(unauthed_client)
    account = testing_accounts[0]

    for bad_change in invalid_password_changes:
        response = unauthed_client.put("/accounts/" + str(account["id"]) + "/password",
                                       json=bad_change, headers=admin_login)
        assert 400 <= response.status_code < 500

        response = unauthed_client.get("/accounts", headers=account_login(account))
        assert response.status_code != 401

    response = unauthed_client.put("/accounts/" + missing_id + "/password",
                                   json={"password": "pw"}, headers=admin_login)
    assert response.status_code == 404

def test_delete_account(unauthed_client):
    """Account endpoint deletes accounts.

    Creates the accounts, then deletes the first one. Asserts the request succeeds, the deleted
    account can no longer log in, only the other accounts are still stored, and deleting it again gives a 404.
    """
    create_accounts(unauthed_client)
    to_be_deleted = testing_accounts[0]

    #delete returns 204 No Content on success
    response = unauthed_client.delete("/accounts/" + str(to_be_deleted["id"]), headers=admin_login)
    assert response.status_code == 204

    response = unauthed_client.get("/products", headers=account_login(to_be_deleted))
    assert response.status_code == 401

    #slice instead of pop so testing_accounts isn't changed for other tests
    response = unauthed_client.get("/accounts", headers=admin_login)
    assert response.get_json() == [admin_account] + [account_fields(a) for a in testing_accounts[1:]]

    response = unauthed_client.delete("/accounts/" + str(to_be_deleted["id"]), headers=admin_login)
    assert response.status_code == 404

def test_admin_cannot_be_changed(unauthed_client):
    """ADMIN account can't have its password changed or be deleted.

    Tries both as ADMIN, and as an account with accounts:write. Asserts both are refused with 403,
    ADMIN can still log in with 123, and ADMIN is unchanged.
    """
    create_accounts(unauthed_client)
    manager = next(a for a in testing_accounts if "accounts:write" in a["permissions"])

    for headers in (admin_login, account_login(manager)):
        response = unauthed_client.put("/accounts/1/password", json={"password": "changed"}, headers=headers)
        assert response.status_code == 403
        response = unauthed_client.delete("/accounts/1", headers=headers)
        assert response.status_code == 403

    response = unauthed_client.get("/accounts?permission=accounts:write", headers=admin_login)
    assert response.status_code == 200
    assert admin_account in response.get_json()

def test_account_with_permission_manages_accounts(unauthed_client):
    """An account other than ADMIN can manage accounts if it has accounts:write.

    Creates the accounts, then has the manager account create, change the password of,
    and delete a new account. Asserts each request succeeds.
    """
    create_accounts(unauthed_client)
    manager = next(a for a in testing_accounts if "accounts:write" in a["permissions"])
    new_account = {"username": "temp", "password": "temppass", "permissions": ["products:read"]}

    response = unauthed_client.post("/accounts", json=new_account, headers=account_login(manager))
    assert response.status_code == 201
    new_id = str(response.get_json()["id"])

    response = unauthed_client.put("/accounts/" + new_id + "/password",
                                   json={"password": "changed"}, headers=account_login(manager))
    assert response.status_code == 200

    response = unauthed_client.delete("/accounts/" + new_id, headers=account_login(manager))
    assert response.status_code == 204

def test_valid_accounts_limited_to_their_permissions(unauthed_client):
    """Each account can only use the endpoints its permissions allow.

    Creates the accounts, then has each one call every endpoint. Asserts every endpoint the account
    lacks the permission for is refused with 403, and every read endpoint it has the permission for
    is not refused. Writes it is allowed are skipped, since they don't handle an empty body.
    """
    create_accounts(unauthed_client)

    for account in testing_accounts:
        for method, path, permission in endpoint_permissions:
            if permission not in account["permissions"]:
                response = unauthed_client.open(path, method=method, headers=account_login(account))
                assert response.status_code == 403, account["username"] + " " + method + " " + path
            elif method == "GET":
                response = unauthed_client.open(path, method=method, headers=account_login(account))
                assert response.status_code not in (401, 403), account["username"] + " " + method + " " + path

def test_invalid_logins_rejected(unauthed_client):
    """Every endpoint refuses requests that aren't logged in to a valid account.

    Creates the accounts, then calls every endpoint with each invalid login. Asserts each one is
    refused with 401, and that no accounts were changed.
    """
    create_accounts(unauthed_client)

    for headers in invalid_logins:
        for method, path, permission in endpoint_permissions:
            response = unauthed_client.open(path, method=method, headers=headers)
            assert response.status_code == 401, str(headers) + " " + method + " " + path

    response = unauthed_client.get("/accounts", headers=admin_login)
    assert response.get_json() == [admin_account] + [account_fields(a) for a in testing_accounts]

def test_website_needs_no_login(unauthed_client):
    """Website pages are not affected by authentication.

    Loads each page without logging in. Asserts each one loads.
    """
    for path in ["/", "/ui/products", "/ui/suppliers", "/ui/transactions"]:
        response = unauthed_client.get(path)
        assert response.status_code == 200


# ============================================================
# HELPER FUNCTIONS
# ============================================================

#Removes reorder_level from each product, since the server adds it but we don't test it (not in README)
def without_reorder_level(products):
    return [{k: v for k, v in p.items() if k != "reorder_level"} for p in products]

#Applies a transaction to the matching product in products (a copy of testing_products) and returns it
def updated_copy(transaction, products):
    product = next(product for product in products if product["id"] == transaction["product_id"])

    #OUT removes stock, IN adds it
    if transaction["type"] == "OUT":
        product["quantity_on_hand"] -= transaction["quantity"]
    else:
        product["quantity_on_hand"] += transaction["quantity"]

    return product

#Keeps only the fields we send for a transaction, so server-added fields (id, transaction_date) don't affect comparisons
def transaction_fields(transactions):
    return [{"product_id": t["product_id"], "supplier_id": t.get("supplier_id"), "type": t["type"], "quantity": t["quantity"]}
            for t in transactions]

#Login header for one of testing_accounts
def account_login(account):
    return login(account["username"], account["password"])

#Keeps only the fields the server returns for an account, so the password doesn't affect comparisons
def account_fields(account):
    return {"id": account["id"], "username": account["username"], "permissions": account["permissions"]}

#Creates every account in testing_accounts as ADMIN
def create_accounts(client):
    for new_account in testing_accounts:
        response = client.post("/accounts", json=new_account, headers=admin_login)
        assert response.status_code == 201
