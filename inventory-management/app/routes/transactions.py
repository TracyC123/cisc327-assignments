from flask import Blueprint, jsonify, request

from app import store
from app.models.transaction import Transaction

transactions_bp = Blueprint("transactions", __name__, url_prefix="/transactions")


@transactions_bp.route("", methods=["GET"])
def list_transactions():
    results = list(store.transactions.values())
    product_id = request.args.get("product_id", type=int)
    supplier_id = request.args.get("supplier_id", type=int)
    if product_id is not None:
        results = [t for t in results if t.supplier_id == product_id]
    if supplier_id is not None:
        results = [t for t in results if t.supplier_id == supplier_id]
    return jsonify([t.to_dict() for t in results])


@transactions_bp.route("", methods=["POST"])
def create_transaction():
    data = request.get_json()
    product = store.products.get(data["product_id"])
    if product is None:
        return jsonify({"error": "Product not found"}), 404

    quantity = data["quantity"]
    tx_type = data["type"]

    if quantity <= 0:
        return jsonify({"error": "Quantity must be greater than 0"}), 400

    if tx_type == "IN":
        product.quantity_on_hand += quantity
    elif tx_type == "OUT":
        if product.quantity_on_hand < quantity: # Check before modifying the quantity_on_hand
            return jsonify({"error": "The quantity of stock requires more than the stock on hand.  Please replenish before proceeding."}), 400
        product.quantity_on_hand -= quantity
    else:
        return jsonify({"error": "type must be IN or OUT"}), 400

    transaction_id = store.next_id("transaction")
    transaction = Transaction(
        id=transaction_id,
        product_id=data["product_id"],
        supplier_id=data.get("supplier_id"),
        type=tx_type,
        quantity=quantity,
    )
    store.transactions[transaction_id] = transaction
    result = {"transaction": transaction.to_dict()}

    if tx_type == "OUT" and product.quantity_on_hand < product.threshold:
        supplier = store.suppliers.get(product.supplier_id)
        if supplier is not None:
            result["notification"] = (
                f"{product.name} is below the threshold of {product.threshold}. The system has identified {supplier.name} ({supplier.contact_email}) for replenishment."
            )
        else: 
            product.quantity_on_hand += quantity # Revert the quantity change since the transaction cannot be completed without a supplier
            return jsonify({"error": "There is no supplier associated with this product.  Please add a supplier."}), 400

    return jsonify(result), 201
