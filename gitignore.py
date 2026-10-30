"""Правила .gitignore для выбранного файла, расширения или директории."""

import os
import threading
import time

import sublime
import sublime_plugin

from .lib.git import find_folder
from .lib.ui import show_popup

# Состояние пунктов меню берётся из кэша: .gitignore читается в отдельном потоке,
# чтобы открытие контекстного меню не ждало диск
CACHE_TTL = 5.0

rules_cache = {}
rules_pending = set()
rules_lock = threading.Lock()


def selected_paths(window, paths=None):
    """Пути из сайдбара, иначе активный файл."""
    if paths:
        return list(paths)
    view = window.active_view()
    if view and view.file_name():
        return [view.file_name()]
    return []


def file_targets(window, paths=None):
    """Пары (корень репозитория, файл) для выбранных файлов."""
    targets = []
    for path in selected_paths(window, paths):
        folder = find_folder(window, path)
        if folder and not os.path.isdir(path):
            targets.append((folder, path))
    return targets


def dir_targets(window, paths=None):
    """Пары (корень репозитория, директория) для выбранных директорий."""
    if paths:
        dirs = [path for path in paths if os.path.isdir(path)]
    else:
        # Без выбора в сайдбаре берём папку активного файла
        dirs = [os.path.dirname(path) for path in selected_paths(window, paths)]

    targets = []
    for path in dirs:
        folder = find_folder(window, path)
        # Правило для корня репозитория не имеет смысла
        if folder and os.path.normcase(os.path.normpath(path)) != os.path.normcase(os.path.normpath(folder)):
            targets.append((folder, path))
    return targets


def rel_path(folder, path):
    return os.path.relpath(path, folder).replace("\\", "/")


def file_rule(folder, path):
    """Правило для файла: путь от корня репозитория."""
    return rel_path(folder, path)


def dir_rule(folder, path):
    """Правило для директории: путь от корня репозитория со слэшем."""
    return rel_path(folder, path).rstrip("/") + "/"


def extension_rule(folder, path):
    """Правило для расширения файла: *.ext."""
    extension = os.path.splitext(os.path.basename(path))[1]
    return "*" + extension if extension else None


def read_rules(folder):
    """Строки .gitignore репозитория."""
    try:
        with open(os.path.join(folder, ".gitignore"), "r", encoding="utf-8") as f:
            return f.read().splitlines()
    except Exception:
        return []


def normalize_rule(rule):
    """Правило без "./", ведущего и завершающего слэша."""
    rule = rule.strip().rstrip("/")
    if rule.startswith("./"):
        rule = rule[2:]
    return rule.lstrip("/")


def parse_rules(lines):
    """Множество правил .gitignore без комментариев и исключений."""
    rules = set()
    for line in lines:
        line = line.strip()
        if line and not line.startswith(("#", "!")):
            rules.add(normalize_rule(line))
    return rules


def has_rule(folder, rule):
    """Есть ли уже такое правило в .gitignore (читает файл)."""
    return normalize_rule(rule) in parse_rules(read_rules(folder))


def cached_rules(folder):
    """Правила из кэша; None, пока .gitignore не прочитан."""
    with rules_lock:
        cached = rules_cache.get(folder)
    return cached["rules"] if cached else None


def is_rules_stale(folder):
    """Нужно ли перечитать .gitignore для кэша."""
    with rules_lock:
        cached = rules_cache.get(folder)
        if not cached:
            return True
        return cached["lastCheck"] < time.time() - CACHE_TTL


def refresh_rules(folder):
    """Читает .gitignore в отдельном потоке, чтобы меню не ждало диск."""
    with rules_lock:
        if folder in rules_pending:
            return
        rules_pending.add(folder)

    def worker():
        try:
            rules = parse_rules(read_rules(folder))
            with rules_lock:
                rules_cache[folder] = {"rules": rules, "lastCheck": time.time()}
        finally:
            with rules_lock:
                rules_pending.discard(folder)

    threading.Thread(target=worker, daemon=True).start()


