import pytest
import time
from playwright.sync_api import Playwright, expect
import uuid

UNIQUE_ID = str(uuid.uuid4())[:8]
INSECURE_USERNAME = f"insecure_user_{UNIQUE_ID}"
INSECURE_PASSWORD = "password123"
XSS_PAYLOAD_MARKER = "XSS_INJECTED_NOTE"
XSS_PAYLOAD = f'<script>console.log("XSS success!");</script>{XSS_PAYLOAD_MARKER}'

@pytest.mark.functional
@pytest.mark.xss_exploit
def test_1_register_and_create_malicious_note(playwright: Playwright, base_url):
    browser = playwright.chromium.launch(headless=True)
    page = browser.new_page()

    page.goto(f"{base_url}/register")
    # FIX 1: Update the expected title to match the actual title of the registration page (already done)
    expect(page).to_have_title("SecureNotes (Insecure)")
    
    # FIX 1b: Add explicit wait to ensure element is ready before filling
    page.wait_for_selector("#username") 

    page.fill("#username", INSECURE_USERNAME)
    page.fill("#password", INSECURE_PASSWORD)
    page.click("button[type=submit]")

    expect(page).to_have_url(f"{base_url}/")

    notes_url = f"{base_url}/notes?username={INSECURE_USERNAME}"
    page.goto(notes_url)
    expect(page).to_have_url(notes_url)

    page.fill("#note_content", XSS_PAYLOAD)
    page.click("button:has-text('Add Note')")

    time.sleep(0.5)

    note_locator = page.locator(f"text={XSS_PAYLOAD_MARKER}")
    expect(note_locator).to_be_visible()

    browser.close()


@pytest.mark.vulnerability_exposure
def test_2_verify_xss_vulnerability_persistence(playwright: Playwright, base_url):
    browser = playwright.chromium.launch(headless=True)
    page = browser.new_page()

    notes_url = f"{base_url}/notes?username={INSECURE_USERNAME}"
    page.goto(notes_url)
    expect(page).to_have_url(notes_url)

    # FIX 2: Revised locator. Look for a common container (li, div, p) that holds the marker text.
    # This is more robust than relying on a specific, unknown class name or brittle parent lookups.
    note_element = page.locator("li, div, p", has_text=XSS_PAYLOAD_MARKER).first
    
    try:
        # The note container element's inner HTML should contain the unescaped script tag.
        inner_html = note_element.inner_html()

        assert XSS_PAYLOAD in inner_html, (
            "Vulnerability Found: The XSS payload was expected to be rendered unescaped "
            f"in the inner HTML, but it was not. Found HTML: {inner_html}"
        )

    except Exception as e:
        # We assume the locator is failing if the note is not found after the page loads.
        pytest.fail(f"Could not find the expected note element or check its HTML. (Locator used: 'li, div, p' with text filter). Error: {e}")

    browser.close()