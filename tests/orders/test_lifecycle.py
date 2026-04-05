import pytest
from gql import gql, Client
from gql.transport.requests import RequestsHTTPTransport

API_URL = "http://localhost:8000/graphql/"


def make_client(token=None):
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    transport = RequestsHTTPTransport(url=API_URL, headers=headers)
    return Client(transport=transport, fetch_schema_from_transport=False)


# TC13 - Order list is accessible and returns correct structure
def test_order_list_accessible(auth_token):
    client = make_client(auth_token)
    query = gql("""
        query {
            orders(first: 5) {
                edges {
                    node {
                        id
                        status
                        number
                    }
                }
            }
        }
    """)
    result = client.execute(query)
    assert "orders" in result
    assert "edges" in result["orders"]


# TC14 - Order cancel mutation exists and responds
def test_order_cancel_mutation_structure(auth_token):
    client = make_client(auth_token)

    # Get first available order
    query = gql("""
        query {
            orders(first: 1) {
                edges { node { id status } }
            }
        }
    """)
    result = client.execute(query)
    edges = result["orders"]["edges"]

    if not edges:
        pytest.skip("No orders available to test cancellation")

    order_id = edges[0]["node"]["id"]
    status = edges[0]["node"]["status"]

    if status not in ["UNCONFIRMED", "UNFULFILLED"]:
        pytest.skip(f"Order status is {status}, cannot cancel")

    mutation = gql("""
        mutation orderCancel($id: ID!) {
            orderCancel(id: $id) {
                order { id status }
                errors { field message code }
            }
        }
    """)
    result = client.execute(mutation, variable_values={"id": order_id})
    assert "orderCancel" in result


# TC15 - Order refund mutation structure is valid
def test_order_refund_mutation_structure(auth_token):
    client = make_client(auth_token)
    query = gql("""
        query {
            orders(first: 5) {
                edges { node { id status } }
            }
        }
    """)
    result = client.execute(query)
    edges = result["orders"]["edges"]

    if not edges:
        pytest.skip("No orders available to test refund")

    # Just verify the mutation is accepted by the schema
    fulfilled = [e for e in edges if e["node"]["status"] == "FULFILLED"]
    if not fulfilled:
        pytest.skip("No fulfilled orders available for refund test")

    order_id = fulfilled[0]["node"]["id"]
    mutation = gql("""
        mutation orderRefund($id: ID!, $amount: PositiveDecimal!) {
            orderRefund(id: $id, amount: $amount) {
                order { id status }
                errors { field message code }
            }
        }
    """)
    result = client.execute(mutation, variable_values={
        "id": order_id,
        "amount": "1.00"
    })
    assert "orderRefund" in result
