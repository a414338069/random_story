export const REALMS = ['凡人', '炼气', '筑基', '金丹', '元婴', '化神', '合体', '大乘', '渡劫飞升'] as const

export const REALM_TIERS: Record<string, { name: string; realms: string[] }> = {
  '低阶': { name: '低阶·入道', realms: ['凡人', '炼气', '筑基'] },
  '中阶': { name: '中阶·显威', realms: ['金丹', '元婴', '化神'] },
  '高阶': { name: '高阶·超脱', realms: ['合体', '大乘', '渡劫飞升'] },
}
