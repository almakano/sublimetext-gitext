import sublime_plugin

from .GitExt import run_git_command, show_popup


class GitextRemoteCommand(sublime_plugin.WindowCommand):
    def run(self, remote=None, branch=None, commit=None):
        self.folder = self.window.folders()[0] if self.window.folders() else None
        if not self.folder:
            show_popup(self.window, "No folder open", "Error")
            return

        if commit:
            self.show_commit_menu(remote, branch, commit)
        elif branch:
            self.show_branch_menu(remote, branch)
        elif remote:
            self.show_remote_menu(remote)
        else:
            self.show_remote_list()

    # --- Уровень 1: Список remotes ---
    def show_remote_list(self):
        def callback(output, error):
            items = [["Add remote", "Add a new remote repository"]]
            remotes = []
            if output:
                for r in output.strip().splitlines():
                    name = r.split()[0]
                    if name not in remotes:
                        remotes.append(name)
                for name in remotes:
                    items.append([name, "Open " + name])
            self.window.show_quick_panel(items, lambda i: self.on_remote_selected(i, items))
        run_git_command(["remote", "-v"], self.folder, callback)

    def on_remote_selected(self, index, items):
        if index == -1:
            return
        if index == 0:
            self.window.show_input_panel("Remote name and URL (name url):", "", self.add_remote, None, None)
        else:
            remote = items[index][0]
            self.run(remote=remote)

    def add_remote(self, text):
        parts = text.strip().split()
        if len(parts) != 2:
            show_popup(self.window, "Format: name url", "Error")
            return
        run_git_command(["remote", "add", parts[0], parts[1]], self.folder, lambda o, e: show_popup(self.window, o if o else e, "Add remote"))

    # --- Уровень 2: Меню конкретного remote ---
    def show_remote_menu(self, remote):
        self.remote = remote
        def callback(output, error):
            items = [["Delete remote " + remote, "Remove this remote"]]
            if output:
                branches = [line.split("\t")[0].replace("refs/heads/", "") for line in output.strip().splitlines()]
                for b in branches:
                    items.append([b, "Open branch " + b])
            self.window.show_quick_panel(items, lambda i: self.on_branch_selected(i, items, remote))
        run_git_command(["ls-remote", "--heads", remote], self.folder, callback)

    def on_branch_selected(self, index, items, remote):
        if index == -1:
            return
        if index == 0:
            run_git_command(["remote", "remove", remote], self.folder, lambda o, e: show_popup(self.window, o if o else e, "Delete remote " + remote))
        else:
            branch = items[index][0]
            self.run(remote=remote, branch=branch)

    # --- Уровень 3: Меню конкретной ветки ---
    def show_branch_menu(self, remote, branch):
        self.remote = remote
        self.branch = branch
        def callback(output, error):
            items = [["Delete branch " + branch, "Remove this branch"]]
            if output:
                for line in output.strip().splitlines():
                    commit_hash, msg = line.split(" ", 1)
                    items.append([commit_hash, msg])
            self.window.show_quick_panel(items, lambda i: self.on_commit_selected(i, items, remote, branch))
        run_git_command(["log", "--oneline", remote + "/" + branch], self.folder, callback)

    def on_commit_selected(self, index, items, remote, branch):
        if index == -1:
            return
        if index == 0:
            run_git_command(["push", remote, "--delete", branch], self.folder, lambda o, e: show_popup(self.window, o if o else e, "Delete branch " + branch))
        else:
            commit = items[index][0]
            self.run(remote=remote, branch=branch, commit=commit)

    # --- Уровень 4: Меню конкретного коммита ---
    def show_commit_menu(self, remote, branch, commit):
        def on_select(i):
            if i == -1:
                return
            if i == 0:  # Checkout
                run_git_command(["checkout", commit], self.folder, lambda o, e: show_popup(self.window, o if o else e, "Checkout " + commit))
            elif i == 1:  # Show diff
                run_git_command(["show", commit], self.folder, lambda o, e: self.show_commit_diff(commit, o, e))
        items = [["Checkout to " + commit, ""], ["Show diff of " + commit, ""]]
        self.window.show_quick_panel(items, on_select)

    def show_commit_diff(self, commit, output, error):
        if error:
            show_popup(self.window, error, "Error")
            return
        v = self.window.new_file()
        v.set_name("Diff " + commit)
        v.set_syntax_file("Packages/Diff/Diff.sublime-syntax")
        v.run_command("append", {"characters": output})
