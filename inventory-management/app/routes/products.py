from flask import Blueprint, jsonify, request

from app import store
from app.models.product import Product

products_bp = Blueprint("products", __name__, url_prefix="/products")


def _is_int(value):
    # bool is a subclass of int, so rule it out explicitly
    return isinstance(value, int) and not isinstance(value, bool)


def _is_number(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def _validate_product_fields(data, required):
    """Return an error message for the first invalid field in data, or None.

    Fields named in `required` must be present; any other field is only
    checked if it is supplied.
    """
    if not isinstance(data, dict):
        return "Request body must be a JSON object"

    for field in required:
        if field not in data:
            return f"{field} is required"

    for field in ("name", "sku"):
        if field in data and not (isinstance(data[field], str) and data[field].strip()):
            return f"{field} must be a non-empty string"

    if "unit_price" in data and not (_is_number(data["unit_price"]) and data["unit_price"] >= 0):
        return "unit_price must be a number greater than or equal to 0"

    for field in ("quantity_on_hand", "threshold", "reorder_level"):
        if field in data and not (_is_int(data[field]) and data[field] >= 0):
            return f"{field} must be an integer greater than or equal to 0"

    if "supplier_id" in data and not _is_int(data["supplier_id"]):
        return "supplier_id must be an integer"

    return None


@products_bp.route("", methods=["GET"])
def list_products():
    return jsonify([p.to_dict() for p in store.products.values()])


@products_bp.route("/low-stock", methods=["GET"])
def low_stock():
    """Return products where quantity_on_hand is at or below their reorder_level."""
    flagged = [
        p for p in store.products.values()
        if p.quantity_on_hand <= p.reorder_level
    ]
    return jsonify([p.to_dict() for p in flagged])


@products_bp.route("", methods=["POST"])
def create_product():
    data = request.get_json(silent=True)
    error = _validate_product_fields(data, required=("name", "sku"))
    if error:
        return jsonify({"error": error}), 400
    product_id = store.next_id("product")
    product = Product(
        id=product_id,
        name=data["name"],
        sku=data["sku"],
        unit_price=data.get("unit_price", 0.0),
        quantity_on_hand=data.get("quantity_on_hand", 0),
        threshold=data.get("threshold", 0),
        supplier_id=data.get("supplier_id", 0),
        reorder_level=data.get("reorder_level", 0),
    )
    store.products[product_id] = product
    return jsonify(product.to_dict()), 201


@products_bp.route("/<int:product_id>", methods=["GET"])
def get_product(product_id):
    product = store.products.get(product_id)
    if product is None:
        return jsonify({"error": "Product not found"}), 404
    return jsonify(product.to_dict())


@products_bp.route("/<int:product_id>", methods=["PUT"])
def update_product(product_id):
    product = store.products.get(product_id)
    if product is None:
        return jsonify({"error": "Product not found"}), 404
    data = request.get_json(silent=True)
    error = _validate_product_fields(data, required=())
    if error:
        return jsonify({"error": error}), 400
    product.name = data.get("name", product.name)
    product.sku = data.get("sku", product.sku)
    product.unit_price = data.get("unit_price", product.unit_price)
    product.quantity_on_hand = data.get("quantity_on_hand", product.quantity_on_hand)
    product.threshold = data.get("threshold", product.threshold)
    product.supplier_id = data.get("supplier_id", product.supplier_id)
    return jsonify(product.to_dict())


@products_bp.route("/<int:product_id>", methods=["DELETE"])
def delete_product(product_id):
    product = store.products.pop(product_id, None)
    if product is None:
        return jsonify({"error": "Product not found"}), 404
    return "", 204


@products_bp.route("/<int:product_id>/stock-level", methods=["GET"])
def stock_level(product_id):
    product = store.products.get(product_id)
    if product is None:
        return jsonify({"error": "Product not found"}), 404
    return jsonify({"product_id": product.id, "quantity_on_hand": product.quantity_on_hand})
