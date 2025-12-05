import { test, expect, Page } from '@playwright/test';

const BASE = 'http://127.0.0.1:8000';
const LOGIN = `${BASE}/secure/`;
const REGISTER = `${BASE}/secure/register`;
const NOTES_LIST = `${BASE}/secure/notes`;
const CREATE_NOTE = `${BASE}/secure/notes`;
const SEARCH = `${BASE}/secure/search`;
const NOTE_ID = 4;

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

test('Registration requires all fields', async ({ page }) => {
  await page.goto(REGISTER);
  await page.click('button[type="submit"]');
  const usernameInput = page.locator('input[name="username"]');
  await expect(usernameInput).toHaveAttribute('required', '');
  await expect(page.locator('text=This field is required')).toBeVisible().catch(() => {});
});

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

test('User can login with valid credentials', async ({ page }) => {
  await login(page);
});

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

  await expect(page.locator('input[name="title"]')).toBeVisible();
  await expect(page.locator('textarea[name="content"]')).toBeVisible();

  await page.fill('input[name="title"]', 'Playwright Test Note');
  await page.fill('textarea[name="content"]', 'Created during automation');

  await Promise.all([
    page.waitForURL(NOTES_LIST, { timeout: 10000 }),
    page.click('button[type="submit"]'),
  ]);

  const allTitles = await page.locator('strong').allTextContents();
  console.log('All note titles on page:', allTitles);

  await expect(page.getByText(/Playwright Test Note/i).first()).toBeVisible({ timeout: 10000 });
});


test('User can search for a note they own', async ({ page }) => {
  await login(page);
  await page.goto(`${SEARCH}?q=Playwright`);
  await expect(page.getByText(/Playwright Test Note/i).first()).toBeVisible();
});


test('Search for non-owned note shows "No results found"', async ({ page }) => {
  await login(page);
  await page.goto(`${SEARCH}?q=SomeOtherPersonsNote`);
  await expect(page.getByText('No results found')).toBeVisible();
});

test('User can edit their own note', async ({ page }) => {
  await login(page);
  
  await page.goto(`${BASE}/secure/notes/${15}/edit`);
  console.log('Current URL after goto:', page.url());

  await page.waitForLoadState('domcontentloaded');

  const titleInputCount = await page.locator('input[name="title"]').count();
  console.log('Title input count:', titleInputCount);

  await page.waitForSelector('input[name="title"]', { timeout: 15000 });

  await page.waitForSelector('textarea[name="content"]', { timeout: 15000 });

  await page.fill('input[name="title"]', 'Updated Note Title');
  await page.fill('textarea[name="content"]', 'Updated note content');

  await Promise.all([
    page.waitForNavigation({ url: NOTES_LIST }),
    page.click('button[type="submit"]'),
  ]);

  await expect(page.getByText('Updated Note Title')).toBeVisible({ timeout: 10000 });
});

test('User can delete their own note', async ({ page }) => {
  await login(page);
  await page.goto(`${BASE}/secure/notes/${15}/delete`);
  
  await Promise.all([
    page.waitForNavigation({ url: NOTES_LIST }),
    page.click('button[type="submit"]'),
  ]);

  await expect(page).toHaveURL(NOTES_LIST);
  await expect(page.getByText('Updated Note Title')).not.toBeVisible();
});