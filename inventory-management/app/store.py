"""In-memory data store.

Each "table" is just a dict mapping id -> object, kept in memory for the
lifetime of the running app. Data is lost when the app restarts. This keeps
the project approachable before students cover databases later in the
program, while still separating storage from the route/model code.
"""

from app.models.account import ADMIN_PASSWORD, ADMIN_USERNAME, ALL_PERMISSIONS, Account

products = {}
suppliers = {}
transactions = {}
purchase_orders = {}
accounts = {}

_next_ids = {"product": 1, "supplier": 1, "transaction": 1, "purchase_order": 1, "account": 1}


def next_id(kind):
    id_ = _next_ids[kind]
    _next_ids[kind] += 1
    return id_


def account_by_username(username):
    return next((a for a in accounts.values() if a.username == username), None)


def seed_admin():
    """Create the baked-in ADMIN account, which always has every permission."""
    account_id = next_id("account")
    accounts[account_id] = Account(
        id=account_id,
        username=ADMIN_USERNAME,
        password=ADMIN_PASSWORD,
        permissions=ALL_PERMISSIONS,
    )


def reset():
    """Clear all data. Handy for resetting state between tests."""
    products.clear()
    suppliers.clear()
    transactions.clear()
    purchase_orders.clear()
    accounts.clear()
    _next_ids.update(product=1, supplier=1, transaction=1, purchase_order=1, account=1)
    seed_admin()


seed_admin()
