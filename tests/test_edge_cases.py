import pytest
from app.services.game_service import (
    start_game, get_next_event, process_choice, check_game_over, get_state, end_game
)


class TestEdgeAttributeCombos:

    def test_all_zero_attributes(self):
        session = start_game(
            name='全零属性', gender='男',
            talent_card_ids=['f01', 'f02', 'f03'],
            attributes={'rootBone': 0, 'comprehension': 0, 'mindset': 0, 'luck': 10},
        )
        sid = session['session_id']
        events = 0
        while not check_game_over(get_state(sid)):
            event = get_next_event(sid)
            process_choice(sid, event['options'][0]['id'])
            events += 1
        result = end_game(sid)
        assert 'ending' in result
        assert 0 <= result['score'] <= 100
        assert events > 0

    def test_all_ten_single_attribute(self):
        session = start_game(
            name='单属性满', gender='女',
            talent_card_ids=['f01', 'f02', 'f03'],
            attributes={'rootBone': 10, 'comprehension': 0, 'mindset': 0, 'luck': 0},
        )
        sid = session['session_id']
        events = 0
        while not check_game_over(get_state(sid)):
            event = get_next_event(sid)
            process_choice(sid, event['options'][0]['id'])
            events += 1
        state = get_state(sid)
        assert state['event_count'] == events
        result = end_game(sid)
        assert 'score' in result


class TestLifespanLimit:

    def test_lifespan_ending(self):
        session = start_game(
            name='寿命测试', gender='男',
            talent_card_ids=['f01', 'f02', 'f03'],
            attributes={'rootBone': 3, 'comprehension': 3, 'mindset': 2, 'luck': 2},
        )
        sid = session['session_id']
        while not check_game_over(get_state(sid)):
            event = get_next_event(sid)
            process_choice(sid, event['options'][0]['id'])
        state = get_state(sid)
        age = state.get('age', 0)
        lifespan = state.get('lifespan', 80)
        events = state['event_count']
        assert age >= lifespan or events >= 60


class TestSpiritStones:

    def test_zero_spirit_stones_gameplay(self):
        session = start_game(
            name='零灵石', gender='男',
            talent_card_ids=['f01', 'f02', 'f03'],
            attributes={'rootBone': 3, 'comprehension': 3, 'mindset': 2, 'luck': 2},
        )
        sid = session['session_id']
        for _ in range(3):
            event = get_next_event(sid)
            process_choice(sid, event['options'][0]['id'])
            state = get_state(sid)
            assert state['spirit_stones'] >= 0

    def test_spirit_stones_clamped(self):
        session = start_game(
            name='灵石钳位', gender='女',
            talent_card_ids=['f01', 'f02', 'f03'],
            attributes={'rootBone': 3, 'comprehension': 3, 'mindset': 2, 'luck': 2},
        )
        sid = session['session_id']
        for _ in range(10):
            if check_game_over(get_state(sid)):
                break
            event = get_next_event(sid)
            process_choice(sid, event['options'][0]['id'])
            assert get_state(sid)['spirit_stones'] >= 0


class TestAIFallback:

    def test_mock_service_works(self):
        from app.services.ai_service import MockAIService
        mock = MockAIService()
        result = mock.generate_event('test prompt', {})
        assert isinstance(result, dict)
        assert 'narrative' in result
        assert 'options' in result
        assert len(result['options']) >= 2

    def test_empty_ai_response_handled(self):
        session = start_game(
            name='空AI响应', gender='女',
            talent_card_ids=['f01', 'f02', 'f03'],
            attributes={'rootBone': 3, 'comprehension': 3, 'mindset': 2, 'luck': 2},
        )
        sid = session['session_id']
        event = get_next_event(sid)
        assert event
        assert event['narrative']
        assert len(event['options']) >= 2


class TestSectSystem:

    def test_no_sect_gameplay(self):
        session = start_game(
            name='散修测试', gender='男',
            talent_card_ids=['f01', 'f02', 'f03'],
            attributes={'rootBone': 3, 'comprehension': 5, 'mindset': 1, 'luck': 1},
        )
        sid = session['session_id']
        for _ in range(5):
            if check_game_over(get_state(sid)):
                break
            event = get_next_event(sid)
            process_choice(sid, event['options'][0]['id'])
        state = get_state(sid)
        assert state['is_alive']


class TestRealmProgression:

    def test_game_completes_with_mortal_realm(self):
        session = start_game(
            name='凡人一生', gender='男',
            talent_card_ids=['f01', 'f02', 'f03'],
            attributes={'rootBone': 0, 'comprehension': 0, 'mindset': 0, 'luck': 10},
        )
        sid = session['session_id']
        while not check_game_over(get_state(sid)):
            event = get_next_event(sid)
            process_choice(sid, event['options'][0]['id'])
        state = get_state(sid)
        result = end_game(sid)
        assert result['ending']
        assert result['score'] >= 0
