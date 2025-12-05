from playwright.sync_api import Playwright, expect
import time
import pytest

# BASE_URL is now passed by pytest command line using the --base-url fixture.
UNIQUE_USERNAME = f"secureuser_{int(time.time())}"
PASSWORD = "SecurePassword123!"


@pytest.mark.uc1_nf_01
def test_uc1_successful_registration_and_login(playwright: Playwright, base_url):
    """Tests successful registration and login on the secure application."""
    browser = playwright.chromium.launch(headless=True)
    page = browser.new_page()

    
    # 1. Register
    # FIX: Concatenate the base_url fixture with the path
    page.goto(f"{base_url}/register")
    page.fill("#username", UNIQUE_USERNAME)
    page.fill("#password", PASSWORD)
    page.fill("#confirm_password", PASSWORD)
    page.click("button[type='submit']")

    expect(page.locator("text=Registration successful")).to_be_visible()

    # 2. Login
    # FIX: Concatenate the base_url fixture with the path
    page.goto(f"{base_url}/login")
    page.fill("#username", UNIQUE_USERNAME)
    page.fill("#password", PASSWORD)
    page.click("button[type='submit']")

    # Assert success redirect
    expect(page).to_have_url(f"{base_url}/dashboard")

    browser.close()


@pytest.mark.uc1_af_02
def test_uc1_input_validation_empty_username(playwright: Playwright, base_url):
    """Tests input validation for an empty username during registration."""
    browser = playwright.chromium.launch(headless=True)
    page = browser.new_page()

    # Attempt registration with missing username
    # FIX: Concatenate the base_url fixture with the path
    page.goto(f"{base_url}/register")
    page.fill("#password", "ValidPassword1")
    page.fill("#confirm_password", "ValidPassword1")
    page.click("button[type='submit']")

    # Assert form error
    expect(page).to_have_url(f"{base_url}/register")
    expect(page.locator("text=Username is required")).to_be_visible()

    browser.close()


@pytest.mark.xss_check
def test_security_xss_prevention(playwright: Playwright, base_url):
    """Verifies the secure application correctly prevents XSS (by escaping the payload)."""
    browser = playwright.chromium.launch(headless=True)
    page = browser.new_page()

    # Login
    # FIX: Concatenate the base_url fixture with the path
    page.goto(f"{base_url}/login")
    page.fill("#username", UNIQUE_USERNAME)
    page.fill("#password", PASSWORD)
    page.click("button[type='submit']")

    # Inject XSS payload
    # FIX: Concatenate the base_url fixture with the path
    page.goto(f"{base_url}/create_note")
    xss_payload = "<script>document.getElementById('note-title').innerText = 'XSS_EXECUTED';</script>"

    page.fill("#title", "XSS Attempt")
    page.fill("#content", xss_payload)
    page.click("button[type='submit']")

    # View the note
    # FIX: Concatenate the base_url fixture with the path
    page.goto(f"{base_url}/dashboard")
    page.click("text=XSS Attempt")

    # Assertion: Script MUST NOT have run (title remains original)
    note_title_element = page.locator("#note-title")
    expect(note_title_element).to_have_text("XSS Attempt")

    browser.close()