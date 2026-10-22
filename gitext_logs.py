import sublime_plugin

from .GitExt import run_git_command, show_popup


class GitextLogsCommand(sublime_plugin.WindowCommand):
    def run(self):
        folder = self.window.folders()[0]

        def callback(output, error):
            if error:
                show_popup(self.window, error, "Error")
                return

            lines = output.splitlines()

            def on_select(index):
                if index == -1:
                    return
                short_hash = lines[index].split(" ")[0]

                def show_callback(output, error):
                    if error:
                        show_popup(self.window, error, "Error")
                        return

                    new_view = self.window.new_file()
                    new_view.set_name("Commit " + short_hash)
                    new_view.set_syntax_file("Packages/Git Formats/Git Commit.sublime-syntax")
                    new_view.set_scratch(True)
                    new_view.run_command("append", {"characters": output})

                run_git_command(["show", short_hash], folder, show_callback)

            self.window.show_quick_panel(lines, on_select)

        run_git_command(["log", "--pretty=format:%h %s (%an, %ad)", "--date=short"], folder, callback)

    def is_enabled(self):
        return bool(self.window.folders())
