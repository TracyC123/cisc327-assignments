from flask import jsonify, request

from app import store

# endpoint name -> permission it needs
ENDPOINT_PERMISSIONS = {
    "products.list_products": "products:read",
    "products.low_stock": "products:read",
    "products.get_product": "products:read",
    "products.stock_level": "products:read",
    "products.create_product": "products:write",
    "products.update_product": "products:write",
    "products.delete_product": "products:write",

    "suppliers.list_suppliers": "suppliers:read",
    "suppliers.get_supplier": "suppliers:read",
    "suppliers.supplier_products": "suppliers:read",
    "suppliers.create_supplier": "suppliers:write",
    "suppliers.update_supplier": "suppliers:write",
    "suppliers.delete_supplier": "suppliers:write",

    "transactions.list_transactions": "transactions:read",
    "transactions.create_transaction": "transactions:write",

    "purchase_orders.list_purchase_orders": "purchase_orders:read",
    "purchase_orders.get_purchase_order": "purchase_orders:read",
    "purchase_orders.create_purchase_order": "purchase_orders:write",
    "purchase_orders.receive_purchase_order": "purchase_orders:write",

    "accounts.list_accounts": "accounts:read",
    "accounts.create_account": "accounts:write",
    "accounts.change_password": "accounts:write",
    "accounts.delete_account": "accounts:write",
}

PUBLIC_BLUEPRINTS = {"views", "static"}


def check_permissions():
    if request.endpoint is None or request.endpoint.split(".")[0] in PUBLIC_BLUEPRINTS:
        return  # website and 404s pass through untouched
    # Expects "Authorization: Basic <base64 username:password>"
    auth = request.authorization
    if auth is None or auth.type != "basic":
        return jsonify({"error": "Unauthorized"}), 401
    account = store.account_by_username(auth.username)
    if account is None or not account.check_password(auth.password):
        return jsonify({"error": "Unauthorized"}), 401
    # Endpoints missing from ENDPOINT_PERMISSIONS map to None and are denied
    if ENDPOINT_PERMISSIONS.get(request.endpoint) not in account.permissions:
        return jsonify({"error": "Forbidden"}), 403
