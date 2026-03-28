import os
import shutil
import subprocess
import threading
import time
import ctypes
import sys


DEFAULT_APP_MAP = {
    # 系统工具
    '记事本': 'notepad.exe',
    'notepad': 'notepad.exe',
    '记事本.exe': 'notepad.exe',
    '计算器': 'calc.exe',
    'calculator': 'calc.exe',
    '计算器.exe': 'calc.exe',
    '资源管理器': 'explorer.exe',
    'explorer': 'explorer.exe',
    '任务管理器': 'taskmgr.exe',
    'cmd': 'cmd.exe',
    'powershell': 'powershell.exe',

    # 浏览器
    '浏览器': 'C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe',
    'chrome': 'C:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe',
    '谷歌浏览器': 'C:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe',
    'googlechrome': 'C:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe',
    'edge': 'msedge',
    '微软边缘': 'msedge',
    'firefox': 'C:\\Program Files\\Mozilla Firefox\\firefox.exe',
    '火狐': 'C:\\Program Files\\Mozilla Firefox\\firefox.exe',

    # 开发工具
    'vscode': 'C:\\Program Files\\Microsoft VS Code\\Code.exe',
    'visualstudio': 'C:\\Program Files (x86)\\Microsoft Visual Studio\\2019\\Community\\Common7\\IDE\\devenv.exe',
    'vs code': 'C:\\Program Files\\Microsoft VS Code\\Code.exe',
    'code': 'code',

    # 通讯工具
    '微信': 'C:\\Program Files\\Tencent\\Weixin\\Weixin.exe',
    'wechat': 'C:\\Program Files\\Tencent\\Weixin\\Weixin.exe',
    'weixin': 'C:\\Program Files\\Tencent\\Weixin\\Weixin.exe',
    'qq': 'C:\\Program Files (x86)\\Tencent\\QQ\\Bin\\QQ.exe',
    '企业微信': 'C:\\Program Files (x86)\\Tencent\\WeChatWork\\wxwork.exe',
    '钉钉': 'C:\\Program Files (x86)\\DingTalk\\DingTalk.exe',
    '飞书': 'C:\\Program Files\\Lark\\lark.exe',
    'dingtalk': 'C:\\Program Files (x86)\\DingTalk\\DingTalk.exe',


    # 办公
    'word': 'C:\\Program Files\\Microsoft Office\\root\\Office16\\WINWORD.EXE',
    'excel': 'C:\\Program Files\\Microsoft Office\\root\\Office16\\EXCEL.EXE',
    'ppt': 'C:\\Program Files\\Microsoft Office\\root\\Office16\\POWERPNT.EXE',
    'outlook': 'C:\\Program Files\\Microsoft Office\\root\\Office16\\OUTLOOK.EXE',

    # 媒体
    '音乐': 'C:\\Program Files\\Windows Media Player\\wmplayer.exe',
    'windows media player': 'C:\\Program Files\\Windows Media Player\\wmplayer.exe',
    'vlc': 'C:\\Program Files\\VideoLAN\\VLC\\vlc.exe',
    '爱奇艺': 'C:\\Program Files\\iQIYI\\iQIYI.exe',
    '抖音': 'C:\\Program Files (x86)\\ByteDance\\douyin\\douyin.exe',
    'douyin': 'C:\\Program Files (x86)\\ByteDance\\douyin\\douyin.exe',

    # 其他
    '画图': 'mspaint.exe',
    '剪贴板': 'C:\\Windows\\System32\\cmd.exe /c clip',
    '记事本++': 'C:\\Program Files\\Notepad++\\notepad++.exe',
    'notepad++': 'C:\\Program Files\\Notepad++\\notepad++.exe',
    '迅雷': 'C:\\Program Files (x86)\\Thunder Network\\Thunder\\Program\\Thunder.exe',
    '微信读书': 'C:\\Program Files\\Tencent\\QQBrowser\\Application\\qqbrowser.exe',
}
APP_MAP = DEFAULT_APP_MAP.copy()

APP_ALIAS_MAP = {
    '微信': 'wechat',
    '企业微信': 'wechatwork',
    '钉钉': 'dingtalk',
    '飞书': 'lark',
    '迅雷': 'thunder',
    '火狐': 'firefox',
    '谷歌浏览器': 'chrome',
    '浏览器': 'chrome',
    '微软边缘': 'msedge',
    '记事本': 'notepad',
    '计算器': 'calc',
    '资源管理器': 'explorer',
}

