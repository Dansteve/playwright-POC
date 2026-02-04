from playwright.sync_api import Page, expect

class LoginPage:
    def __init__(self, page: Page):
        self.page = page
        self.username_input = page.locator('input[aria-label="Username"]')
        self.password_input = page.locator('input[aria-label="Password"]')
        self.primary_button = page.locator('button.b-button--primary')

    def navigate(self):
        self.page.goto('https://uix.blueoptima.com/uix/login')

    def enter_username(self, username: str):
        self.username_input.wait_for(state='visible')
        self.username_input.fill(username)
        # Trigger SSO detection
        self.username_input.press('Tab')
        self.page.mouse.click(0, 0)  # Click away to ensure blur

    def wait_for_sso_redirection(self):
        print('Waiting for password field to be removed (SSO trigger)...')
        try:
            expect(self.password_input).to_be_hidden(timeout=15000)
            print('Password field removed.')
        except Exception:
            print('Password field still visible. Attempting to proceed anyway...')

    def click_next(self):
        print(f"Attempting to click 'Next' button. Visible: {self.primary_button.is_visible()}, Enabled: {self.primary_button.is_enabled()}")
        self.primary_button.click()
        print("Clicked 'Next' button.")

    def wait_for_login_completion(self):
        print('Waiting for redirection away from login page...')
        self.page.wait_for_url(lambda url: '/uix/login' not in url, timeout=30000)
        print('Successfully redirected.')
