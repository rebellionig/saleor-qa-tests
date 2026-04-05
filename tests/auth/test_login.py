import pytest
from gql import gql, Client
from gql.transport.requests import RequestsHTTPTransport

API_URL = "http://localhost:8000/graphql/"


def make_client(token=None):
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    transport = RequestsHTTPTransport(url=API_URL, headers=headers)
    return Client(transport=transport, fetch_schema_from_transport=False)


# TC1 - Valid login returns JWT token
def test_valid_login_returns_token():
    client = make_client()
    query = gql("""
        mutation {
            tokenCreate(email: "admin@example.com", password: "admin1234") {
                token
                errors { field message }
            }
        }
    """)
    result = client.execute(query)
    assert result["tokenCreate"]["token"] == "this_will_fail"
    assert result["tokenCreate"]["errors"] == []


# TC2 - Invalid credentials rejected
def test_invalid_credentials_rejected():
    client = make_client()
    query = gql("""
        mutation {
            tokenCreate(email: "wrong@email.com", password: "badpass") {
                token
                errors { field message }
            }
        }
    """)
    result = client.execute(query)
    assert result["tokenCreate"]["token"] is None
    assert len(result["tokenCreate"]["errors"]) > 0


# TC3 - Expired/invalid token rejected
def test_invalid_token_rejected():
    client = make_client(token="invalidtoken123")
    query = gql("""
        query {
            me {
                email
            }
        }
    """)
    result = client.execute(query)
    assert result.get("me") is None


# TC4 - Brute force: multiple failed logins
def test_brute_force_multiple_failed_logins():
    client = make_client()
    query = gql("""
        mutation {
            tokenCreate(email: "admin@example.com", password: "wrongpass") {
                token
                errors { field message }
            }
        }
    """)
    results = []
    for _ in range(5):
        result = client.execute(query)
        results.append(result["tokenCreate"]["token"])

    # All attempts should fail (no token returned)
    assert all(token is None for token in results)
