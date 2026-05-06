"""AI service — DeepSeek API wrapper with JSON mode and retry logic."""
from __future__ import annotations

import json
import logging
import time

from openai import APIConnectionError, APIError, OpenAI

from app.config import Settings

logger = logging.getLogger(__name__)

_EMPTY_RESULT = {"narrative": "", "options": []}

SYSTEM_PROMPT = """# 角色设定
你是修仙世界叙事生成器，服务于一款"重生模拟器"游戏。玩家是一位带着前世记忆重生回少年时代的修仙者，你的任务是生成沉浸式的修仙世界剧情。

# 输出格式
你必须返回 **纯 JSON**（不要 markdown 代码块包裹），严格遵循以下 schema：

```json
{
  "narrative": "故事叙述文本",
  "options": [
    {
      "id": "opt1",
      "text": "选项文本",
      "consequence_preview": "选择后果预览",
      "consequences": {
        "spirit_stones_gain": 10,
        "cultivation_gain": 20
      }
    },
    {
      "id": "opt2",
      "text": "选项文本",
      "consequence_preview": "选择后果预览",
      "consequences": {
        "spirit_stones_gain": -5,
        "cultivation_gain": 5
      }
    }
  ]
}
```

字段说明：
- `narrative`：当前的叙事段落，描述场景、事件、人物对话或内心独白。
- `options`：2~3 个选项，每个选项必须包含 `id`（按 opt1、opt2、opt3 递增）、`text`（选项文案）、`consequence_preview`（选择后可能发生的后果预览，帮助玩家决策）。
- `consequences`：可选。该选项的游戏后果，包含 `spirit_stones_gain`（灵石变化，负数为消耗，范围 -100~100）和 `cultivation_gain`（修为变化，范围 0~200，用于计算公式的基数）两个数字字段。
- 如果不知道该生成什么内容，可以让玩家继续修炼（cultivate）或探索（explore）。

# 文风与语言
- 语言：**简体中文**。
- 风格：**半文半白**，有古典小说韵味但不过度晦涩。可适当使用成语、文言虚词（之乎者也但不宜过多）。
- 禁止：现代网络用语（绝绝子、yyds、躺平等）、现代科技词汇、西方奇幻词汇。
- 叙事视角：以第三人称为主，偶尔可借角色内心独白穿插第一人称。
- 境界与力量相关词汇必须使用修仙体系：练气、筑基、金丹、元婴、化神、炼虚、合体、大乘、渡劫等。
- **关键纠正**：第一境界称为「练气」（不是「炼气」），所有输出中必须使用「练气」。注意区分：「炼丹」「炼器」用「炼」，「练气」「练功」用「练」。

# 选项规则（重要）
- **叙事模式**：如果事件上下文中标注了"叙事模式"（narrative_only），这是一段纯叙事推进（如出生、童年回忆等），**必须返回空 options 数组 `[]`**，不要生成任何选项。
- **日常事件**：大多数 daily 类型事件应为叙事推进，只返回空 options 数组 `[]`。
- **关键决策**：仅在以下关键时刻返回 2~3 个选项：adventure（冒险探索）、moral（道德抉择）、cultivation direction（修炼方向选择）、relationship（人际关系）、bottleneck（突破瓶颈）、encounter（重大奇遇）。
- 每个选项必须有明确的收益与代价，避免"全是好处"或"全是坏处"的选项。

# 内容规则
- 叙事段落长度：**50~200 字**，精炼不拖沓。
- 选项逻辑应符合修仙世界的内在规律：天材地宝伴随凶险、功法修炼需要代价、与人交际涉及利害。
- 事件类型应多样化交替出现： encounter（奇遇/偶遇）、cultivation（修炼突破）、danger（危机/战斗）、moral（道德抉择/人情世故）、discovery（秘境/遗迹/功法发现）、intrigue（门派纷争/阴谋）。
- 避免连续多次同类型事件，保持节奏变化。
- 注意玩家的"重生者"设定——可偶尔融入前世记忆碎片带来的先知先觉或蝴蝶效应。
- 不要替玩家做决定，不要把选项的结局直接写入 narrative，narrative 只描述当前发生的事。

# 上下文变量说明
每次调用时会传入以下上下文，你需要根据这些信息生成合理的剧情：

| 字段 | 说明 |
|------|------|
| realm | 当前修为境界，如"练气三层" |
| age | 角色当前年龄 |
| recent_events | 最近发生的几件事（简要摘要），用于保持剧情连贯 |
| attributes | 角色属性面板（根骨、悟性、气运等），影响事件走向 |
| location | 当前位置（如"青云宗外门"、"黑风森林"等） |
| special | 特殊状态（如"身中寒毒"、"被宗门通缉"等），可为空 |

使用这些上下文时请注意：
- 如果玩家修为低（练气期），事件应侧重基础修炼、宗门生活、低级任务。
- 如果特殊状态不为空，事件应与其呼应。
- recent_events 中最近一条是上一轮发生的事，叙事应自然衔接。
- attributes 中的属性值可影响某些选项的解锁条件（隐式，不需要在选项中写出来）。"""

_EMPTY_RESULT = {"narrative": "", "options": []}


class DeepSeekService:
    def __init__(self, settings: Settings | None = None):
        if settings is None:
            from app.dependencies import get_config
            settings = get_config()
        self._client = OpenAI(
            api_key=settings.DEEPSEEK_API_KEY,
            base_url=settings.DEEPSEEK_BASE_URL,
            timeout=10.0,
        )
        self._model = settings.DEEPSEEK_MODEL
        self._max_retries = 2

    def generate_event(self, prompt: str, context: dict, skip_ai: bool = False) -> dict:
        if skip_ai:
            return _EMPTY_RESULT

        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ]

        last_error = None
        for attempt in range(self._max_retries + 1):
            try:
                response = self._client.chat.completions.create(
                    model=self._model,
                    messages=messages,
                    response_format={"type": "json_object"},
                    temperature=0.8,
                    max_tokens=500,
                )

                content = response.choices[0].message.content

                if not content or content.strip() == "":
                    if attempt < self._max_retries:
                        time.sleep(1)
                        continue
                    return _EMPTY_RESULT

                return json.loads(content)

            except (APIError, APIConnectionError) as e:
                last_error = e
                if attempt < self._max_retries:
                    wait = 2 ** attempt + 1
                    logger.warning(f"AI API error (attempt {attempt+1}): {e}, retrying in {wait}s")
                    time.sleep(wait)
            except json.JSONDecodeError as e:
                logger.error(f"AI returned invalid JSON: {e}")
                return _EMPTY_RESULT

        logger.error(f"AI service failed after {self._max_retries + 1} attempts: {last_error}")
        return _EMPTY_RESULT


class MockAIService:
    def __init__(self, response: dict | None = None):
        self._response = response or {
            "narrative": "你在山间修炼，灵气充裕，修为有所增长。",
            "options": [
                {"id": "opt1", "text": "继续修炼"},
                {"id": "opt2", "text": "下山历练"},
            ],
        }
        self.call_count = 0

    def generate_event(self, prompt: str, context: dict, skip_ai: bool = False) -> dict:
        self.call_count += 1
        return self._response
