import pytest
from gql import gql, Client
from gql.transport.requests import RequestsHTTPTransport
import threading

API_URL = "http://localhost:8000/graphql/"


def make_client(token=None):
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    transport = RequestsHTTPTransport(url=API_URL, headers=headers)
    return Client(transport=transport, fetch_schema_from_transport=False)


# TC10 - Verify product list is accessible
def test_product_list_accessible(auth_token):
    client = make_client(auth_token)
    query = gql("""
        query {
            products(first: 5, channel: "default-channel") {
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


# TC11 - Product creation with valid data
def test_product_create_valid(auth_token):
    client = make_client(auth_token)

    # First get a product type
    query_types = gql("""
        query {
            productTypes(first: 1) {
                edges { node { id name } }
            }
        }
    """)
    types_result = client.execute(query_types)
    edges = types_result["productTypes"]["edges"]

    if not edges:
        pytest.skip("No product types available to test product creation")

    product_type_id = edges[0]["node"]["id"]

    # Get a category
    query_cats = gql("""
        query {
            categories(first: 1) {
                edges { node { id name } }
            }
        }
    """)
    cats_result = client.execute(query_cats)
    cat_edges = cats_result["categories"]["edges"]

    if not cat_edges:
        pytest.skip("No categories available")

    category_id = cat_edges[0]["node"]["id"]

    mutation = gql("""
        mutation productCreate($input: ProductCreateInput!) {
            productCreate(input: $input) {
                product { id name }
                errors { field message code }
            }
        }
    """)
    result = client.execute(mutation, variable_values={
        "input": {
            "name": "Test Product TC11",
            "productType": product_type_id,
            "category": category_id,
        }
    })
    assert result["productCreate"]["errors"] == [] or result["productCreate"]["product"] is not None


# TC12 - Concurrent product queries do not cause errors
def test_concurrent_product_queries(auth_token):
    results = []
    errors = []

    def run_query():
        try:
            client = make_client(auth_token)
            query = gql("""
                query {
                    products(first: 5, channel: "default-channel") {
                        edges { node { id name } }
                    }
                }
            """)
            result = client.execute(query)
            results.append(result)
        except Exception as e:
            errors.append(str(e))

    threads = [threading.Thread(target=run_query) for _ in range(5)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert len(errors) == 0
    assert len(results) == 5
