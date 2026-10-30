"""Всплывающие окна пакета GitExt."""

import html

import sublime

def show_popup(window, text, title="GitExt", max_width=900, max_height=600):
    sublime.set_timeout(lambda: print('GitExt show_popup', text), 0)
    view = window.active_view()
    if view:
        escaped = html.escape(text).replace('\n', '<br>')
        html_text = "<b>{}</b><br>{}".format(html.escape(title), escaped)
        view.show_popup(html_text, max_width=max_width, max_height=max_height)
    else:
        sublime.set_timeout(lambda: print('GitExt error view is undefined'), 0)
