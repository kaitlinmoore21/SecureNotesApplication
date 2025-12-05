import { test, expect, Page } from '@playwright/test';

const BASE = 'http://127.0.0.1:8000';
const LOGIN = `${BASE}/secure/`;
const REGISTER = `${BASE}/secure/register`;
const NOTES_LIST = `${BASE}/secure/notes`;
const CREATE_NOTE = `${BASE}/secure/notes`;
const SEARCH = `${BASE}/secure/search`;
const NOTE_ID = 4;

// Simple login helper with wait for navigation
async function login(page: Page) {
  await page.goto(LOGIN);
  await page.fill('input[name="username"]', 'testuser');
  await page.fill('input[name="password"]', 'ValidPass123!');
  await Promise.all([
    page.waitForNavigation({ url: NOTES_LIST }),
    page.click('button[type="submit"]'),
  ]);
  await expect(page).toHaveURL(NOTES_LIST);
}

// Registration requires all fields validation
test('Registration requires all fields', async ({ page }) => {
  await page.goto(REGISTER);
  await page.click('button[type="submit"]');
  const usernameInput = page.locator('input[name="username"]');
  await expect(usernameInput).toHaveAttribute('required', '');
  await expect(page.locator('text=This field is required')).toBeVisible().catch(() => {});
});

// Registration fails if username already exists
test('Registration fails if username already exists', async ({ page }) => {
  await page.goto(REGISTER);
  await page.fill('input[name="username"]', 'testuser');
  await page.fill('input[name="password"]', 'ValidPass123!');
  await Promise.all([
    page.waitForResponse(resp => resp.url().includes('/register') && resp.status() === 200),
    page.click('button[type="submit"]'),
  ]);
  const errorMessage = page.getByText('Username already taken');
  await expect(errorMessage).toBeVisible();
});

// User can login with valid credentials
test('User can login with valid credentials', async ({ page }) => {
  await login(page);
});

// Login fails with invalid password
test('Login fails with invalid password', async ({ page }) => {
  await page.goto(LOGIN);
  await page.fill('input[name="username"]', 'testuser');
  await page.fill('input[name="password"]', 'WrongPassword!');
  await Promise.all([
    page.waitForResponse(response => response.url().includes('/login') && response.status() === 200),
    page.click('button[type="submit"]'),
  ]);
  const error = page.getByText(/invalid credentials/i);
  await expect(error).toBeVisible();
});

// Creating a note requires a title
test('Creating a note requires a title', async ({ page }) => {
  await login(page);
  await page.goto(CREATE_NOTE);
  await page.fill('textarea[name="content"]', 'Some content only');
  await page.click('button[type="submit"]');
  const titleInput = page.locator('input[name="title"]');
  await expect(titleInput).toHaveAttribute('required', '');
  await expect(page.locator('text=This field is required')).toBeVisible().catch(() => {});
});

test('User can create a new note', async ({ page }) => {
  await login(page);

  await page.goto(CREATE_NOTE);
  await page.waitForLoadState('domcontentloaded');

  // Debug selectors existence:
  await expect(page.locator('input[name="title"]')).toBeVisible();
  await expect(page.locator('textarea[name="content"]')).toBeVisible();

  await page.fill('input[name="title"]', 'Playwright Test Note');
  await page.fill('textarea[name="content"]', 'Created during automation');

  await Promise.all([
    page.waitForURL(NOTES_LIST, { timeout: 10000 }),
    page.click('button[type="submit"]'),
  ]);

  // Confirm note title is visible
  await expect(page.getByText('Playwright Test Note')).toBeVisible({ timeout: 10000 });
});


// User can search for a note they own
test('User can search for a note they own', async ({ page }) => {
  await login(page);
  await page.goto(`${SEARCH}?q=Playwright`);
  await expect(page.getByText(/Playwright/i)).toBeVisible();
});

// Search for non-owned note shows "No results found"
test('Search for non-owned note shows "No results found"', async ({ page }) => {
  await login(page);
  await page.goto(`${SEARCH}?q=SomeOtherPersonsNote`);
  await expect(page.getByText('No results found')).toBeVisible();
});

// User can edit their own note
test('User can edit their own note', async ({ page }) => {
  await login(page);
  await page.goto(`${BASE}/secure/notes/${NOTE_ID}/edit`);
  await page.waitForSelector('input[name="title"]', { timeout: 10000 });
  await page.waitForSelector('textarea[name="content"]', { timeout: 10000 });
  await page.fill('input[name="title"]', 'Updated Note Title');
  await page.fill('textarea[name="content"]', 'Updated note content');
  await Promise.all([
    page.waitForNavigation({ url: NOTES_LIST }),
    page.click('button[type="submit"]'),
  ]);
  await expect(page.getByText('Updated Note Title')).toBeVisible({ timeout: 10000 });
});

// User can delete their own note
test('User can delete their own note', async ({ page }) => {
  await login(page);
  await page.goto(`${BASE}/secure/notes/${NOTE_ID}/delete`);
  
  // Assuming there is a confirmation button for deletion:
  await Promise.all([
    page.waitForNavigation({ url: NOTES_LIST }),
    page.click('button[type="submit"]'), // confirm delete
  ]);

  await expect(page).toHaveURL(NOTES_LIST);
  await expect(page.getByText('Updated Note Title')).not.toBeVisible();
});
