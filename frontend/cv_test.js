const { chromium } = require('playwright');

(async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: 1600, height: 1000 } });
  const errors = [];
  page.on('pageerror', (e) => errors.push('pageerror: ' + e.message));
  page.on('console', (msg) => { if (msg.type() === 'error') errors.push('console: ' + msg.text()); });

  await page.goto('http://localhost:5173/login');
  await page.fill('input[type="email"], input[name="email"]', 'cvtest@example.com');
  await page.fill('input[type="password"], input[name="password"]', 'TestPass123');
  await page.click('button[type="submit"]');
  await page.waitForURL('**/dashboard', { timeout: 15000 });

  await page.goto('http://localhost:5173/cv-builder');
  await page.waitForSelector('text=Build your CV', { timeout: 15000 });
  await page.screenshot({ path: 'C:/Users/iremi/AppData/Local/Temp/claude/d--ai-career-navigator/190c16fa-1151-42c7-aaea-60fc24c18ab4/scratchpad/cv_1_initial.png', fullPage: true });

  // Fill personal title
  await page.fill('label:has-text("Title") >> xpath=following-sibling::input', 'Artificial Intelligence Student');
  await page.fill('label:has-text("Phone") >> xpath=following-sibling::input', '+601111580711');
  await page.fill('label:has-text("Location") >> xpath=following-sibling::input', 'Melaka, Malaysia');
  await page.fill('label:has-text("Github") >> xpath=following-sibling::input, label:has-text("GitHub") >> xpath=following-sibling::input', 'github.com/ZayedDevs').catch(()=>{});

  // Summary
  await page.fill('textarea', 'Final-year student and AI specialist passionate about building end-to-end ML systems.');

  // Add a skill
  const skillInputs = page.locator('input[placeholder="Add…"]');
  await skillInputs.nth(0).fill('python');
  await skillInputs.nth(0).press('Enter');
  await skillInputs.nth(0).fill('docker');
  await skillInputs.nth(0).press('Enter');

  // Add expertise
  await skillInputs.nth(1).fill('Machine Learning');
  await skillInputs.nth(1).press('Enter');

  // Add a project
  await page.click('button:has-text("+ Add Project")');
  await page.screenshot({ path: 'C:/Users/iremi/AppData/Local/Temp/claude/d--ai-career-navigator/190c16fa-1151-42c7-aaea-60fc24c18ab4/scratchpad/cv_2_filled.png', fullPage: true });

  console.log('ERRORS:', JSON.stringify(errors, null, 2));
  console.log('DONE');
  await page.waitForTimeout(500);
  await browser.close();
})().catch((e) => { console.error(e); process.exit(1); });
