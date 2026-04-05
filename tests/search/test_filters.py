import pytest
from gql import gql, Client
from gql.transport.requests import RequestsHTTPTransport

API_URL = "http://localhost:8000/graphql/"


def make_client(token=None):
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    transport = RequestsHTTPTransport(url=API_URL, headers=headers)
    return Client(transport=transport, fetch_schema_from_transport=False)


# TC17 - Product search returns results
def test_product_search_returns_results(auth_token):
    client = make_client(auth_token)
    query = gql("""
        query {
            products(first: 10, filter: { search: "shirt" }, channel: "default-channel") {
                edges {
                    node { id name }
                }
            }
        }
    """)
    result = client.execute(query)
    assert "products" in result
    assert "edges" in result["products"]


# TC18 - Special characters handled safely (XSS injection)
def test_special_chars_handled_safely(auth_token):
    client = make_client(auth_token)
    query = gql("""
        query {
            products(first: 10, filter: { search: "<script>alert(1)</script>" }, channel: "default-channel") {
                edges {
                    node { id name }
                }
            }
        }
    """)
    result = client.execute(query)
    # Should return empty results without throwing an error
    assert "products" in result
    assert result["products"]["edges"] == []


# TC - Empty search string returns products
def test_empty_search_returns_products(auth_token):
    client = make_client(auth_token)
    query = gql("""
        query {
            products(first: 5, channel: "default-channel") {
                edges {
                    node { id name }
                }
            }
        }
    """)
    result = client.execute(query)
    assert "products" in result
