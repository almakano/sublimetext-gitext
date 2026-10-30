"""Запуск git, поиск папки репозитория и кэш статуса для команд GitExt."""

import os
import subprocess
import threading
import time

import sublime

STATUS_CODES = " MADRCUT?!"

# Ключи lastCheck/output оставлены для старых копий функции после перезагрузки плагина
git_status_cache = { 'lastCheck': 0, 'output': None }

def windows_startupinfo():
    """STARTUPINFO со скрытым окном консоли; None вне Windows."""
    if os.name != "nt":
        return None
    startupinfo = subprocess.STARTUPINFO()
    startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
    startupinfo.wShowWindow = subprocess.SW_HIDE
    return startupinfo

def get_git_status(folder):

    cached = git_status_cache.get(folder)
    # 55 > 56-5
    if isinstance(cached, dict) and cached.get('lastCheck', 0) > (time.time() - 5):
        print('GitExt', 'checking status', 'use cached')
        return cached.get('output', '')

    print('GitExt', 'checking status')
    try:
        output = subprocess.check_output(
            ["git", "-c", "core.quotepath=false", "status", "--porcelain"],
            cwd=folder,
            stderr=subprocess.STDOUT,
            startupinfo=windows_startupinfo()
        ).decode().strip()
        git_status_cache[folder] = { 'lastCheck': time.time(), 'output': output }
        print('GitExt', 'status', bool(output))
        return output
    except subprocess.CalledProcessError as e:
        error = e.output.decode('utf-8')
    except Exception as e:
        error = str(e)
    git_status_cache[folder] = { 'lastCheck': time.time(), 'output': error }
    print('GitExt', 'status error', error)
    return error

def get_git_status_lines(folder):
    """Строки git status --porcelain без сообщений git об ошибках."""
    lines = []
    for line in get_git_status(folder).splitlines():
        if len(line) > 3 and line[2] == " " and line[0] in STATUS_CODES and line[1] in STATUS_CODES:
            lines.append(line)
    return lines

def find_folder(window, file_path):
    normalized = os.path.normcase(file_path)
    for folder in window.folders():
        if normalized.startswith(os.path.normcase(folder)):
            return folder
    return None

def resolve_folder(window, paths=None):
    """Папка по выбранным путям, иначе по активному файлу, иначе первая в окне."""
    for path in paths or []:
        folder = find_folder(window, path)
        if folder:
            return folder
    view = window.active_view()
    if view and view.file_name():
        folder = find_folder(window, view.file_name())
        if folder:
            return folder
    folders = window.folders()
    return folders[0] if folders else None

def run_git_sync(cmd, cwd):
    """Вызов git, результат которого нужен сразу: проверки is_enabled и подобные."""
    return subprocess.check_output(
        ["git"] + cmd, cwd=cwd, stderr=subprocess.STDOUT, startupinfo=windows_startupinfo()
    ).decode()

def run_git_command(cmd, cwd, callback=None):
    def worker():
        sublime.set_timeout(lambda: print('GitExt request', cmd, cwd), 0)
        try:
            output = run_git_sync(cmd, cwd)
            sublime.set_timeout(lambda: print('GitExt response', output[:100]), 0)
            if callback:
                sublime.set_timeout(lambda: callback(output, None), 0)
        except subprocess.CalledProcessError as e:
            error = e.output.decode()
            sublime.set_timeout(lambda: print('GitExt subprocess error', error), 0)
            if callback:
                sublime.set_timeout(lambda: callback(None, error), 0)
        except Exception as e:
            error = str(e)
            sublime.set_timeout(lambda: print('GitExt worker error', error), 0)
            if callback:
                sublime.set_timeout(lambda: callback(None, error), 0)

    thread = threading.Thread(target=worker)
    thread.start()
