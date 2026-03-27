# Windows 交互语音助手

通过语音或文本指令控制 Windows 系统的智能助手，支持应用管理、系统控制、文件操作、定时提醒等功能。

## 功能特性

### 语音控制
- **唤醒词检测** — 支持配置唤醒词，唤醒后说出指令
- **语音识别** — 使用 Google 语音识别引擎，支持中文
- **双模式输入** — 语音模式和文本模式可随时切换

### 应用管理
- **打开/关闭应用** — 语音或文本指令打开/关闭任意应用
- **应用扫描** — 自动扫描本地已安装程序并注册到指令系统
- **智能匹配** — 支持中文名、英文名、别名等多种唤起方式

### 系统控制
- 音量调节
- 记事本、计算器、文件管理器等系统工具快速打开
- 支持扩展插件自定义指令

### 反馈机制
- TTS 语音播报执行结果
- Windows 通知栏实时通知

## 支持的指令

| 指令示例 | 说明 |
|---------|------|
| 打开 记事本 | 打开记事本 |
| 关闭 计算器 | 关闭计算器 |
| 设置 音量 50 | 设置音量为 50% |
| 定时 5 分钟 | 设置 5 分钟定时提醒 |
| 存入文件夹 C:\test 内容 测试文本 | 保存文本到文件夹 |
| 列出应用 | 显示已注册应用列表 |
| 检查应用 VSCode | 查询应用是否已安装 |
| 退出 | 退出程序 |

## 环境要求

- Windows 10/11
- Python 3.10+
- 麦克风（用于语音模式）

## 安装依赖

```powershell
pip install sounddevice SpeechRecognition pyyaml win10toast
```

## 运行

```powershell
python src/main.py
```

## 使用方式

### 文本模式（默认）
启动后直接输入指令，如 `打开微信`

### 语音模式
1. 输入 `1` 切换到语音模式
2. 说出 **唤醒词 + 指令**，如 `你好小猪打开微信`
3. 输入 `0` 切回文本模式

### 配置文件

`config/config.json` 可配置以下选项：

```json
{
    "wake_words": ["你好小猪"],
    "language": "zh-CN",
    "tts_engine": "pyttsx3",
    "intents_path": "data/intents.json",
    "plugin_path": "plugins",
    "log_file": "assistant.log",
    "app_map_path": "config/app_map.json"
}
```

## 项目结构

```
Windows-interact-assistant/
├── config/
│   ├── config.json      # 主配置文件
│   └── app_map.json     # 应用路径映射
├── data/
│   └── intents.json     # 意图定义
├── plugins/
│   └── example_plugin.py # 插件示例
├── src/
│   ├── main.py          # 程序入口
│   ├── config.py        # 配置加载
│   ├── executor.py      # 指令执行
│   ├── intents.py       # 意图解析
│   ├── plugins.py       # 插件管理
│   ├── recognize.py      # 语音识别
│   ├── feedback.py       # 反馈（TTS/通知）
│   └── logger.py        # 日志
└── README.md
```

## 扩展插件

在 `plugins/` 目录下创建 `.py` 文件，需包含：

```python
intent_name = 'my_command'

def execute(slots):
    return '执行结果'
```

插件被加载后，通过意图名称自动触发。

## 扩展意图

编辑 `data/intents.json` 添加自定义意图模式：

```json
[
    {
        "name": "my_intent",
        "patterns": ["我的指令(\\w+)"],
        "slots": {"keyword": "(\\w+)"}
    }
]
```

## License

MIT
