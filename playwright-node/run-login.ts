import { chromium, Page, BrowserContext } from 'playwright';
import * as fs from 'fs';
import * as path from 'path';

const DATA_DIR = 'data';
const TARGET_ENDPOINTS = [
    'api/v2/developers',
    'api/v2/tld/developers',
    'api/v1/tld/compass/execution/developers'
];

const COMPASS_FETCH_LIMIT = 7000;
let capturedHeaders: Record<string, string> = {};
const savedEndpoints = new Set<string>();

function extractParamsFromPayload(payload: string | null): string {
    if (!payload) return '';
    try {
        const data = JSON.parse(payload);
        const params: string[] = [];
        ['limit', 'startDate', 'endDate', 'teamId'].forEach(key => {
            if (data[key] !== undefined && data[key] !== null) {
                params.push(`${key}_${data[key]}`);
            }
        });
        return params.length > 0 ? '_' + params.join('_') : '';
    } catch {
        return '';
    }
}

function getBaseName(url: string, postData: string | null): string | null {
    const urlParts = url.split('?');
    const urlPath = urlParts[0];
    const queryString = urlParts[1] || '';

    const pathPart = urlPath.split('://').pop()?.split('/').slice(1).join('/');
    if (!pathPart || !pathPart.startsWith('api/')) return null;

    let parts = pathPart.split('/');
    if (parts[0] === 'api') parts = parts.slice(1);

    const version = parts[0].startsWith('v') ? parts[0] : null;
    let rest = version ? parts.slice(1) : parts;

    rest = [...rest].reverse();
    if (version) rest.push(version);

    let baseName = rest.join('_');

    if (queryString.includes('limit=')) {
        const limitMatch = queryString.match(/limit=([^&]+)/);
        if (limitMatch) baseName += `_limit_${limitMatch[1]}`;
    }

    if (postData) {
        baseName += extractParamsFromPayload(postData);
    }

    return baseName;
}

function saveJsonData(name: string, data: any, folderDate: string, typeSuffix: string = 'responses', isCore: boolean = false) {
    const subfolder = isCore ? 'core' : typeSuffix;
    const suffix = typeSuffix.endsWith('s') ? typeSuffix.slice(0, -1) : typeSuffix;
    const filename = `${name}_${suffix}.json`;
    const targetDir = path.join(DATA_DIR, folderDate, subfolder);

    if (!fs.existsSync(targetDir)) {
        fs.mkdirSync(targetDir, { recursive: true });
    }

    const filepath = path.join(targetDir, filename);
    fs.writeFileSync(filepath, JSON.stringify(data, null, 4));
    console.log(`File Written: ${filepath}`);
}

