import type { NormalizedGameState, PlayerStatePydantic, GameStateDict } from './types'

export function normalizeFromPydantic(state: PlayerStatePydantic): NormalizedGameState {
  return {
    sessionId: state.id,
    name: state.name,
    gender: state.gender,
    talentIds: state.talent_ids,
    attributes: {
      rootBone: state.root_bone,
      comprehension: state.comprehension,
      mindset: state.mindset,
      luck: state.luck,
    },
    realm: state.realm,
    realmProgress: state.realm_progress,
    cultivation: state.cultivation ?? 0,
    age: state.age ?? 0,
    lifespan: state.lifespan,
    faction: state.faction,
    spiritStones: state.spirit_stones,
    techniques: state.techniques,
    inventory: state.inventory,
    eventCount: state.event_count,
    isAlive: state.is_alive,
    ascended: false,
    score: state.score,
    endingId: state.ending_id,
    tags: state.tags,
    story_memory: state.story_memory,
  }
}

export function normalizeFromDict(state: GameStateDict): NormalizedGameState {
  return {
    sessionId: state.session_id,
    name: state.name,
    gender: state.gender,
    talentIds: state.talent_ids,
    attributes: {
      rootBone: state.attributes.rootBone,
      comprehension: state.attributes.comprehension,
      mindset: state.attributes.mindset,
      luck: state.attributes.luck,
    },
    realm: state.realm,
    realmProgress: state.realm_progress,
    cultivation: state.cultivation,
    age: state.age,
    lifespan: state.lifespan,
    faction: state.faction,
    spiritStones: state.spirit_stones,
    techniques: state.techniques,
    inventory: state.inventory,
    eventCount: state.event_count,
    isAlive: state.is_alive,
    ascended: state.ascended,
    score: 0,
    endingId: null,
    tags: state.tags,
    story_memory: state.story_memory,
  }
}
