import { Page, Locator, expect } from '@playwright/test';

export class LoginPage {
    readonly page: Page;
    readonly usernameInput: Locator;
    readonly passwordInput: Locator;
    readonly primaryButton: Locator;

    constructor(page: Page) {
        this.page = page;
        this.usernameInput = page.locator('input[aria-label="Username"]');
        this.passwordInput = page.locator('input[aria-label="Password"]');
        this.primaryButton = page.locator('button.b-button--primary');
    }

    async navigate() {
        await this.page.goto('https://uix.blueoptima.com/uix/login');
    }

    async enterUsername(username: string) {
        await this.usernameInput.waitFor({ state: 'visible' });
        await this.usernameInput.fill(username);
        // Trigger SSO detection
        await this.usernameInput.press('Tab');
        await this.page.mouse.click(0, 0); // Click away to ensure blur
    }

    async waitForSSORedirection() {
        console.log('Waiting for password field to be removed (SSO trigger)...');
        try {
            await expect(this.passwordInput).toBeHidden({ timeout: 15000 });
            console.log('Password field removed.');
        } catch (error) {
            console.log('Password field still visible. Attempting to proceed anyway...');
        }
    }

    async clickNext() {
        await this.primaryButton.click();
    }

    async waitForLoginCompletion() {
        console.log('Waiting for redirection away from login page...');
        await this.page.waitForURL((url) => !url.href.includes('/uix/login'), { timeout: 30000 });
        console.log('Successfully redirected.');
    }
}
