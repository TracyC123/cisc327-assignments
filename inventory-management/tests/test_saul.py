#List all products


#The below items must be of the correct type and not generate server errors. The first post product test
#assumes the below is valid, and so will fail if there are problems 
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

transactions = [
    {"product_id": 1, "type": "IN", "quantity": 100}
    ]

#Valid edits to existing items in testing_products
#Built from testing_products so they always target real items, whatever that list contains
def product_at(i):
    return testing_products[i % len(testing_products)]

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

def without_reorder_level(products):
    return [{k: v for k, v in p.items() if k != "reorder_level"} for p in products]

def updated_copy(transaction):
    product = next(product for product in testing_products if product["id"] == transaction["product_id"])

    if transaction["type"] == "OUT":   
        product["quantity_on_hand"] -= transaction["quantity"]
    else:
        product["quantity_on_hand"] += transaction["quantity"]

    return product



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
    for new_product in testing_products:
        client.post("/products", json=new_product)

    #copy so edits don't change testing_products for other tests
    expected_products = [dict(product) for product in testing_products]

    for edit in testing_edits:
        response = client.put("/products/" + str(edit["id"]), json=edit)
        assert response.status_code == 200

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

        response = client.get("/products")
        assert without_reorder_level(response.get_json()) == testing_products

def test_item_delete(client):
    for new_product in testing_products:
            client.post("/products", json=new_product)
    if len(testing_products) == 0:
        return
    
    to_be_deleted = testing_products[0]

    response = client.delete("/products/" + str(to_be_deleted["id"]))
    assert response.status_code == 204
    assert without_reorder_level(client.get("/products").get_json()) == testing_products[1:]

        
def test_transactions(client):

    for new_product in testing_products:
        client.post("/products", json=new_product)

    for transaction in transactions:
        response = client.post("/transactions", json=transaction)
        assert response.status_code == 201
        edited_stored_transaction = client.get("/products/" + str(transaction["product_id"])).get_json()
        edited_local_transaction = updated_copy(transaction)
        assert edited_local_transaction == without_reorder_level(edited_stored_transaction) 
        assert edited_stored_transaction["quantity_on_hand"] >= 0 

def test_get_transactions(client):


    for new_product in testing_products:
        client.post("/products", json=new_product)

    for transaction in transactions:
            response = client.post("/transactions", json=transaction)
            assert response.status_code == 201

    supplier_ids = [transaction["supplier_id"] for transaction in transactions]

    for testing_product in testing_products:
        product_id = testing_product["id"]
    
        response = client.get("/transactions/?product_id=" + product_id)

        assert response.get_json() == transactions.sort(sort by removing all that dont have matching product ID)

        for supplier_id in supplier_ids:
            response = client.get("/transactions/?product_id=" + product_id + "&supplier_id=" + supplier_id)
            assert response.get_json() == transactions.sort(sort by removing all that dont have matching product ID and supplier id)

    for supplier_id in supplier_ids:
        response = client.get("/transactions/?supplier_id=" + supplier_id)
        assert response.get_json() == transactions.sort(sort by removing all that dont have matching supplier id)

    







    

#need to test all product IDs, and any supplier ID matches if they are in the transaction. So go through each item and search it with a nested loop for each supplier ID found in transactions. 
#then check it by taking the transaction list and sorting for the above, and assessing that they are equal, boom 