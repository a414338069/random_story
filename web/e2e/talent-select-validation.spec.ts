import { test, expect } from '@playwright/test'

test.describe('Talent Select Validation', () => {
  test('should show validation error when submitting with empty name', async ({ page }) => {
    await page.goto('/select')
    await page.waitForLoadState('networkidle')
    await page.waitForTimeout(1500)

    await page.click('button:has-text("抽取天赋")')

    await expect(page.getByText('请输入道号')).toBeVisible()

    const input = page.locator('input')
    await expect(input.first()).toBeVisible()
  })

  test('should proceed normally with a valid name', async ({ page }) => {
    await page.goto('/select')
    await page.waitForLoadState('networkidle')
    await page.waitForTimeout(1500)

    const input = page.locator('input')
    await input.first().fill('测试仙人')

    await page.click('button:has-text("抽取天赋")')

    await expect(page.locator('.talent-card').first()).toBeVisible()
  })
})
