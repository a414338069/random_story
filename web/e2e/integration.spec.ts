import { test, expect } from '@playwright/test'

test.describe('Integration', () => {
  test('full UI flow from title to talent select', async ({ page }) => {
    await page.goto('/')
    await page.waitForLoadState('networkidle')
    await expect(page.locator('.title-main')).toBeVisible()
    await page.click('button:has-text("开始修仙")')
    await expect(page).toHaveURL('/select')

    await page.waitForLoadState('networkidle')
    await page.waitForTimeout(1500)
    const input = page.locator('input')
    await input.first().fill('E2E仙人')
    await page.click('button:has-text("抽取天赋")')
    await page.waitForTimeout(500)
    await expect(page.locator('.talent-card').first()).toBeVisible()
    await page.click('button:has-text("确认天赋")')
    await page.waitForTimeout(500)
    await expect(page.locator('.attr-allocator')).toBeVisible()

    const startBtn = page.locator('button:has-text("开始修仙")')
    await expect(startBtn).toBeVisible()
  })

  test('backend API proxy works', async ({ page }) => {
    const response = await page.request.post('/api/v1/game/start', {
      data: {
        name: 'APITest',
        gender: '男',
        talent_card_ids: ['f01', 'l02', 'x01'],
        attributes: { root_bone: 3, comprehension: 3, mindset: 2, luck: 2 },
      },
    })
    expect(response.ok()).toBeTruthy()
    const body = await response.json()
    expect(body.session_id).toBeTruthy()
    expect(body.state.name).toBe('APITest')

    const lbResponse = await page.request.get('/api/v1/game/leaderboard')
    expect(lbResponse.ok()).toBeTruthy()
  })
})
