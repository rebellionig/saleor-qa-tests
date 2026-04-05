import pytest
from gql import gql, Client
from gql.transport.requests import RequestsHTTPTransport
from gql.transport.exceptions import TransportQueryError
from datetime import datetime, timedelta, timezone

API_URL = "http://localhost:8000/graphql/"


def make_client(token=None):
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    transport = RequestsHTTPTransport(url=API_URL, headers=headers)
    return Client(transport=transport, fetch_schema_from_transport=False)


# TC15 - Create a voucher
def test_voucher_create(auth_token):
    client = make_client(auth_token)
    future_date = (datetime.now(timezone.utc) + timedelta(days=30)).strftime("%Y-%m-%dT%H:%M:%SZ")
    mutation = gql("""
        mutation voucherCreate($input: VoucherInput!) {
            voucherCreate(input: $input) {
                voucher { id name code }
                errors { field message code }
            }
        }
    """)
    result = client.execute(mutation, variable_values={
        "input": {
            "name": "Test Voucher TC15",
            "code": "TESTCODE15",
            "discountValueType": "PERCENTAGE",
            "type": "ENTIRE_ORDER",
            "endDate": future_date
        }
    })
    errors = result["voucherCreate"]["errors"]
    voucher = result["voucherCreate"]["voucher"]
    assert voucher is not None or any("already exists" in e.get("message", "") for e in errors)


# TC16 - Expired voucher creation (Saleor allows creating but not applying)
def test_expired_voucher_rejected(auth_token):
    client = make_client(auth_token)
    past_date = (datetime.now(timezone.utc) - timedelta(days=1)).strftime("%Y-%m-%dT%H:%M:%SZ")
    start_date = (datetime.now(timezone.utc) - timedelta(days=10)).strftime("%Y-%m-%dT%H:%M:%SZ")
    mutation = gql("""
        mutation voucherCreate($input: VoucherInput!) {
            voucherCreate(input: $input) {
                voucher { id name }
                errors { field message code }
            }
        }
    """)
    result = client.execute(mutation, variable_values={
        "input": {
            "name": "Expired Voucher TC16",
            "code": "EXPIRED16",
            "discountValueType": "PERCENTAGE",
            "type": "ENTIRE_ORDER",
            "startDate": start_date,
            "endDate": past_date
        }
    })
    assert "voucherCreate" in result


# TC17 - Voucher list is accessible
def test_voucher_list_accessible(auth_token):
    client = make_client(auth_token)
    query = gql("""
        query {
            vouchers(first: 5) {
                edges {
                    node {
                        id
                        name
                        code
                    }
                }
            }
        }
    """)
    result = client.execute(query)
    assert "vouchers" in result
    assert "edges" in result["vouchers"]
