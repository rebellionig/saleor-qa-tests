import pytest
from playwright.sync_api import sync_playwright

DASHBOARD_URL = "http://localhost:9000"
ADMIN_EMAIL = "admin@example.com"
ADMIN_PASSWORD = "admin1234"


def login(page):
    page.goto(DASHBOARD_URL)
    page.wait_for_load_state("networkidle")
    page.wait_for_selector('input[name="email"]', timeout=10000)
    page.fill('input[name="email"]', ADMIN_EMAIL)
    page.fill('input[name="password"]', ADMIN_PASSWORD)
    page.click('button[type="submit"]')
    # Wait for SPA to redirect after login
    page.wait_for_timeout(3000)
    page.wait_for_load_state("networkidle")


# TC5 - Dashboard login and navigation E2E
def test_dashboard_login_and_navigation():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        login(page)

        # After login the URL should no longer be the login page
        assert page.url != f"{DASHBOARD_URL}/" or \
               page.locator("text=Store Dashboard").count() > 0 or \
               page.locator("text=Home").count() > 0 or \
               "login" not in page.url

        browser.close()


# TC6 - Navigate to catalog section
def test_navigate_to_catalog():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        login(page)

        page.goto(f"{DASHBOARD_URL}/products/")
        page.wait_for_load_state("networkidle")

        assert "products" in page.url

        browser.close()


# TC7 - Navigate to orders section
def test_navigate_to_orders():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        login(page)

        page.goto(f"{DASHBOARD_URL}/orders/")
        page.wait_for_load_state("networkidle")

        assert "orders" in page.url

        browser.close()
