from werkzeug.security import check_password_hash, generate_password_hash

# scrypt (werkzeug's default) is missing from some Python builds, so use pbkdf2.
# Basic auth re-checks the password on every request, so the iteration count is
# kept low; werkzeug's default (600,000) makes each request take ~0.1s.
PASSWORD_HASH_METHOD = "pbkdf2:sha256:1000"

ADMIN_USERNAME = "ADMIN"
ADMIN_PASSWORD = "123"

ALL_PERMISSIONS = {
    "products:read", "products:write",
    "suppliers:read", "suppliers:write",
    "transactions:read", "transactions:write",
    "purchase_orders:read", "purchase_orders:write",
    "accounts:read", "accounts:write",
}


class Account:
    def __init__(self, id, username, password, permissions):
        self.id = id
        self.username = username
        self.password_hash = generate_password_hash(password, method=PASSWORD_HASH_METHOD)
        self.permissions = set(permissions)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password, method=PASSWORD_HASH_METHOD)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def to_dict(self):
        # password_hash is deliberately left out
        return {
            "id": self.id,
            "username": self.username,
            "permissions": sorted(self.permissions),
        }
