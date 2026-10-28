import base64

import pytest

from app import create_app, store


@pytest.fixture
def client():
    app = create_app()
    app.config["TESTING"] = True
    store.reset()
    with app.test_client() as client:
        admin_credentials = base64.b64encode(b"ADMIN:123").decode()
        client.environ_base["HTTP_AUTHORIZATION"] = f"Basic {admin_credentials}"
        yield client
    store.reset()