APP_SEARCH_PATHS = [
    os.environ.get('ProgramFiles', 'C:\\Program Files'),
    os.environ.get('ProgramFiles(x86)', 'C:\\Program Files (x86)'),
    os.environ.get('LocalAppData', ''),
]


def find_app_in_program_files(app_name):
    normalized = app_name.strip().lower()
    if not normalized:
        return None

    candidate_tokens = set()
    candidate_tokens.add(normalized)
    candidate_tokens.add(normalized.replace(' ', ''))
    candidate_tokens.add(normalized.replace(' ', '').replace('程', ''))

    alias = APP_ALIAS_MAP.get(normalized)
    if alias:
        candidate_tokens.add(alias)

    # 部分名字可能提取为英文单词，如 微信->wechat、企业微信->wechatwork
    if normalized in APP_ALIAS_MAP:
        candidate_tokens.add(APP_ALIAS_MAP[normalized])

    for root in APP_SEARCH_PATHS:
        if not root or not os.path.isdir(root):
            continue
        try:
            for dirpath, dirnames, filenames in os.walk(root):
                lower_path = dirpath.lower()
                path_token_match = any(tok in lower_path for tok in candidate_tokens)
                if path_token_match:
                    for file in filenames:
                        if not file.lower().endswith('.exe'):
                            continue
                        file_lower = file.lower()
                        if any(tok in file_lower for tok in candidate_tokens):
                            return os.path.join(dirpath, file)
                else:
                    # 如果当前目录直接包含可执行文件名关键字也算
                    for file in filenames:
                        if not file.lower().endswith('.exe'):
                            continue
                        file_lower = file.lower()
                        if any(tok in file_lower for tok in candidate_tokens):
                            return os.path.join(dirpath, file)

                # 限制深度避免性能问题
                if dirpath.count(os.sep) - root.count(os.sep) > 3:  # 减少深度
                    dirnames[:] = []
        except (OSError, PermissionError):
            continue  # 跳过无权限目录
    return None


def load_app_map(path=None):
    global APP_MAP
    APP_MAP = DEFAULT_APP_MAP.copy()
    if not path:
        return APP_MAP
    path = os.path.abspath(path)
    if not os.path.exists(path):
        return APP_MAP

    try:
        import json
        with open(path, 'r', encoding='utf-8') as f:
            user_map = json.load(f)
        if isinstance(user_map, dict):
            for k, v in user_map.items():
                if isinstance(k, str) and isinstance(v, str):
                    APP_MAP[k.strip().lower()] = v
    except Exception:
        pass

    return APP_MAP


def list_apps():
    return sorted(APP_MAP.keys())


def scan_programs_folder(folder=None, refresh_map=True, prefix=None):
    """扫描目录下 .exe 并自动添加到 APP_MAP。"""
    folder = folder or os.path.expandvars(r'%LOCALAPPDATA%\\Programs')
    if not folder or not os.path.isdir(folder):
        return []

    if refresh_map:
        load_app_map()  # reset to default + user map

    mapped = []
    for dirpath, dirnames, filenames in os.walk(folder):
        for filename in filenames:
            if not filename.lower().endswith('.exe'):
                continue
            path = os.path.join(dirpath, filename)
            key = os.path.splitext(filename)[0].strip().lower()
            if prefix:
                key = f'{prefix} {key}'.strip()

            if key not in APP_MAP:
                APP_MAP[key] = path
                mapped.append((key, path))

            # 还支持少量直接命令名，如果只包含字母数字
            maybe_cmd = key.replace(' ', '')
            if maybe_cmd != key and maybe_cmd not in APP_MAP:
                APP_MAP[maybe_cmd] = path
                mapped.append((maybe_cmd, path))

    return mapped


def scan_standard_windows_program_files(refresh_map=True):
    """扫描C:\\Program Files 和 C:\\Program Files (x86) 列表并加入 APP_MAP。"""
    if refresh_map:
        load_app_map()

    all_mapped = []
    for base in [r'C:\Program Files', r'C:\Program Files (x86)']:
        if os.path.isdir(base):
            mapped = scan_programs_folder(base, refresh_map=False)
            all_mapped.extend(mapped)
    return all_mapped


