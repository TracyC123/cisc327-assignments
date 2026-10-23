#Tests for the products and transactions endpoints

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
