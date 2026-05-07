# Issues — ai-narrative-aftermath-fix

## Known Gotchas
- except Exception: pass 在现有代码中有8处静默吞异常
- as any 在前端代码中有4处
- 确保 `check_narrative_option_alignment` 不引入第三方NLP库
