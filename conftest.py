import pytest
import requests
from gql import gql, Client
from gql.transport.requests import RequestsHTTPTransport

API_URL = "http://localhost:8000/graphql/"
ADMIN_EMAIL = "admin@example.com"
ADMIN_PASSWORD = "admin1234"


def get_auth_token():
    transport = RequestsHTTPTransport(url=API_URL)
    client = Client(transport=transport, fetch_schema_from_transport=False)
    query = gql("""
        mutation tokenCreate($email: String!, $password: String!) {
            tokenCreate(email: $email, password: $password) {
                token
                errors { field message }
            }
        }
    """)
    result = client.execute(query, variable_values={
        "email": ADMIN_EMAIL,
        "password": ADMIN_PASSWORD
    })
    return result["tokenCreate"]["token"]


@pytest.fixture(scope="session")
def auth_token():
    return get_auth_token()


@pytest.fixture(scope="session")
def gql_client(auth_token):
    transport = RequestsHTTPTransport(
        url=API_URL,
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    return Client(transport=transport, fetch_schema_from_transport=False)


@pytest.fixture(scope="session")
def unauth_client():
    transport = RequestsHTTPTransport(url=API_URL)
    return Client(transport=transport, fetch_schema_from_transport=False)