def remember_rule(folder, rule):
    """Помечает правило добавленным, не дожидаясь перечитывания файла."""
    with rules_lock:
        cached = rules_cache.get(folder)
        if cached:
            cached["rules"].add(normalize_rule(rule))
            cached["lastCheck"] = time.time()


def add_rule(window, folder, rule):
    """Дописывает правило в .gitignore, создавая файл при необходимости."""
    path = os.path.join(folder, ".gitignore")
    try:
        content = ""
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
        if content and not content.endswith("\n"):
            content += "\n"
        with open(path, "w", encoding="utf-8") as f:
            f.write(content + rule + "\n")
    except Exception as e:
        show_popup(window, str(e), "Error")
        return False
    return True


class GitextGitignoreCommand(sublime_plugin.WindowCommand):
    """Добавляет правила в .gitignore репозитория выбранных путей."""

    def rule(self, folder, path):
        raise NotImplementedError

    def targets(self, paths=None):
        raise NotImplementedError

    def pending_rules(self, paths=None):
        """Пары (корень репозитория, правило), которых нет в кэше правил."""
        rules = []
        folders = []
        for folder, path in self.targets(paths):
            rule = self.rule(folder, path)
            if not rule:
                continue
            folders.append(folder)
            known = cached_rules(folder)
            # Пока .gitignore не прочитан, правило считается отсутствующим
            if known is None or normalize_rule(rule) not in known:
                rules.append((folder, rule))

        # Устаревший кэш обновляем в фоне, текущий вызов не ждёт диск
        for folder in folders:
            if is_rules_stale(folder):
                refresh_rules(folder)
        return rules

    def run(self, paths=None):
        added = []
        seen = set()
        folders = []
        for folder, path in self.targets(paths):
            rule = self.rule(folder, path)
            if not rule or has_rule(folder, rule):
                continue
            key = (os.path.normcase(folder), rule)
            if key in seen:
                continue
            seen.add(key)
            folders.append(folder)
            if add_rule(self.window, folder, rule):
                added.append(rule)
                remember_rule(folder, rule)

        for folder in folders:
            refresh_rules(folder)

        if added:
            self.window.status_message("GitExt: added to .gitignore " + ", ".join(added))
        else:
            show_popup(self.window, "Nothing to add to .gitignore", "GitExt")

    def is_enabled(self, paths=None):
        return bool(self.pending_rules(paths))


class GitextGitignoreFileCommand(GitextGitignoreCommand):
    """Добавляет в .gitignore путь выбранного файла."""

    def rule(self, folder, path):
        return file_rule(folder, path)

    def targets(self, paths=None):
        return file_targets(self.window, paths)


class GitextGitignoreExtensionCommand(GitextGitignoreCommand):
    """Добавляет в .gitignore маску расширения выбранного файла."""

    def rule(self, folder, path):
        return extension_rule(folder, path)

    def targets(self, paths=None):
        return file_targets(self.window, paths)


class GitextGitignoreDirCommand(GitextGitignoreCommand):
    """Добавляет в .gitignore путь выбранной директории."""

    def rule(self, folder, path):
        return dir_rule(folder, path)

    def targets(self, paths=None):
        return dir_targets(self.window, paths)


class GitextGitignoreListener(sublime_plugin.EventListener):
    """Прогревает кэш правил, чтобы меню открывалось без задержки."""

    def on_activated(self, view):
        self.prefetch(view)

    def on_post_save(self, view):
        self.prefetch(view)

    def prefetch(self, view):
        window = view.window()
        path = view.file_name()
        if not window or not path:
            return
        folder = find_folder(window, path)
        if not folder:
            return
        # Правка .gitignore делает кэш недействительным сразу
        if os.path.basename(path) == ".gitignore" or is_rules_stale(folder):
            refresh_rules(folder)


def plugin_loaded():
    """Прогревает кэш правил для уже открытых окон."""
    for window in sublime.windows():
        for folder in window.folders():
            refresh_rules(folder)
