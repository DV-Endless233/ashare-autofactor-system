# Codex Responses API 连通性测试

## 用途
当需要验证 dvcoder 的 GPT 账号（openai-codex OAuth 提供者）是否能正常工作时，
使用本方法直接测试 API。适用于用户更换账号/恢复账号后验证。

## 测试过程

注意 ChatGPT Codex 使用 Responses API，**不是** Chat Completions API。

### 正确的 API 参数
- **Endpoint**: `https://chatgpt.com/backend-api/codex/responses`
- **必须参数**：
  - `store: False` — Codex 后端要求显式关闭存储
  - `stream: True` — Codex 后端要求显式开启流式
- **不支持**的参数（去掉否则报 400）：
  - `temperature` — 不支持
  - `max_output_tokens` — 不支持（用 `max_tokens` 也不行）
- **input 格式**：`[{"role": "user", "content": "..."}]`（list 形式）

### Python 测试脚本

```python
import urllib.request, json, os

with open(os.path.expanduser("${HERMES_HOME}/profiles/dvcoder/auth.json")) as f:
    auth = json.load(f)
access_token = auth["providers"]["openai-codex"]["tokens"]["access_token"]

url = "https://chatgpt.com/backend-api/codex/responses"
payload = json.dumps({
    "model": "gpt-5.5",
    "input": [{"role": "user", "content": "Say exactly 'HVPN test OK' if you can hear me, nothing else."}],
    "store": False,
    "stream": True,
}).encode()

req = urllib.request.Request(url, data=payload, headers={
    "Authorization": f"Bearer {access_token}",
    "Content-Type": "application/json",
}, method="POST")

with urllib.request.urlopen(req, timeout=60) as resp:
    raw = resp.read().decode()
    # 从 SSE 事件中提取文本
    text_parts = []
    for line in raw.split('\n'):
        if line.startswith('data: '):
            evt = json.loads(line[6:])
            if evt.get('type') == 'response.output_text.delta':
                text_parts.append(evt.get('delta', ''))
    print(''.join(text_parts))
```

### 使用管道测试

也可以用管道直接测试：
```bash
PYTHONPATH=${PROJECT_ROOT} python3 test_script.py
```

如果返回 "HVPN test OK" 则账号正常。
