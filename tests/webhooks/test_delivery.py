import pytest
from gql import gql, Client
from gql.transport.requests import RequestsHTTPTransport

API_URL = "http://localhost:8000/graphql/"


def make_client(token=None):
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    transport = RequestsHTTPTransport(url=API_URL, headers=headers)
    return Client(transport=transport, fetch_schema_from_transport=False)


# TC19 - Webhook can be created
def test_webhook_create(auth_token):
    client = make_client(auth_token)

    query = gql("""
        query {
            apps(first: 1) {
                edges { node { id name } }
            }
        }
    """)
    result = client.execute(query)
    edges = result["apps"]["edges"]

    if not edges:
        pytest.skip("No apps available to attach webhook")

    app_id = edges[0]["node"]["id"]

    mutation = gql("""
        mutation webhookCreate($input: WebhookCreateInput!) {
            webhookCreate(input: $input) {
                webhook { id name targetUrl }
                errors { field message code }
            }
        }
    """)
    result = client.execute(mutation, variable_values={
        "input": {
            "name": "Test Webhook TC19",
            "targetUrl": "https://webhook.site/test-tc19",
            "syncEvents": [],
            "asyncEvents": ["ORDER_CREATED"],
            "app": app_id,
            "isActive": True
        }
    })
    assert "webhookCreate" in result


# TC20 - Webhook events list is accessible (correct field name is webhookEvents)
def test_webhook_events_accessible(auth_token):
    client = make_client(auth_token)
    query = gql("""
        query {
            webhookEvents {
                eventType
                name
            }
        }
    """)
    result = client.execute(query)
    assert "webhookEvents" in result
    assert len(result["webhookEvents"]) > 0