async function runManualFetch(page: Page) {
    if (Object.keys(capturedHeaders).length === 0) {
        console.log('CRITICAL: No headers captured. Manual fetch blocked.');
        return;
    }

    console.log('\n--- Triggering Browser-Native Fetch for Compass (Limit 7000) ---');
    const folderDate = new Date().toISOString().split('T')[0];

    const filteredHeaders: Record<string, string> = {};
    for (const [key, value] of Object.entries(capturedHeaders)) {
        if (!['content-length', 'host', 'connection'].includes(key.toLowerCase())) {
            filteredHeaders[key] = value;
        }
    }

    const payload = {
        limit: COMPASS_FETCH_LIMIT,
        startDate: folderDate,
        endDate: folderDate,
        teamId: null
    };

    try {
        console.log(`Triggering native fetch from browser context with limit ${COMPASS_FETCH_LIMIT}...`);
        const result = await page.evaluate(async ({ headers, payload }: any) => {
            try {
                const url = "https://uix.blueoptima.com/api/v1/tld/compass/execution/developers";
                console.log(`Native fetch to: ${url}`);

                const response = await fetch(url, {
                    method: 'POST',
                    headers: {
                        ...headers,
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify(payload),
                    credentials: 'include'
                });
                return { ok: response.ok, status: response.status, url: url };
            } catch (e: any) {
                return { ok: false, error: e.message };
            }
        }, { headers: filteredHeaders, payload });

        console.log(`Native fetch trigger result:`, result);
    } catch (error) {
        console.error(`Failed to trigger native fetch:`, error);
    }
}

async function saveCookies(context: BrowserContext, folderDate: string) {
    console.log(`Saving browser cookies for ${folderDate}...`);
    try {
        const cookies = await context.cookies();
        const targetDir = path.join(DATA_DIR, folderDate);
        if (!fs.existsSync(targetDir)) {
            fs.mkdirSync(targetDir, { recursive: true });
        }
        const filepath = path.join(targetDir, 'cookies.json');
        fs.writeFileSync(filepath, JSON.stringify(cookies, null, 4));
        console.log(`Cookies saved to: ${filepath}`);
    } catch (error) {
        console.error(`Failed to save cookies:`, error);
    }
}

async function run() {
    const username = process.env.LOGIN_USERNAME || 'dansteve.adekanbi@coutts.com';
    const demoMode = (process.env.DEMO || 'true').toLowerCase() === 'true';
    const folderDate = new Date().toISOString().split('T')[0];

    console.log(`--- Starting Node.js Data Extraction (Interception + Manual Fallback) ---`);
    console.log(`User: ${username}`);
    console.log(`Demo Mode: ${demoMode}`);

    const browser = await chromium.launch({ headless: false });
    const context = await browser.newContext();
    const page = await context.newPage();

    page.on('request', request => {
        const url = request.url();
        if (url.includes('api/')) {
            const name = getBaseName(url, request.postData());
            if (name) {
                const urlPathOnly = url.split('?')[0];
                const isCore = TARGET_ENDPOINTS.some(target => urlPathOnly.endsWith(target));
                const reqData = {
                    method: request.method(),
                    url: url,
                    headers: request.headers(),
                    postData: request.postData()
                };
                saveJsonData(name, reqData, folderDate, 'requests', isCore);
            }
        }
    });

    page.on('response', async response => {
        const url = response.url();
        const request = response.request();
        const name = getBaseName(url, request.postData());

        // Capture headers for manual fetch (X-Auth-Token, etc.)
        const reqHeaders = request.headers();
        const hasAuth = Object.keys(reqHeaders).some(k =>
            ['x-auth-token', 'authorization'].includes(k.toLowerCase())
        );
        if (hasAuth || url.includes('api/v2/tld/developers')) {
            capturedHeaders = { ...capturedHeaders, ...reqHeaders };
            console.log(`!!! Updated captured headers from: ${url}`);
        }

        if (url.includes('api/')) {
            const isTargeted = name ? 'target' : 'extra';
            console.log(`Network Intercepted (${isTargeted}): ${url} (Status: ${response.status()})`);
        }

        if (name) {
            const urlPathOnly = url.split('?')[0];
            const isCore = TARGET_ENDPOINTS.some(target => urlPathOnly.endsWith(target));

            if (response.status() === 200) {
                try {
                    const data = await response.json();
                    saveJsonData(name, data, folderDate, 'responses', isCore);
                    savedEndpoints.add(name);
                } catch (e) {
                    console.error(`Failed to process response for ${name}:`, e);
                }
            } else {
                console.log(`SKIPPED: ${url} (Status: ${response.status()})`);
            }
        }
    });

    try {
        console.log('Navigating to login page...');
        await page.goto('https://uix.blueoptima.com/login');

        console.log(`Entering username: ${username}`);
        await page.fill('input[name="username"]', username);
        await page.click('button[type="submit"]');

        console.log('Waiting for login completion...');
        try {
            // Simplified wait for dashboard elements
            await page.waitForTimeout(15000);
            console.log(`Logged in. URL: ${page.url()}`);

            console.log("Searching for 'Developer view' trigger...");
            const teamTrigger = page.getByText('Team view', { exact: false });
            const developerTrigger = page.getByText('Developer view', { exact: false });

            try {
                await developerTrigger.first().waitFor({ state: 'visible', timeout: 30000 });
                console.log("Clicking 'Developer view'...");
                await developerTrigger.first().click();
                await page.waitForTimeout(5000);

                await teamTrigger.first().waitFor({ state: 'visible', timeout: 30000 });
                console.log("Clicking 'Team view'...");
                await teamTrigger.first().click();
                await page.waitForTimeout(5000);

                await developerTrigger.first().waitFor({ state: 'visible', timeout: 30000 });
                console.log("Clicking 'Developer view'...");
                await developerTrigger.first().click();

                console.log('Trigger sequence complete!');
            } catch (clickErr) {
                console.warn(`WARNING: Trigger sequence failed: ${clickErr}`);
            }

            console.log('Waiting 15 seconds for network capture...');
            await page.waitForTimeout(15000);

            // Trigger the browser-native high-limit fetch
            await runManualFetch(page);

            console.log('Waiting 10 seconds for interception...');
            await page.waitForTimeout(10000);

            await saveCookies(context, folderDate);

        } catch (error) {
            console.error(`Functional block error: ${error}`);
        }

    } catch (error) {
        console.error('An error occurred during execution:', error);
        await page.screenshot({ path: 'node_error_screenshot_interception.png' });
    }

    if (demoMode) {
        console.log('Demo mode active. Keeping browser open. Press Ctrl+C to exit.');
        await new Promise(() => { });
    }

    await browser.close();
}

run().catch(console.error);
