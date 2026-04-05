import pytest
from gql import gql, Client
from gql.transport.requests import RequestsHTTPTransport
from gql.transport.exceptions import TransportQueryError

API_URL = "http://localhost:8000/graphql/"


def make_client(token=None):
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    transport = RequestsHTTPTransport(url=API_URL, headers=headers)
    return Client(transport=transport, fetch_schema_from_transport=False)


# TC8 - productList query returns correct schema
def test_product_list_query(auth_token):
    client = make_client(auth_token)
    query = gql("""
        query {
            products(first: 10, channel: "default-channel") {
                edges {
                    node {
                        id
                        name
                        slug
                    }
                }
            }
        }
    """)
    result = client.execute(query)
    assert "products" in result
    assert "edges" in result["products"]


# TC9 - Mutation with missing required arg returns validation error
def test_mutation_missing_required_arg(auth_token):
    client = make_client(auth_token)
    query = gql("""
        mutation {
            productCreate(input: {}) {
                product { id }
                errors { field message code }
            }
        }
    """)
    try:
        result = client.execute(query)
        assert len(result["productCreate"]["errors"]) > 0
    except TransportQueryError as e:
        # GraphQL validation error for missing required fields is the correct response
        assert "productType" in str(e) or "invalid value" in str(e)


# TC10 - Unauthorised query blocked (no auth header)
def test_unauthorised_mutation_blocked():
    client = make_client()
    query = gql("""
        query {
            orders(first: 5) {
                edges {
                    node { id }
                }
            }
        }
    """)
    try:
        result = client.execute(query)
        assert result.get("orders") is None
    except TransportQueryError as e:
        # PermissionDenied is the correct response
        assert "MANAGE_ORDERS" in str(e) or "permission" in str(e).lower()
