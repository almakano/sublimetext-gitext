# GitExt

Git integration for Sublime Text 4. Inspect the current diff, stage files, commit, push, and browse branches, remotes, logs and file history without leaving the editor.

## Features

- In-tab diff: added lines get a dark green background, deleted lines are shown as dark red phantoms without changing the real line numbers.
- Automatic diff when a file is opened (configurable).
- Stage the current file, the sidebar selection, or everything.
- Commit staged changes, commit all tracked changes, or commit and push in one step.
- Branch, remote, log and file-history browsers built on quick panels.
- Context menus in the editor and in the sidebar.
- Repository initialization with a generated `.gitignore`, and safe deinitialization.

## Requirements

- Sublime Text 4, build 4132 or newer.
- `git` available in `PATH`.

## Installation

### Package Control

Until the package is available in the default channel:

1. Run `Package Control: Add Repository` and enter:
   `https://github.com/almakano/sublimetext-gitext`
2. Run `Package Control: Install Package` and choose **GitExt**.

After the package is accepted into the default channel, install it directly with `Package Control: Install Package`.

### Manual

Clone the repository into your `Packages` directory:

```sh
git clone https://github.com/almakano/sublimetext-gitext.git "…/Sublime Text/Packages/GitExt"
```

## Usage

Right-click in the editor or on a file/folder in the sidebar and open the **GitExt** submenu.

| Command | Description |
| --- | --- |
| Init | Runs `git init`; creates a `.gitignore` if missing. |
| DeInit | Removes the `.git` directory after confirmation. |
| Status | Shows `git status` in a popup. |
| diffTab | Shows the unstaged diff in the current tab. |
| Config | Opens `.git/config`. |
| Branch | Lists local and remote branches; checkout or delete. |
| Remotes | Browses remotes, branches and commits; add or remove remotes. |
| Pull | Runs `git pull`. |
| Add | Stages the current file or the sidebar selection. |
| Add all | Runs `git add .` in the repository root. |
| Reset changes | Runs `git reset` (unstages changes). |
| Commit | Runs `git commit -m` for staged files. |
| Commit all | Runs `git commit -am` for tracked files. |
| Commit n Push | Stages everything, commits and pushes; sets the upstream if needed. |
| Push | Pushes the current branch to a selected remote. |
| Logs | Shows recent commits; opens a commit diff. |
| File history | Runs `git log -p -- <file>`. |
| gitignore file | Appends the selected file's path to `.gitignore`. |
| gitignore extension | Appends `*.ext` for the selected file's extension to `.gitignore`. |
| gitignore dir | Appends the selected directory's path to `.gitignore`. |
| Run | Opens the current file in the default application. |

The `Run` item is a separate top-level context-menu entry.

Menu items that cannot do anything (no repository, no changes, nothing staged) are disabled.

The `gitignore` commands are disabled when the selection does not match the rule kind (a file for `gitignore file` and `gitignore extension`, a directory for `gitignore dir`), when the directory is the repository root, when the file has no extension, or when the rule is already present in `.gitignore`. Without a sidebar selection they act on the active file and its folder.

The **Add**, **Add all**, **Commit**, **Commit all** and **Commit n Push** commands in the sidebar act on the selected path's repository.

## Settings

`GitExt.sublime-settings`:

```json
{
    "show_gitdiff_on_open": true
}
```

`show_gitdiff_on_open` runs `diffTab` automatically when a saved file from a Git repository is loaded.

The file opens with `Preferences: GitExt Settings` in the command palette or with **Preferences → Package Settings → GitExt → Settings**.

## Notes

- `diffTab` decorates the current view, so the buffer and line numbers are not modified.
- The `gitignore` items read `.gitignore` in a background thread and cache the rules for a few seconds, so opening the menu does not block rendering. The cache is refreshed on window/view activation, after saving `.gitignore`, and after a rule is added.
- The generated color scheme used for the green background is written to `Packages/User/gitext_diff.sublime-color-scheme`.
- Shared code lives in the `lib` subpackage; every other module in the package root is a plugin loaded by Sublime Text.
- The plugin is developed and tested on Windows. All commands, including the file `Run` action, work on macOS and Linux as well.

## License

MIT — see [LICENSE](LICENSE).
