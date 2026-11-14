from flask import Blueprint, jsonify, request

from app import store
from app.models.account import ADMIN_USERNAME, ALL_PERMISSIONS, Account

accounts_bp = Blueprint("accounts", __name__, url_prefix="/accounts")


def _valid_string(value):
    return isinstance(value, str) and value.strip() != ""


def _json_object():
    """The request body if it's a JSON object, otherwise {} so it fails validation."""
    data = request.get_json(silent=True)
    return data if isinstance(data, dict) else {}


@accounts_bp.route("", methods=["GET"])
def list_accounts():
    """List accounts. Each ?permission=... narrows to accounts holding all of them."""
    results = list(store.accounts.values())
    for permission in request.args.getlist("permission"):
        results = [a for a in results if permission in a.permissions]
    return jsonify([a.to_dict() for a in results])


@accounts_bp.route("", methods=["POST"])
def create_account():
    data = _json_object()
    username = data.get("username")
    password = data.get("password")
    permissions = data.get("permissions", [])

    if not _valid_string(username):
        return jsonify({"error": "username is required"}), 400
    # Basic auth splits "username:password" at the first colon
    if ":" in username:
        return jsonify({"error": "username cannot contain ':'"}), 400
    if not _valid_string(password):
        return jsonify({"error": "password is required"}), 400
    if not isinstance(permissions, list) or not all(
        isinstance(p, str) and p in ALL_PERMISSIONS for p in permissions
    ):
        return jsonify({"error": "permissions must be a list of known permissions"}), 400
    if store.account_by_username(username) is not None:
        return jsonify({"error": "username already exists"}), 409

    account_id = store.next_id("account")
    account = Account(id=account_id, username=username, password=password, permissions=permissions)
    store.accounts[account_id] = account
    return jsonify(account.to_dict()), 201


@accounts_bp.route("/<int:account_id>/password", methods=["PUT"])
def change_password(account_id):
    account = store.accounts.get(account_id)
    if account is None:
        return jsonify({"error": "Account not found"}), 404
    if account.username == ADMIN_USERNAME:
        return jsonify({"error": "The ADMIN account cannot be changed"}), 403
    data = _json_object()
    password = data.get("password")
    if not _valid_string(password):
        return jsonify({"error": "password is required"}), 400
    account.set_password(password)
    return jsonify(account.to_dict())


@accounts_bp.route("/<int:account_id>", methods=["DELETE"])
def delete_account(account_id):
    account = store.accounts.get(account_id)
    if account is None:
        return jsonify({"error": "Account not found"}), 404
    if account.username == ADMIN_USERNAME:
        return jsonify({"error": "The ADMIN account cannot be changed"}), 403
    store.accounts.pop(account_id)
    return "", 204
