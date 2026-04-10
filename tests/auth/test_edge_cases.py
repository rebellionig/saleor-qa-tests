import pytest
import threading
import time
from gql import gql, Client
from gql.transport.requests import RequestsHTTPTransport
from gql.transport.exceptions import TransportQueryError

API_URL = "http://localhost:8000/graphql/"


def make_client(token=None):
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    transport = RequestsHTTPTransport(url=API_URL, headers=headers)
    return Client(transport=transport, fetch_schema_from_transport=False)


# TC-AUTH-EDGE-01 - Empty email and password fields
def test_empty_credentials_rejected():
    client = make_client()
    query = gql("""
        mutation {
            tokenCreate(email: "", password: "") {
                token
                errors { field message }
            }
        }
    """)
    result = client.execute(query)
    assert result["tokenCreate"]["token"] is None
    assert len(result["tokenCreate"]["errors"]) > 0


# TC-AUTH-EDGE-02 - Extremely long email input (boundary test)
def test_extremely_long_email_rejected():
    client = make_client()
    long_email = "a" * 1000 + "@test.com"
    query = gql("""
        mutation tokenCreate($email: String!, $password: String!) {
            tokenCreate(email: $email, password: $password) {
                token
                errors { field message }
            }
        }
    """)
    result = client.execute(query, variable_values={
        "email": long_email,
        "password": "password123"
    })
    assert result["tokenCreate"]["token"] is None


# TC-AUTH-EDGE-03 - SQL injection attempt in email field
def test_sql_injection_in_email_rejected():
    client = make_client()
    query = gql("""
        mutation tokenCreate($email: String!, $password: String!) {
            tokenCreate(email: $email, password: $password) {
                token
                errors { field message }
            }
        }
    """)
    result = client.execute(query, variable_values={
        "email": "' OR '1'='1",
        "password": "' OR '1'='1"
    })
    assert result["tokenCreate"]["token"] is None


# TC-API-EDGE-01 - Query with extremely large first parameter
def test_large_pagination_value(auth_token):
    client = make_client(auth_token)
    query = gql("""
        query {
            products(first: 1000, channel: "default-channel") {
                edges {
                    node { id name }
                }
            }
        }
    """)
    try:
        result = client.execute(query)
        assert "products" in result
    except TransportQueryError as e:
        # System should handle gracefully - either cap the value or return error
        assert "first" in str(e).lower() or "limit" in str(e).lower() or "maximum" in str(e).lower()


# TC-API-EDGE-02 - Special characters in product search
def test_special_characters_in_search(auth_token):
    client = make_client(auth_token)
    query = gql("""
        query {
            products(first: 10, filter: { search: "!@#$%^&*()" }, channel: "default-channel") {
                edges {
                    node { id name }
                }
            }
        }
    """)
    result = client.execute(query)
    # Should return empty results without crashing
    assert "products" in result
    assert result["products"]["edges"] == []


# TC-CONCUR-01 - Simultaneous login attempts (race condition)
def test_simultaneous_login_attempts():
    results = []
    errors = []

    def attempt_login():
        try:
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
            results.append(result["tokenCreate"]["token"] is not None)
        except Exception as e:
            errors.append(str(e))

    threads = [threading.Thread(target=attempt_login) for _ in range(5)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    # All concurrent logins should succeed
    assert len(errors) == 0
    assert all(results)


# TC-CONCUR-02 - Parallel product list queries
def test_parallel_product_queries(auth_token):
    results = []
    errors = []

    def run_query():
        try:
            client = make_client(auth_token)
            query = gql("""
                query {
                    products(first: 10, channel: "default-channel") {
                        edges { node { id name } }
                    }
                }
            """)
            result = client.execute(query)
            results.append(len(result["products"]["edges"]) >= 0)
        except Exception as e:
            errors.append(str(e))

    threads = [threading.Thread(target=run_query) for _ in range(10)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert len(errors) == 0
    assert len(results) == 10


# TC-INVALID-01 - Access admin endpoint without token
def test_access_restricted_endpoint_without_token():
    client = make_client()
    query = gql("""
        query {
            customers(first: 5) {
                edges {
                    node { id email }
                }
            }
        }
    """)
    try:
        result = client.execute(query)
        assert result.get("customers") is None
    except TransportQueryError as e:
        assert "permission" in str(e).lower() or "MANAGE" in str(e)


# TC-INVALID-02 - Double voucher code creation (duplicate handling)
def test_duplicate_voucher_code_rejected(auth_token):
    from datetime import datetime, timedelta, timezone
    client = make_client(auth_token)
    future_date = (datetime.now(timezone.utc) + timedelta(days=30)).strftime("%Y-%m-%dT%H:%M:%SZ")

    mutation = gql("""
        mutation voucherCreate($input: VoucherInput!) {
            voucherCreate(input: $input) {
                voucher { id code }
                errors { field message code }
            }
        }
    """)

    input_data = {
        "name": "Duplicate Test Voucher",
        "code": "DUPCODE99",
        "discountValueType": "PERCENTAGE",
        "type": "ENTIRE_ORDER",
        "endDate": future_date
    }

    # First creation
    result1 = client.execute(mutation, variable_values={"input": input_data})

    # Second creation with same code
    result2 = client.execute(mutation, variable_values={"input": input_data})

    # Second attempt should return an error about duplicate code
    errors = result2["voucherCreate"]["errors"]
    assert len(errors) > 0 or result2["voucherCreate"]["voucher"] is None


# TC-INVALID-03 - Rapid repeated failed login attempts
def test_rapid_repeated_failed_logins():
    client = make_client()
    query = gql("""
        mutation {
            tokenCreate(email: "admin@example.com", password: "wrongpassword") {
                token
                errors { field message }
            }
        }
    """)
    failed_count = 0
    for _ in range(8):
        result = client.execute(query)
        if result["tokenCreate"]["token"] is None:
            failed_count += 1
        time.sleep(0.1)

    # All attempts should fail
    assert failed_count == 8