def scan_all_program_folders():
    """扫描本地 AppData 和两大 Program Files 目录，并合并到 APP_MAP。"""
    print("Loading app map...")
    load_app_map()
    print("App map loaded")
    mapped = []
    # 只扫描 Local\Programs 在启动时，Program Files 太大
    print("Scanning Local Programs...")
    local_mapped = scan_programs_folder(os.path.expandvars(r'%LOCALAPPDATA%\\Programs'), refresh_map=False)
    mapped.extend(local_mapped)
    print(f"Scanned {len(local_mapped)} from Local Programs")
    return mapped


def check_app_exists(app_name):
    exe = resolve_app_executable(app_name)
    if exe and (os.path.exists(exe) or shutil.which(exe)):
        return True, exe
    return False, None


def resolve_app_executable(app_name):
    """尝试从应用名解析可执行路径或命令。"""
    normalized = normalize_app_name(app_name)

    # 优先绝对路径
    if os.path.isabs(app_name) and os.path.exists(app_name):
        return app_name
    if os.path.isabs(normalized) and os.path.exists(normalized):
        return normalized

    # 针对 edge 进行特化处理，优先官方安装路径，破除 AweSun 等误匹配
    if normalized in ('edge', '微软边缘', 'msedge', 'microsoftedge'):
        for edge_path in [
            r'C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe',
            r'C:\Program Files\Microsoft\Edge\Application\msedge.exe',
        ]:
            if os.path.exists(edge_path):
                return edge_path
        if shutil.which('msedge'):
            return shutil.which('msedge')

    # 映射表命中
    if normalized in APP_MAP:
        candidate = APP_MAP[normalized]
        if os.path.exists(candidate) or shutil.which(candidate):
            return candidate

    # 模糊匹配映射表关键词（优先精确、短名）
    candidate = None
    for key, value in APP_MAP.items():
        if not key or not value:
            continue

        if key == normalized or key.replace(' ', '') == normalized.replace(' ', ''):
            if os.path.exists(value) or shutil.which(value):
                return value
            candidate = value
            break

    if not candidate:
        for key, value in APP_MAP.items():
            if normalized in key.split() or key in normalized.split():
                if os.path.exists(value) or shutil.which(value):
                    return value
                if not any(x in key for x in ('uninstall', 'uninst', 'unins', '卸载', 'remove', 'cleanup', 'setup', 'installer', '安装', '反安装', 'unregister')):
                    candidate = value
                    break

    # 如果模糊匹配返回路径但不可用，继续后续查找
    if candidate and not (os.path.exists(candidate) or shutil.which(candidate)):
        candidate = None

    # 直接候选文件名、命令（normalized 已是小写）
    for candidate in [normalized, f'{normalized}.exe']:
        if os.path.exists(candidate) or shutil.which(candidate):
            return candidate

    # 搜索系统目录（包括别名）
    found = find_app_in_program_files(normalized)
    if found:
        return found

    alias = APP_ALIAS_MAP.get(normalized)
    if alias:
        found = find_app_in_program_files(alias)
        if found:
            return found

    # 如果前面 candidate 为路径但不存在，但命令在 PATH 可用也返回
    if 'candidate' in locals() and candidate and shutil.which(candidate):
        return candidate

    # 最后，尝试模糊匹配最接近的 key（大小写不敏感）
    import difflib
    close_matches = difflib.get_close_matches(normalized, APP_MAP.keys(), n=1, cutoff=0.6)
    if close_matches:
        close_key = close_matches[0]
        candidate = APP_MAP[close_key]
        if os.path.exists(candidate) or shutil.which(candidate):
            return candidate

    return None


def normalize_app_name(app_name):
    if not app_name or not app_name.strip():
        return ''

    normalized = app_name.strip().lower()
    for bad in ['程序', '软件', '应用', '打开', '启动', '请', '帮我']:
        normalized = normalized.replace(bad, '').strip()

    normalized = normalized.strip(' .，。、!！?？')

    return normalized


