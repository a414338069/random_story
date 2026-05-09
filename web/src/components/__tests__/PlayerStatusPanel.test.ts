import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import {
  NDrawer,
  NDrawerContent,
  NTag,
  NProgress,
  NDivider,
  NSpace,
  NText,
} from 'naive-ui'
import PlayerStatusPanel from '@/components/PlayerStatusPanel.vue'
import type { NormalizedGameState } from '@/core/types'

const mockGameState: NormalizedGameState = {
  sessionId: 'test-session-001',
  name: '测试修士',
  gender: '男',
  talentIds: ['f01', 'l02'],
  attributes: { rootBone: 8, comprehension: 6, mindset: 5, luck: 4 },
  realm: '金丹',
  realmProgress: 0.45,
  cultivation: 1200,
  age: 25,
  lifespan: 200,
  faction: '青云宗',
  spiritStones: 500,
  techniques: ['青云剑法', '炎火术'],
  techniqueGrades: ['灵品', '凡品'],
  inventory: ['回春丹', '破境丹', '灵石袋'],
  eventCount: 12,
  isAlive: true,
  ascended: false,
  score: 0,
  endingId: null,
}

function mountPanel(visible = true, overrides?: Partial<NormalizedGameState>) {
  const gameState = { ...mockGameState, ...overrides }
  return mount(PlayerStatusPanel, {
    props: { visible, gameState },
    global: {
      components: {
        NDrawer,
        NDrawerContent,
        NTag,
        NProgress,
        NDivider,
        NSpace,
        NText,
      },
    },
  })
}

function bodyText() {
  return document.body.textContent ?? ''
}

describe('PlayerStatusPanel', () => {
  describe('mounting', () => {
    it('mounts without error when visible is true', () => {
      const wrapper = mountPanel(true)
      expect(wrapper.vm).toBeDefined()
    })

    it('mounts without error when visible is false', () => {
      const wrapper = mountPanel(false)
      expect(wrapper.vm).toBeDefined()
    })

    it('passes visible prop to NDrawer via show', () => {
      const wrapper = mountPanel(true)
      const drawer = wrapper.findComponent(NDrawer)
      expect(drawer.props('show')).toBe(true)
    })

    it('passes false show to NDrawer when hidden', () => {
      const wrapper = mountPanel(false)
      const drawer = wrapper.findComponent(NDrawer)
      expect(drawer.props('show')).toBe(false)
    })
  })

  describe('Section 1 — 基本信息', () => {
    it('renders name field', async () => {
      mountPanel()
      await new Promise(r => setTimeout(r, 10))
      expect(bodyText()).toContain('测试修士')
    })

    it('renders gender field', async () => {
      mountPanel()
      await new Promise(r => setTimeout(r, 10))
      expect(bodyText()).toContain('男')
    })

    it('renders realm with tag', async () => {
      mountPanel()
      await new Promise(r => setTimeout(r, 10))
      expect(bodyText()).toContain('金丹')
    })

    it('renders faction', async () => {
      mountPanel()
      await new Promise(r => setTimeout(r, 10))
      expect(bodyText()).toContain('青云宗')
    })

    it('shows 散修 when faction is empty', async () => {
      mountPanel(true, { faction: '' })
      await new Promise(r => setTimeout(r, 10))
      expect(bodyText()).toContain('散修')
    })
  })

  describe('Section 2 — 四维属性', () => {
    it('renders all four attribute labels', async () => {
      mountPanel()
      await new Promise(r => setTimeout(r, 10))
      const text = bodyText()
      expect(text).toContain('根骨')
      expect(text).toContain('悟性')
      expect(text).toContain('心境')
      expect(text).toContain('气运')
    })

    it('renders attribute values', async () => {
      mountPanel()
      await new Promise(r => setTimeout(r, 10))
      const text = bodyText()
      expect(text).toContain('8 / 10')
      expect(text).toContain('6 / 10')
      expect(text).toContain('5 / 10')
      expect(text).toContain('4 / 10')
    })
  })

  describe('Section 3 — 天赋', () => {
    it('renders matched talent names', async () => {
      mountPanel()
      await new Promise(r => setTimeout(r, 10))
      const text = bodyText()
      expect(text).toContain('粗壮体魄')
      expect(text).toContain('过人悟性')
    })

    it('renders talent grades', async () => {
      mountPanel()
      await new Promise(r => setTimeout(r, 10))
      const text = bodyText()
      expect(text).toContain('凡品')
      expect(text).toContain('灵品')
    })

    it('shows 无天赋 when no talents', async () => {
      mountPanel(true, { talentIds: [] })
      await new Promise(r => setTimeout(r, 10))
      expect(bodyText()).toContain('无天赋')
    })

    it('renders effects summary', async () => {
      mountPanel()
      await new Promise(r => setTimeout(r, 10))
      const text = bodyText()
      expect(text).toContain('根骨+1')
      expect(text).toContain('悟性+3')
    })

    it('handles talents with no attr bonuses', async () => {
      mountPanel(true, { talentIds: ['f05'] })
      await new Promise(r => setTimeout(r, 10))
      const text = bodyText()
      expect(text).toContain('灵根初显')
      expect(text).toContain('特殊效果')
    })
  })

  describe('Section 4 — 物品与资源', () => {
    it('renders spirit stones', async () => {
      mountPanel()
      await new Promise(r => setTimeout(r, 10))
      expect(bodyText()).toContain('500')
    })

    it('renders inventory count', async () => {
      mountPanel()
      await new Promise(r => setTimeout(r, 10))
      expect(bodyText()).toContain('3 件物品')
    })

    it('renders techniques count', async () => {
      mountPanel()
      await new Promise(r => setTimeout(r, 10))
      expect(bodyText()).toContain('2 种')
    })

    it('shows 0 items for empty inventory', async () => {
      mountPanel(true, { inventory: [], techniques: [], spiritStones: 0 })
      await new Promise(r => setTimeout(r, 10))
      const text = bodyText()
      expect(text).toContain('0 件物品')
      expect(text).toContain('0 种')
      expect(text).toContain('0')
    })
  })

  describe('Section 5 — 状态', () => {
    it('renders age / lifespan', async () => {
      mountPanel()
      await new Promise(r => setTimeout(r, 10))
      expect(bodyText()).toContain('25 / 200')
    })

    it('renders cultivation value', async () => {
      mountPanel()
      await new Promise(r => setTimeout(r, 10))
      expect(bodyText()).toContain('1,200')
    })

    it('renders realm progress percentage', async () => {
      mountPanel()
      await new Promise(r => setTimeout(r, 10))
      expect(bodyText()).toContain('45%')
    })
  })

  describe('events', () => {
    it('emits update:visible when drawer closes', () => {
      const wrapper = mountPanel(true)
      const drawer = wrapper.findComponent(NDrawer)
      drawer.vm.$emit('update:show', false)
      expect(wrapper.emitted('update:visible')).toBeTruthy()
      expect(wrapper.emitted('update:visible')?.[0]).toEqual([false])
    })
  })
})
