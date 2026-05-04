import { test, expect } from '@playwright/test'

test.describe('Title Screen', () => {
  test('should display and navigate to select', async ({ page }) => {
    await page.goto('/')
    await page.waitForLoadState('networkidle')
    await expect(page.locator('.title-main')).toBeVisible()
    await page.click('button:has-text("开始修仙")')
    await expect(page).toHaveURL('/select')
  })
})

test.describe('Talent Select', () => {
  test('should render and draw cards', async ({ page }) => {
    await page.goto('/select')
    await page.waitForLoadState('networkidle')
    await page.waitForTimeout(2000)
    await expect(page.locator('.ts-title')).toBeVisible()

    const input = page.locator('input')
    await input.first().fill('测试仙人')
    await page.click('button:has-text("抽取天赋")')
    await page.waitForTimeout(1000)

    await expect(page.locator('.talent-card').first()).toBeVisible()

    await page.click('button:has-text("确认天赋")')
    await page.waitForTimeout(1000)
    await expect(page.locator('.attr-allocator')).toBeVisible()
  })
})

test.describe('Mobile Viewport', () => {
  test.use({ viewport: { width: 375, height: 812 } })

  test('title screen should fit mobile viewport', async ({ page }) => {
    await page.goto('/')
    await page.waitForLoadState('networkidle')
    await expect(page.locator('.title-main')).toBeVisible()
    const bodyWidth = await page.evaluate(() => document.body.scrollWidth)
    expect(bodyWidth).toBeLessThanOrEqual(380)
  })
})