def open_app(app_name):
    display_name = app_name
    exe = resolve_app_executable(app_name)
    normalized = normalize_app_name(app_name)
    if normalized:
        display_name = normalized

    if not exe:
        return False, f'应用 [{app_name}] 未识别或未安装'

    try:
        if os.path.exists(exe):
            os.startfile(exe)
            return True, f'已打开 {display_name}'

        if shutil.which(exe):
            subprocess.Popen(exe)
            return True, f'已打开 {display_name}'

        # 处理引号路径
        trimmed = exe.strip('"')
        if os.path.exists(trimmed):
            subprocess.Popen([trimmed])
            return True, f'已打开 {display_name}'

        # 可能是带参数的串，但无有效可执行文件时不直接返回成功
        if ' ' in exe and os.path.exists(trimmed):
            subprocess.Popen(f'"{exe}"', shell=True)
            return True, f'已打开 {display_name}'

        return False, f'可执行文件 [{exe}] 不存在，无法打开 {display_name}'
    except Exception as e:
        return False, f'打开 {display_name} 失败：{e}，请确认应用名或路径是否正确'

def close_app(app_name):
    if not app_name:
        return False, '没有指定要关闭的应用'
    # 去除 .exe 后缀，避免 taskkill /im xxx.exe.exe
    app_base = app_name.rstrip('.exe').strip()
    try:
        subprocess.Popen(f'taskkill /im {app_base}.exe /f', shell=True)
        return True, f'已尝试关闭{app_base}'
    except Exception as e:
        return False, f'关闭{app_base}失败：{e}'


def set_volume(value):
    try:
        value = int(value)
    except (ValueError, TypeError):
        value = 50
    value = max(0, min(100, value))
    try:
        from pycaw.pycaw import AudioUtilities
        devices = AudioUtilities.GetSpeakers()
        volume = devices.EndpointVolume
        volume.SetMasterVolumeLevelScalar(value / 100.0, None)
        return True, f'已将音量设置为 {value}%'
    except Exception as e:
        return True, f'请求设置音量到 {value}%'


def set_timer(minutes):
    def _alarm():
        time.sleep(minutes * 60)
        print('定时提醒：时间到！')

    thread = threading.Thread(target=_alarm, daemon=True)
    thread.start()
    return True, f'已设置 {minutes} 分钟定时提醒'


def save_to_folder(folder=None, filepath=None, content=''):
    import os
    from datetime import datetime

    if filepath:
        target = os.path.abspath(filepath)
        folder = os.path.dirname(target)
        filename = os.path.basename(target)
    else:
        folder = os.path.abspath(folder or '.')
        os.makedirs(folder, exist_ok=True)
        filename = datetime.now().strftime('assistant_%Y%m%d_%H%M%S.txt')
        target = os.path.join(folder, filename)

    os.makedirs(folder, exist_ok=True)

    if not content:
        return False, '没有要保存的内容'

    try:
        with open(target, 'w', encoding='utf-8') as f:
            f.write(content)
        return True, f'已保存到 {target}'
    except Exception as e:
        return False, f'保存失败：{e}'


def execute_intent(intent_name, slots):
    if intent_name == 'open_app':
        return open_app(slots.get('app_name', ''))
    if intent_name == 'close_app':
        return close_app(slots.get('app_name', ''))
    if intent_name == 'set_volume':
        return set_volume(slots.get('value', 50))
    if intent_name == 'set_timer':
        return set_timer(slots.get('minutes', 10))
    if intent_name == 'save_to_folder':
        return save_to_folder(
            folder=slots.get('folder'),
            filepath=slots.get('filepath'),
            content=slots.get('content', ''),
        )
    if intent_name == 'list_apps':
        apps = list_apps()
        return True, '已注册应用：' + '、'.join(apps[:50])
    if intent_name == 'check_app':
        exists, path = check_app_exists(slots.get('app_name', ''))
        if exists:
            return True, f'已找到应用，路径/命令：{path}'
        return False, '未找到应用，请确认名称是否正确'
    if intent_name == 'douyin_control':
        return _execute_douyin_control(slots.get('action', ''))

    # 系统控制（支持确认机制）
    from .config import load_config
    cfg = load_config()
    confirm_required = cfg.get('confirm_dangerous_actions', True)

    if intent_name == 'systemShutdown':
        if confirm_required and not confirm_action():
            return False, '已取消关机'
        return system_shutdown()
    if intent_name == 'systemReboot':
        if confirm_required and not confirm_action():
            return False, '已取消重启'
        return system_reboot()
    if intent_name == 'systemLock':
        return system_lock()
    if intent_name == 'systemSleep':
        if confirm_required and not confirm_action():
            return False, '已取消休眠'
        return system_sleep()
    if intent_name == 'open_system_panel':
        return open_system_panel(slots.get('panel', ''))

    return False, '未识别的意图'


def _is_windows():
    return sys.platform == 'win32' or sys.platform == 'cygwin'


def system_shutdown():
    """关机"""
    if not _is_windows():
        return False, '仅支持 Windows 系统'
    try:
        os.system('shutdown /s /t 30')
        return True, '系统将在 30 秒后关机'
    except Exception as e:
        return False, f'关机失败: {e}'


def system_reboot():
    """重启"""
    if not _is_windows():
        return False, '仅支持 Windows 系统'
    try:
        os.system('shutdown /r /t 30')
        return True, '系统将在 30 秒后重启'
    except Exception as e:
        return False, f'重启失败: {e}'


def system_lock():
    """锁屏"""
    if not _is_windows():
        return False, '仅支持 Windows 系统'
    try:
        user32 = ctypes.windll.user32
        result = user32.LockWorkStation()
        if result:
            return True, '已锁定屏幕'
        return False, '锁定屏幕失败'
    except Exception as e:
        return False, f'锁定屏幕失败: {e}'


def system_sleep():
    """休眠/睡眠"""
    if not _is_windows():
        return False, '仅支持 Windows 系统'
    try:
        powrprof = ctypes.windll.powrprof
        result = powrprof.SetSuspendState(False, True, True)
        if result:
            return True, '系统已进入睡眠模式'
        result = powrprof.SetSuspendState(True, True, True)
        if result:
            return True, '系统已进入休眠模式'
        return False, '系统无法进入睡眠/休眠模式'
    except Exception as e:
        return False, f'进入睡眠模式失败: {e}'


def confirm_action():
    """请求用户确认（用于危险操作）"""
    try:
        confirm = input('确定要执行此操作吗？(y/n)：').strip().lower()
        return confirm in ('y', 'yes', '是', '确认')
    except (EOFError, KeyboardInterrupt):
        return False


# 系统面板命令映射表
SYSTEM_PANEL_COMMANDS = {
    '设置': 'start ms-settings:',
    '控制面板': 'control',
    '任务管理器': 'taskmgr',
    '网络设置': 'start ms-settings:network',
    '无线设置': 'start ms-settings:network',
    '蓝牙设置': 'start ms-settings:bluetooth',
    '声音设置': 'start ms-settings:sound',
    '音频设置': 'start ms-settings:sound',
    '显示设置': 'start ms-settings:display',
    '屏幕设置': 'start ms-settings:display',
    '电源设置': 'start ms-settings:powersleep',
    '个性化设置': 'start ms-settings:personalization',
    '主题设置': 'start ms-settings:personalization',
    '应用设置': 'start ms-settings:appsfeatures',
    '应用管理': 'start ms-settings:appsfeatures',
    '任务栏设置': 'start ms-settings:taskbar',
    '投影设置': 'start ms-settings:project',
    '投屏': 'start ms-settings:project',
    '截图': 'snippingtool',
    '截屏': 'snippingtool',
    '清空回收站': 'powershell -Command "Clear-RecycleBin -Force"',
    '浏览器': 'C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe',
}


def open_system_panel(panel_name):
    """打开Windows系统面板或工具"""
    cmd = SYSTEM_PANEL_COMMANDS.get(panel_name)
    if not cmd:
        return False, f'未知系统面板: {panel_name}'
    try:
        subprocess.Popen(cmd, shell=True)
        return True, f'已打开{panel_name}'
    except Exception as e:
        return False, f'打开{panel_name}失败: {e}'


def _execute_douyin_control(action):
    """执行抖音控制命令"""
    try:
        from .nlu.douyin_controller import DouyinController
    except ImportError:
        try:
            from nlu.douyin_controller import DouyinController
        except ImportError:
            return False, f'抖音 [{action}] 控制失败：缺少 pyautogui 依赖（pip install pyautogui）'

    controller = DouyinController()
    if not controller.is_available():
        return False, f'抖音 [{action}] 控制失败：pyautogui 不可用'

    return controller.trigger(action)
