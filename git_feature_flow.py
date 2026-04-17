#!/usr/bin/env python3
import os
import re
import shlex
import subprocess
import sys
import traceback
import random
import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Tuple, Any, Union

# ============================================================
# CƠ CHẾ LOAD CẤU HÌNH THÔNG MINH (NO-CODE SEPARATION)
# ============================================================
CURRENT_LANG = "vn_pro"
EMOJI_MODE = False


def load_json_config(filename: str) -> dict:
    """
    Load cấu hình với thứ tự ưu tiên:
    1. Thư mục 'config' nằm ngang hàng với file .exe (User override)
    2. Thư mục 'config' được nhúng ngầm bên trong .exe (sys._MEIPASS)
    """
    if getattr(sys, 'frozen', False):
        # Môi trường đã build ra .exe bằng PyInstaller
        external_base = os.path.dirname(sys.executable)
        internal_base = sys._MEIPASS
    else:
        # Môi trường chạy code .py bình thường
        external_base = os.path.dirname(os.path.abspath(__file__))
        internal_base = external_base

    external_path = os.path.join(external_base, 'config', filename)
    internal_path = os.path.join(internal_base, 'config', filename)

    # Ưu tiên 1: Đọc file bên ngoài (Nếu user tự tạo để Override)
    if os.path.exists(external_path):
        try:
            with open(external_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"[Cảnh báo] File custom {filename} bị lỗi cú pháp JSON: {e}")

    # Ưu tiên 2: Đọc file mặc định nhúng sẵn trong ruột .exe
    if os.path.exists(internal_path):
        try:
            with open(internal_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            pass

    print(f"🚨 LỖI HỆ THỐNG: Bị thiếu file cấu hình {filename}!")
    return {}


# Tự động load khi chạy script
EMOJI_MAP = load_json_config('emoji_map.json')
LANGUAGES = load_json_config('languages.json')


# ============================================================
# Hàm Translate thông minh (Vẫn giữ nguyên logic Fallback)
# ============================================================
def _t(key: str, **kwargs) -> str:
    lang_dict = LANGUAGES.get(key, {})

    # Smart Fallback: Rơi tự do từ CURRENT_LANG -> vn_pro -> en_pro -> trả về đúng cái key
    msg_data = lang_dict.get(CURRENT_LANG)
    if not msg_data:
        msg_data = lang_dict.get("vn_pro", lang_dict.get("en_pro", key))

    # Xử lý random nếu data là list
    if isinstance(msg_data, list):
        msg = random.choice(msg_data)
    else:
        msg = msg_data

    # Format chuỗi an toàn
    if kwargs:
        try:
            msg = msg.format(**kwargs)
        except Exception:
            pass

    # Thêm Emoji nếu đang bật
    if EMOJI_MODE and key in EMOJI_MAP:
        msg = f"{msg} {EMOJI_MAP.get(key, '')}"

    return msg


# ============================================================
# Quoting Helper (Xử lý chuỗi an toàn cho Windows CMD & Unix)
# ============================================================
def quote_arg(arg: str) -> str:
    """
    Sử dụng hàm này thay cho shlex.quote() vì shlex sinh ra dấu nháy đơn ('...')
    Windows CMD không hiểu dấu nháy đơn để nhóm chuỗi có khoảng trắng,
    điều này sẽ gây lỗi văng lệnh khi git commit.
    """
    if os.name == "nt":
        # Escape nháy kép bên trong và bọc toàn bộ bằng nháy kép
        return '"' + arg.replace('"', '\\"') + '"'
    return shlex.quote(arg)

# ============================================================
# Optional Windows color support via colorama
# ============================================================
def try_init_colorama() -> bool:
    try:
        from colorama import just_fix_windows_console
        just_fix_windows_console()
        return True
    except Exception:
        return False

# ============================================================
# Exit / pause helpers
# ============================================================
def should_pause_on_exit() -> bool:
    if getattr(sys, "frozen", False):
        return True
    stdin_tty = hasattr(sys.stdin, "isatty") and sys.stdin.isatty()
    stdout_tty = hasattr(sys.stdout, "isatty") and sys.stdout.isatty()
    return not (stdin_tty and stdout_tty)

def pause_exit(code: int = 0) -> None:
    if should_pause_on_exit():
        try:
            input(_t("press_exit"))
        except Exception:
            pass
    sys.exit(code)

def pause_continue() -> None:
    try:
        input(f"\n{THEME.dim(_t('press_continue'))}")
    except Exception:
        pass

def clear_screen() -> None:
    os.system("cls" if os.name == "nt" else "clear")

# ============================================================
# Terminal / color capability
# ============================================================
def supports_color(stream) -> bool:
    if os.environ.get("NO_COLOR"):
        return False
    if not hasattr(stream, "isatty") or not stream.isatty():
        return False
    term = os.environ.get("TERM", "")
    if term.lower() == "dumb":
        return False
    if os.name == "nt":
        try_init_colorama()
        return True
    return True

def supports_unicode_box(stream) -> bool:
    encoding = (getattr(stream, "encoding", None) or "").lower()
    return "utf" in encoding or "65001" in encoding

# ============================================================
# Theme / rendering
# ============================================================
@dataclass
class Theme:
    use_color: bool
    use_unicode_box: bool
    RESET: str = "\033[0m"
    BOLD: str = "\033[1m"
    DIM: str = "\033[2m"
    BLACK: str = "\033[30m"
    RED: str = "\033[31m"
    GREEN: str = "\033[32m"
    YELLOW: str = "\033[33m"
    BLUE: str = "\033[34m"
    MAGENTA: str = "\033[35m"
    CYAN: str = "\033[36m"
    BG_YELLOW: str = "\033[43m"
    BRIGHT_RED: str = "\033[91m"
    BRIGHT_GREEN: str = "\033[92m"
    BRIGHT_YELLOW: str = "\033[93m"
    BRIGHT_BLUE: str = "\033[94m"
    BRIGHT_MAGENTA: str = "\033[95m"
    BRIGHT_CYAN: str = "\033[96m"

    def s(self, text: str, *styles: str) -> str:
        if not self.use_color: return text
        return "".join(styles) + text + self.RESET
    def bold(self, text: str) -> str: return self.s(text, self.BOLD)
    def dim(self, text: str) -> str: return self.s(text, self.DIM)
    def info(self, text: str) -> str: return self.s(text, self.BRIGHT_CYAN, self.BOLD)
    def ok(self, text: str) -> str: return self.s(text, self.BRIGHT_GREEN, self.BOLD)
    def warn(self, text: str) -> str: return self.s(text, self.BRIGHT_YELLOW, self.BOLD)
    def err(self, text: str) -> str: return self.s(text, self.BRIGHT_RED, self.BOLD)
    def branch(self, text: str) -> str: return self.s(text, self.BRIGHT_BLUE, self.BOLD)
    def commit(self, text: str) -> str: return self.s(text, self.BRIGHT_MAGENTA, self.BOLD)
    def count(self, text: str) -> str: return self.s(text, self.BRIGHT_YELLOW, self.BOLD)
    def cmd(self, text: str) -> str: return self.s(text, self.GREEN, self.BOLD)
    def choice(self, text: str) -> str: return self.s(text, self.CYAN, self.BOLD)
    def key(self, text: str) -> str: return self.s(text, self.BRIGHT_CYAN, self.BOLD)
    def tag_feat(self, text: str) -> str: return self.s(text, self.BRIGHT_GREEN, self.BOLD)
    def tag_fix(self, text: str) -> str: return self.s(text, self.BRIGHT_YELLOW, self.BOLD)
    def tag_refactor(self, text: str) -> str: return self.s(text, self.BRIGHT_MAGENTA, self.BOLD)
    def tag_other(self, text: str) -> str: return self.s(text, self.BRIGHT_CYAN, self.BOLD)

THEME = Theme(
    use_color=supports_color(sys.stdout),
    use_unicode_box=supports_unicode_box(sys.stdout),
)

def box_chars():
    if THEME.use_unicode_box:
        return {"tl": "╔", "tr": "╗", "bl": "╚", "br": "╝", "h": "═", "v": "║", "lt": "╠", "rt": "╣"}
    return {"tl": "+", "tr": "+", "bl": "+", "br": "+", "h": "-", "v": "|", "lt": "+", "rt": "+"}
BOX = box_chars()

def strip_ansi(text: str) -> str:
    return re.sub(r"\x1b\[[0-9;]*m", "", text)

def visible_len(text: str) -> int:
    return len(strip_ansi(text))

def print_box(title: str, lines: List[str]) -> None:
    width = max([len(title)] + [visible_len(line) for line in lines]) + 2
    top = f"{BOX['tl']}{BOX['h'] * (width + 2)}{BOX['tr']}"
    mid = f"{BOX['lt']}{BOX['h'] * (width + 2)}{BOX['rt']}"
    bottom = f"{BOX['bl']}{BOX['h'] * (width + 2)}{BOX['br']}"
    print()
    print(THEME.branch(top))
    title_line = f"{BOX['v']} {THEME.bold(title.ljust(width))} {BOX['v']}"
    print(THEME.branch(title_line))
    print(THEME.branch(mid))
    for line in lines:
        padding = width - visible_len(line)
        print(THEME.branch(f"{BOX['v']} ") + line + (" " * padding) + THEME.branch(f" {BOX['v']}"))
    print(THEME.branch(bottom))

# ============================================================
# Git Error Decoder
# ============================================================
def get_friendly_git_error(stderr_str: str) -> str:
    stderr_lower = stderr_str.lower()

    if "could not resolve host" in stderr_lower or "authentication failed" in stderr_lower or "permission denied" in stderr_lower:
        return _t("err_network")
    if "conflict" in stderr_lower:
        return _t("err_conflict")
    if "would be overwritten by" in stderr_lower or "please commit your changes or stash them" in stderr_lower:
        return _t("err_overwrite")
    if "fetch first" in stderr_lower or "non-fast-forward" in stderr_lower or "updates were rejected" in stderr_lower:
        return _t("err_push_rejected")

    return _t("err_unknown")

# ============================================================
# Shell / Git helpers
# ============================================================
def run(cmd: str, cwd: Optional[str] = None, check: bool = True, capture: bool = False) -> str:
    print(f"\n{THEME.cmd('> ' + cmd)}")

    if capture:
        result = subprocess.run(cmd, shell=True, text=True, capture_output=True, cwd=cwd)
        stdout_val = result.stdout or ""
        stderr_val = result.stderr or ""
    else:
        result = subprocess.run(cmd, shell=True, text=True, stderr=subprocess.PIPE, cwd=cwd)
        stdout_val = ""
        stderr_val = result.stderr or ""

    if check and result.returncode != 0:
        if stderr_val:
            print(THEME.err(stderr_val.rstrip()), file=sys.stderr)

        if cwd:
            print(THEME.warn(f"Working directory: {cwd}"))

        friendly_msg = get_friendly_git_error(stderr_val)
        print(f"\n{THEME.branch(BOX['tl'] + BOX['h']*50)}")
        print(f"{THEME.branch(BOX['v'])} {THEME.info('💡 GIẢI MÃ LỖI / ERROR DECODER:')}")
        print(f"{THEME.branch(BOX['v'])} {friendly_msg}")
        print(f"{THEME.branch(BOX['bl'] + BOX['h']*50)}\n")

        raise RuntimeError(f"Command failed: {cmd}")

    return stdout_val.strip()

def git_output(cmd: str, cwd: Optional[str] = None, check: bool = True) -> str:
    return run(cmd, cwd=cwd, check=check, capture=True)

def ensure_git_installed() -> None:
    result = subprocess.run("git --version", shell=True, text=True, capture_output=True)
    if result.returncode != 0:
        print(THEME.err(_t("no_git_err")))
        print(THEME.warn(_t("no_git_warn")))
        pause_exit(1)

# ============================================================
# Predict Conflict (git merge-tree)
# ============================================================
def check_potential_conflict(repo_dir: str, base_branch: str) -> Tuple[bool, List[str], bool]:
    cmd = f"git merge-tree --write-tree origin/{base_branch} HEAD"
    try:
        result = subprocess.run(cmd, shell=True, text=True, capture_output=True, cwd=repo_dir)
        if result.returncode == 0:
            return False, [], True
        elif result.returncode == 1:
            c_lines = [line.strip() for line in result.stdout.splitlines() if "CONFLICT" in line]
            return True, c_lines, True
        else:
            return False, [], False
    except Exception:
        return False, [], False


# ============================================================
# Smart Git Command Interceptor
# ============================================================
def handle_smart_git_command(command: str, repo_dir: str) -> bool:
    parts = command.strip().split()
    if len(parts) < 2 or parts[0].lower() != "git":
        return False

    subcmd = parts[1].lower()
    explain_key = f"git_cmd_{subcmd}"
    if explain_key not in LANGUAGES:
        explain_key = "git_cmd_unknown"

    print(f"\n{THEME.info('💡 ' + _t('smart_git_detect'))} {THEME.cmd(command)}")
    print(f"   {THEME.dim('->')} {_t(explain_key)}")

    ans = input(f"\n{THEME.info('?')} {_t('smart_git_confirm')} {THEME.ok('[Y/n]')}: ").strip().lower()
    if ans in ('', 'y', 'yes'):
        print(f"\n{THEME.branch(BOX['tl'] + BOX['h'] * 80)}")
        try:
            # FIX LOGIC: Dùng cờ -C của Git để ép buộc thư mục gốc, bất chấp môi trường Windows
            # Ví dụ: command là 'git commit -m "abc"' -> args là 'commit -m "abc"'
            args = command[3:].strip()
            safe_repo = quote_arg(repo_dir)

            # Lệnh thực tế sẽ chạy: git -C "D:\Đường dẫn\Repo" commit -m "abc"
            exact_command = f"git -C {safe_repo} {args}"

            # Vẫn giữ cwd=repo_dir để phòng hờ các lệnh bash script con bên trong hook
            result = subprocess.run(exact_command, shell=True, cwd=repo_dir)
            print(f"{THEME.branch(BOX['bl'] + BOX['h'] * 80)}")

            if result.returncode == 0:
                print(THEME.ok(_t('smart_git_done')))
            else:
                # Bắt luôn lỗi Exit code của đợt fix trước
                print(THEME.err(_t('smart_git_fail', code=result.returncode)))

        except Exception as e:
            print(f"{THEME.branch(BOX['bl'] + BOX['h'] * 80)}")
            print(THEME.err(f"Lỗi hệ thống khi thực thi: {e}"))

        pause_continue()
        return True
    else:
        ans2 = input(
            f"{THEME.info('?')} Có muốn dùng cụm '{command}' như câu trả lời bình thường thay vì lệnh Git không? [y/N]: ").strip().lower()
        if ans2 in ('y', 'yes'):
            return False
        else:
            print(THEME.warn(_t('smart_git_cancel')))
            return True

# ============================================================
# Prompt helpers (Có hỗ trợ Back '<' và Smart Git Intercept)
# ============================================================
def ask_yes_no(question_key: str, default: bool = True, allow_back: bool = False, repo_dir: Optional[str] = None, **kwargs) -> Any:
    suffix = THEME.ok("[Y/n]") if default else THEME.warn("[y/N]")
    back_hint = THEME.dim(_t("type_back")) if allow_back else ""
    while True:
        answer = input(f"{THEME.info('?')} {_t(question_key, **kwargs)} {suffix}{back_hint}: ").strip()

        if repo_dir and answer.lower().startswith("git "):
            if handle_smart_git_command(answer, repo_dir):
                clear_screen()
                continue

        ans_lower = answer.lower()
        if allow_back and ans_lower == "<": return "<BACK>"
        if not ans_lower: return default
        if ans_lower in ("y", "yes"): return True
        if ans_lower in ("n", "no"): return False
        print(THEME.warn(_t("invalid_yn")))

def ask_non_empty(question_key: str, default: Optional[str] = None, allow_back: bool = False, repo_dir: Optional[str] = None) -> Any:
    back_hint = THEME.dim(_t("type_back")) if allow_back else ""
    while True:
        if default is None:
            answer = input(f"{THEME.info('?')} {_t(question_key)}{back_hint}: ").strip()
        else:
            answer = input(f"{THEME.info('?')} {_t(question_key)} {THEME.dim('[' + default + ']')}{back_hint}: ").strip()

        if repo_dir and answer.lower().startswith("git "):
            if handle_smart_git_command(answer, repo_dir):
                clear_screen()
                continue

        if allow_back and answer == "<": return "<BACK>"
        if not answer and default is not None: return default
        if answer: return answer
        print(THEME.warn(_t("not_empty")))

def ask_choice(question_key: str, option_keys: List[str], default_index: int = 0, allow_back: bool = False, repo_dir: Optional[str] = None) -> str:
    while True:
        print(f"\n{THEME.info('?')} {_t(question_key)}")
        for i, opt_key in enumerate(option_keys, start=1):
            marker = f" {THEME.ok(_t('default_marker'))}" if i - 1 == default_index else ""
            display = _t(opt_key)
            if opt_key == "m_emoji":
                state = "ON 🟢" if EMOJI_MODE else "OFF 🔴"
                display = f"{display} [{state}]"
            print(f"  {THEME.choice(str(i) + '.')} {display}{marker}")

        if allow_back:
            print(f"  {THEME.choice('<.')} {_t('opt_back')}")

        answer = input(f"{THEME.info('?')} {_t('choose_num')} ").strip()

        if repo_dir and answer.lower().startswith("git "):
            if handle_smart_git_command(answer, repo_dir):
                clear_screen()
                continue

        if allow_back and answer == "<": return "<BACK>"
        if not answer: return option_keys[default_index]
        if answer.isdigit():
            idx = int(answer) - 1
            if 0 <= idx < len(option_keys): return option_keys[idx]
        clear_screen()
        print(THEME.warn(_t("invalid_choice")))


# ============================================================
# Repo detection helpers
# ============================================================
def is_git_repo(path: str) -> bool:
    result = subprocess.run("git rev-parse --is-inside-work-tree", shell=True, text=True, capture_output=True, cwd=path)
    return result.returncode == 0


def find_git_repo_upwards(start_path: str) -> Optional[str]:
    current = Path(start_path).resolve()
    for candidate in [current] + list(current.parents):
        if (candidate / ".git").exists(): return str(candidate)
    return None


def ask_repo_path() -> str:
    while True:
        repo_path = input(f"{THEME.info('?')} {_t('enter_repo')}").strip().strip('"')
        if not repo_path:
            print(THEME.warn(_t("not_empty")))
            continue

        # FIX LOGIC: Ép thành đường dẫn tuyệt đối (Absolute Path)
        repo_path = os.path.abspath(repo_path)

        if not os.path.isdir(repo_path):
            print(THEME.err(_t("repo_not_exist")))
            continue
        if not is_git_repo(repo_path):
            print(THEME.err(_t("not_git_repo")))
            continue
        return repo_path


def resolve_repo_dir() -> str:
    # FIX LOGIC: Ép cwd thành tuyệt đối
    cwd = os.path.abspath(os.getcwd())
    if is_git_repo(cwd): return cwd
    guessed = find_git_repo_upwards(cwd)
    if guessed:
        print(THEME.warn(_t("cwd_not_git")))
        print(THEME.ok(_t("found_closest", guessed=guessed)))
        if ask_yes_no("use_this", True): return guessed
    print(THEME.warn(_t("pls_choose_repo")))
    return ask_repo_path()

# ============================================================
# Working tree helpers
# ============================================================
def get_worktree_status(repo_dir: str) -> List[str]:
    output = git_output("git status --porcelain", cwd=repo_dir)
    return output.splitlines() if output else []

def show_worktree_changes(changes: List[str]) -> None:
    lines = changes[:20] if changes else [THEME.dim(_t("no_local_changes"))]
    if len(changes) > 20:
        lines.append(THEME.dim("..."))
        lines.append(THEME.dim("(Truncated)"))
    print_box("Working Tree Changes", lines)

def handle_dirty_worktree(repo_dir: str) -> Optional[bool]:
    changes = get_worktree_status(repo_dir)
    if not changes: return False

    print(THEME.warn(_t("wt_dirty_warn")))
    show_worktree_changes(changes)

    choice = ask_choice("what_do_changes", ["opt_stash", "opt_no_stash", "opt_cancel"], default_index=0, repo_dir=repo_dir)

    if choice == "opt_stash":
        run('git stash push -u -m "git-feature-flow auto-stash"', cwd=repo_dir)
        print(THEME.ok(_t("stashed_ok")))
        return True

    if choice == "opt_no_stash":
        print(THEME.warn(_t("warn_no_stash")))
        if not ask_yes_no("sure_no_stash", False, repo_dir=repo_dir):
            print(THEME.warn(_t("canceled_return")))
            return None
        return False

    print(THEME.warn(_t("canceled_return")))
    return None

def maybe_restore_auto_stash(repo_dir: str, auto_stashed: bool) -> None:
    if not auto_stashed: return
    restore = ask_yes_no("restore_stash_q", True, repo_dir=repo_dir)
    if not restore:
        print(THEME.warn(_t("kept_stash")))
        return
    run("git stash pop", cwd=repo_dir)
    print(THEME.ok(_t("restored_stash")))

# ============================================================
# Git branch logic & Checkout
# ============================================================
def current_branch(repo_dir: str) -> str:
    return git_output("git rev-parse --abbrev-ref HEAD", cwd=repo_dir)

def ensure_not_on_base(base_branch: str, current: str) -> bool:
    if current == base_branch or current == f"origin/{base_branch}":
        print(THEME.err(_t("on_base_branch", base=base_branch)))
        print(THEME.warn(_t("checkout_feature_first")))
        return False
    return True

def clean_branch_name(b: str) -> str:
    return b.strip().strip("'").strip('"')

def highlight_b(b_name: str, kw: str, is_loc: bool) -> str:
    if not THEME.use_color:
        return b_name
    base_ansi = (THEME.BRIGHT_BLUE + THEME.BOLD) if is_loc else THEME.DIM
    if not kw:
        return base_ansi + b_name + THEME.RESET
    hl_ansi = THEME.BG_YELLOW + THEME.BLACK + THEME.BOLD
    pattern = re.compile(re.escape(kw), re.IGNORECASE)
    colored = pattern.sub(lambda m: hl_ansi + m.group(0) + THEME.RESET + base_ansi, b_name)
    return base_ansi + colored + THEME.RESET

def handle_checkout(repo_dir: str) -> bool:
    local_branches_str = git_output("git branch --format=%(refname:short)", cwd=repo_dir)
    local_branches = [clean_branch_name(b) for b in local_branches_str.splitlines() if b.strip()]

    remote_branches_str = git_output("git branch -r --format=%(refname:short)", cwd=repo_dir)
    remote_branches_raw = [clean_branch_name(b) for b in remote_branches_str.splitlines() if b.strip()]
    remote_branches = [b for b in remote_branches_raw if "origin/HEAD" not in b and b != "origin"]

    local_set = set(local_branches)
    remote_only = []
    for rb in remote_branches:
        clean_name = rb.replace("origin/", "", 1)
        if clean_name not in local_set:
            remote_only.append(rb)

    all_branches = local_branches + remote_only
    if not all_branches:
        return False

    curr = current_branch(repo_dir)
    current_list = all_branches
    search_kw = ""
    alert_msg = ""

    total_count = len(all_branches)
    if total_count >= 50: alert_msg = THEME.warn(_t("branch_count_many", count=total_count))
    elif total_count <= 5: alert_msg = THEME.ok(_t("branch_count_few", count=total_count))

    while True:
        clear_screen()
        show_startup(repo_dir)

        if alert_msg:
            print(f"\n{alert_msg}")
            alert_msg = ""

        print(f"\n{THEME.info(_t('list_branches'))}")
        for i, b in enumerate(current_list, start=1):
            marker = f" {THEME.ok('*')}" if b == curr else ""
            is_loc = b in local_branches
            display_name = highlight_b(b, search_kw, is_loc)
            print(f"  {THEME.choice(str(i) + '.')} {display_name}{marker}")

        ans = input(f"\n{THEME.info('?')} {_t('choose_branch_checkout')} ").strip()

        if ans.lower().startswith("git "):
            if handle_smart_git_command(ans, repo_dir):
                continue

        if not ans: return False

        if ans.lower() == 'f':
            alert_msg = THEME.info(_t("fetching_remote"))
            print(f"\n{alert_msg}")
            run("git fetch origin --prune", cwd=repo_dir)
            return handle_checkout(repo_dir)

        target = None
        if ans.isdigit():
            idx = int(ans) - 1
            if 0 <= idx < len(current_list): target = current_list[idx]
        elif ans in current_list:
            target = ans
        else:
            matches = [b for b in all_branches if ans.lower() in b.lower()]
            if not matches:
                alert_msg = THEME.warn(_t("branch_not_found"))
                continue
            elif len(matches) == 1:
                target = matches[0]
                print(THEME.info(_t("branch_search_single", target=target)))
            else:
                search_kw = ans
                alert_msg = THEME.info(_t("branch_search_found", count=len(matches), kw=ans))
                current_list = matches
                continue

        if target:
            try:
                if target.startswith("origin/"):
                    clean_name = target.replace("origin/", "", 1)
                    run(f"git checkout -t {quote_arg(target)}", cwd=repo_dir)
                    print(THEME.ok(_t("checkout_success", branch=clean_name)))
                else:
                    run(f"git checkout {quote_arg(target)}", cwd=repo_dir)
                    print(THEME.ok(_t("checkout_success", branch=target)))
                return True
            except RuntimeError:
                print(THEME.err(_t("checkout_fail")))
                return False

# ============================================================
# Rebase state & VERIFICATION helpers
# ============================================================
def get_git_dir(repo_dir: str) -> Path:
    git_dir = git_output("git rev-parse --git-dir", cwd=repo_dir)
    git_path = Path(git_dir)
    if not git_path.is_absolute(): git_path = Path(repo_dir) / git_path
    return git_path

def is_rebase_in_progress(repo_dir: str) -> bool:
    git_dir = get_git_dir(repo_dir)
    return (git_dir / "rebase-merge").exists() or (git_dir / "rebase-apply").exists()

def get_conflicted_files(repo_dir: str) -> List[str]:
    output = git_output("git diff --name-only --diff-filter=U", cwd=repo_dir, check=False)
    return output.splitlines() if output else []

def show_git_status_box(repo_dir: str) -> None:
    output = git_output("git status --short", cwd=repo_dir, check=False)
    lines = output.splitlines() if output else ["(No output)"]
    if len(lines) > 30:
        lines = lines[:30] + [THEME.dim("..."), THEME.dim("(Truncated)")]
    print_box("Git Status", lines)

def show_conflicted_files_box(repo_dir: str) -> None:
    files = get_conflicted_files(repo_dir)
    if not files:
        lines = ["(No conflicted files found)"]
    else:
        lines = [f"• {f}" for f in files[:30]]
        if len(files) > 30: lines += [THEME.dim("..."), THEME.dim("(Truncated)")]
    print_box("Conflicted Files", lines)

def handle_rebase_recovery(repo_dir: str) -> str:
    while True:
        if not is_rebase_in_progress(repo_dir):
            print(THEME.ok(_t("rebase_ext_success")))
            return "completed"

        conflict_files = get_conflicted_files(repo_dir)
        lines = [
            _t("rebase_paused_1"), _t("rebase_paused_2"), _t("rebase_paused_3"),
            _t("rebase_paused_4", count=len(conflict_files)),
        ]
        print_box("Rebase Recovery", lines)

        choice = ask_choice("choose_action", ["opt_show_status", "opt_show_conflict", "opt_continue", "opt_abort", "opt_return"], 0, repo_dir=repo_dir)

        if choice == "opt_show_status":
            show_git_status_box(repo_dir)
            continue

        if choice == "opt_show_conflict":
            show_conflicted_files_box(repo_dir)
            continue

        if choice == "opt_continue":
            if not is_rebase_in_progress(repo_dir):
                print(THEME.ok(_t("rebase_ext_success")))
                return "completed"

            try:
                run("git -c core.editor=true rebase --continue", cwd=repo_dir)
            except RuntimeError:
                if is_rebase_in_progress(repo_dir):
                    c_files = get_conflicted_files(repo_dir)
                    wt_changes = get_worktree_status(repo_dir)
                    if len(c_files) == 0 and len(wt_changes) == 0:
                        if ask_yes_no("rebase_skip_q", True, repo_dir=repo_dir):
                            try:
                                run("git -c core.editor=true rebase --skip", cwd=repo_dir)
                            except RuntimeError:
                                pass
                            continue
                    print(THEME.warn(_t("rebase_not_done")))
                    continue
                print(THEME.err(_t("continue_fail")))
                continue

            if is_rebase_in_progress(repo_dir):
                print(THEME.warn(_t("rebase_still_running")))
                continue

            print(THEME.ok(_t("rebase_success")))
            return "completed"

        if choice == "opt_abort":
            if not ask_yes_no("opt_abort_confirm", False, repo_dir=repo_dir): continue
            try:
                run("git rebase --abort", cwd=repo_dir)
                print(THEME.warn(_t("abort_success")))
                return "aborted"
            except RuntimeError:
                print(THEME.err(_t("abort_fail")))
                continue

        if choice == "opt_return":
            print(THEME.warn(_t("rebase_keep_state")))
            return "menu"

def create_backup(repo_dir: str, branch: str) -> str:
    ts = datetime.now().strftime("%Y%m%d-%H%M%S")
    backup_branch = f"backup/{branch.replace('/', '-')}-{ts}"
    run(f"git branch {quote_arg(backup_branch)}", cwd=repo_dir)
    return backup_branch

def get_effective_base_point(repo_dir: str, base_branch: str, history_type: str) -> Optional[str]:
    cmd = f"git merge-base HEAD origin/{base_branch}" if history_type == "clean" else f"git merge-base --fork-point origin/{base_branch} HEAD"
    base_point = git_output(cmd, cwd=repo_dir, check=False)
    if not base_point:
        print(THEME.err(_t("err_no_base_point")))
        print(THEME.warn(_t("warn_complex_history")))
        return None
    return base_point

def commit_count_since(repo_dir: str, base_point: str) -> int:
    return int(git_output(f"git rev-list --count {base_point}..HEAD", cwd=repo_dir))

def detect_history_type(repo_dir: str, base_branch: str) -> Tuple[str, str]:
    merge_base = git_output(f"git merge-base HEAD origin/{base_branch}", cwd=repo_dir)
    merge_commit_count = int(git_output(f"git rev-list --merges --count {merge_base}..HEAD", cwd=repo_dir))

    if merge_commit_count > 0:
        return "merged", _t("merged_reason", count=merge_commit_count, base=merge_base)
    return "clean", _t("clean_reason", base=merge_base)

def get_commit_preview(repo_dir: str, base_point: str, limit: int = 50) -> List[str]:
    output = git_output(f"git log --oneline --no-decorate {base_point}..HEAD -n {limit}", cwd=repo_dir)
    return output.splitlines() if output else []

# ============================================================
# Post-Rebase Verification Engine (Sử dụng git patch-id)
# ============================================================
def get_diff_patch_id(repo_dir: str, base_ref: str, target_ref: str) -> str:
    diff_output = git_output(f"git diff {base_ref}...{target_ref}", cwd=repo_dir, check=False)
    if not diff_output.strip():
        return "empty"

    try:
        p = subprocess.Popen(["git", "patch-id", "--stable"], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=repo_dir)
        out, err = p.communicate(input=diff_output.encode('utf-8'))
        if p.returncode == 0 and out:
            return out.decode('utf-8').split()[0]
    except Exception:
        pass

    cleaned = re.sub(r'@@.*?@@', '', diff_output)
    cleaned = re.sub(r'\s+', '', cleaned)
    return cleaned

def run_verification(repo_dir: str, state: dict, branch: str, backup_branch: Optional[str], conflict_occurred: bool) -> bool:
    print(f"\n{THEME.branch(BOX['tl'] + BOX['h']*80)}")
    print(f"{THEME.branch(BOX['v'])} {THEME.info(_t('verify_title'))}")

    passed = True
    behind = 0

    run(f"git fetch origin {state['base_branch']}", cwd=repo_dir, capture=True)

    try:
        rev_count = git_output(f"git rev-list --left-right --count origin/{state['base_branch']}...HEAD", cwd=repo_dir)
        behind, ahead = map(int, rev_count.split())
        if behind > 0:
            print(f"{THEME.branch(BOX['v'])} {THEME.err(_t('verify_ahead_fail', base=state['base_branch'], behind=behind))}")
            passed = False
        else:
            print(f"{THEME.branch(BOX['v'])} {THEME.ok(_t('verify_ahead_ok', base=state['base_branch'], ahead=ahead))}")
    except Exception:
        print(f"{THEME.branch(BOX['v'])} {THEME.warn('Không thể kiểm tra Ahead/Behind.')}")

    reference_ref = backup_branch if backup_branch else f"origin/{branch}"
    if not git_output(f"git rev-parse --verify {reference_ref}", cwd=repo_dir, check=False):
        reference_ref = None

    if not reference_ref:
        print(f"{THEME.branch(BOX['v'])} {THEME.err(_t('verify_no_ref'))}")
    else:
        old_patch_id = get_diff_patch_id(repo_dir, state["base_point"], reference_ref)
        new_patch_id = get_diff_patch_id(repo_dir, f"origin/{state['base_branch']}", "HEAD")

        if old_patch_id == new_patch_id:
            print(f"{THEME.branch(BOX['v'])} {THEME.ok(_t('verify_patch_ok'))}")
        else:
            passed = False
            print(f"{THEME.branch(BOX['v'])} {THEME.warn(_t('verify_patch_diff'))}")
            if conflict_occurred:
                print(f"{THEME.branch(BOX['v'])} {THEME.dim(_t('verify_conflict_reason'))}")
            else:
                print(f"{THEME.branch(BOX['v'])} {THEME.err(_t('verify_missing_reason'))}")

            diff_cmd = f"git diff {reference_ref} HEAD"
            print(f"{THEME.branch(BOX['v'])} {THEME.info(_t('verify_diff_cmd'))} {THEME.cmd(diff_cmd)}")

    print(f"{THEME.branch(BOX['bl'] + BOX['h']*80)}\n")
    return passed

# ============================================================
# Commit line formatting
# ============================================================
COMMIT_TYPE_RE = re.compile(r"^(feat|fix|refactor|chore|docs|test)(\(.+?\))?:", re.IGNORECASE)

def highlight_commit_message(message: str) -> str:
    match = COMMIT_TYPE_RE.match(message)
    if not match: return message
    commit_type, prefix = match.group(1).lower(), match.group(0)
    if commit_type == "feat": colored_prefix = THEME.tag_feat(prefix)
    elif commit_type == "fix": colored_prefix = THEME.tag_fix(prefix)
    elif commit_type == "refactor": colored_prefix = THEME.tag_refactor(prefix)
    else: colored_prefix = THEME.tag_other(prefix)
    return colored_prefix + message[len(prefix):]

def format_commit_line(line: str) -> str:
    parts = line.split(" ", 1)
    if len(parts) == 1: return f"• {THEME.commit(parts[0])}"
    return f"• {THEME.commit(parts[0])} {highlight_commit_message(parts[1])}"

# ============================================================
# UI blocks - WIZARD DASHBOARD
# ============================================================
def show_startup(repo_dir: str) -> None:
    try:
        branch = current_branch(repo_dir)
    except Exception:
        branch = "(unknown / initial)"

    rebase_state = THEME.warn('🚧 IN PROGRESS') if is_rebase_in_progress(repo_dir) else THEME.ok('idle')

    lines = [
        f"{THEME.key('Platform')} : {os.name}",
        f"{THEME.key('Repo')}     : {repo_dir}",
        f"{THEME.key('Branch')}   : {THEME.branch(branch)}",
        f"{THEME.key('Rebase')}   : {rebase_state}",
    ]
    print_box("Feature Branch Squash + Rebase Assistant", lines)

def show_wizard_dashboard(state: dict, current_step: int) -> None:
    def check(step_idx: int) -> str:
        if current_step > step_idx: return THEME.ok("[✓]")
        if current_step == step_idx: return THEME.warn("[►]")
        return THEME.dim("[ ]")

    lines = []

    v0 = THEME.branch(state.get('base_branch', '')) if current_step > 0 else "..."
    lines.append(f"{check(0)} {_t('dash_base_branch').ljust(18)} : {v0}")

    v1 = "Yes" if state.get('do_fetch') else "No"
    v1 = THEME.choice(v1) if current_step > 1 else "..."
    lines.append(f"{check(1)} {_t('dash_fetch').ljust(18)} : {v1}")

    if state.get('conflict_status'):
        c_stat = state['conflict_status']
        if c_stat == "clean":
            c_str = THEME.ok(_t("dash_predict_clean"))
        elif c_stat == "conflict":
            c_str = THEME.err(_t("dash_predict_conflict", count=state.get("conflict_count", 0)))
        else:
            c_str = THEME.dim("N/A")
        lines.append(f"       └─ {THEME.dim(_t('dash_predict') + ':')} {c_str}")

    v2 = THEME.choice(state.get('history_type', '')) if current_step > 2 else "..."
    lines.append(f"{check(2)} {_t('dash_history').ljust(18)} : {v2}")
    if current_step > 2 and state.get('commit_total', 0) > 0:
        lines.append(f"       └─ {THEME.dim('Commits to squash:')} {THEME.count(str(state['commit_total']))}")

    v3 = "Yes" if state.get('do_backup') else "No"
    v3 = THEME.choice(v3) if current_step > 3 else "..."
    lines.append(f"{check(3)} {_t('dash_backup').ljust(18)} : {v3}")

    v4 = THEME.commit(state.get('final_msg', '')) if current_step > 4 else "..."
    lines.append(f"{check(4)} {_t('dash_msg').ljust(18)} : {v4}")

    v5 = "Yes" if state.get('auto_push') else "No"
    v5 = THEME.choice(v5) if current_step > 5 else "..."
    lines.append(f"{check(5)} {_t('dash_push').ljust(18)} : {v5}")

    print_box(_t("dash_title"), lines)

    if current_step > 2 and state.get('commit_total', 0) >= 20:
        print(f"  {THEME.warn(_t('ee_spam_commit', count=state['commit_total']))}")

def show_action_plan(base_point: str, final_message: str, base_branch: str, feature_branch: str, commit_count: int, auto_push: bool) -> None:
    pad_base = base_branch.ljust(15)
    pad_feat = feature_branch.ljust(15)

    sketch = [
        f"{THEME.dim('[TRƯỚC / BEFORE]')}",
        f" {THEME.branch(pad_base)} ──○──○──◉──○──○ (origin)",
        f"                         \\",
        f" {THEME.branch(pad_feat)}          ○──○──○ ({commit_count} commits)",
        f"",
        f"{THEME.dim('[SAU / AFTER]')}",
        f" {THEME.branch(pad_base)} ──○──○──◉──○──○ (origin)",
        f"                                     \\",
        f" {THEME.branch(pad_feat)}                      🌟 (1 squashed)"
    ]
    print_box("Rebase Flow Sketch", sketch)

    lines = [
        THEME.cmd(f"1. git reset --soft {base_point}"),
        THEME.cmd(f'2. git commit -m "{final_message}"'),
        THEME.cmd(f"3. git rebase origin/{base_branch}"),
    ]
    if auto_push: lines.append(THEME.cmd("4. git push --force-with-lease"))
    print_box("Commands to execute", lines)


# ============================================================
# Rollback Engine
# ============================================================
def perform_rollback(repo_dir: str, original_commit: str) -> None:
    print(f"\n{THEME.warn(_t('rollback_in_progress'))}")
    # Nếu đang dính rebase dở dang, abort nó trước
    if is_rebase_in_progress(repo_dir):
        run("git rebase --abort", cwd=repo_dir, check=False)
    # Hard reset về chính xác commit lúc chưa chạy tool
    run(f"git reset --hard {original_commit}", cwd=repo_dir)
    print(THEME.ok(_t('rollback_success')))


# ============================================================
# Core flow (STATE MACHINE WIZARD)
# ============================================================
def run_feature_flow(repo_dir: str) -> None:
    if is_rebase_in_progress(repo_dir):
        print(THEME.warn("Repo is in rebase progress state."))
        if handle_rebase_recovery(repo_dir) in ("completed", "aborted", "menu"): return

    branch = current_branch(repo_dir)
    print(f"\n{THEME.ok('Current branch:')} {THEME.branch(branch)}")

    auto_stashed_result = handle_dirty_worktree(repo_dir)
    if auto_stashed_result is None: return
    auto_stashed = auto_stashed_result

    state = {
        "base_branch": "develop",
        "do_fetch": True,
        "detected_type": "",
        "detected_reason": "",
        "history_type": "",
        "base_point": "",
        "commit_total": 0,
        "commits": [],
        "do_backup": True,
        "final_msg": "feat: update feature",
        "auto_push": False,
        "conflict_status": None,
        "conflict_count": 0
    }

    step = 0
    max_step = 6

    while step <= max_step:
        clear_screen()
        print(f"\n{THEME.ok('Current branch:')} {THEME.branch(branch)}")
        show_wizard_dashboard(state, current_step=step)

        if step == 0:
            state["conflict_status"] = None
            ans = ask_non_empty("base_branch_name", state["base_branch"], allow_back=True, repo_dir=repo_dir)
            if ans == "<BACK>":
                print(f"\n{THEME.warn(_t('canceled_return'))}")
                maybe_restore_auto_stash(repo_dir, auto_stashed)
                return
            if not ensure_not_on_base(ans, branch):
                pause_continue()
                continue
            state["base_branch"] = ans
            step += 1

        elif step == 1:
            ans = ask_yes_no("fetch_origin_q", default=state["do_fetch"], allow_back=True, repo_dir=repo_dir)
            if ans == "<BACK>":
                step -= 1
                continue
            state["do_fetch"] = ans
            if ans: run("git fetch origin", cwd=repo_dir)
            dt, dr = detect_history_type(repo_dir, state["base_branch"])
            state["detected_type"] = dt
            state["detected_reason"] = dr

            has_conflict, c_lines, supported = check_potential_conflict(repo_dir, state["base_branch"])
            if supported:
                if has_conflict:
                    state["conflict_status"] = "conflict"
                    state["conflict_count"] = len(c_lines)
                    print(f"\n{THEME.err(_t('predict_conflict_warn', base=state['base_branch']))}")
                    for line in c_lines[:5]:
                        print(f"  {THEME.dim(line)}")
                    if len(c_lines) > 5:
                        print(f"  {THEME.dim(f'... ({len(c_lines) - 5} conflicts more)')}")
                    pause_continue()
                else:
                    state["conflict_status"] = "clean"
                    print(f"\n{THEME.ok(_t('predict_conflict_clean', base=state['base_branch']))}")
                    pause_continue()
            else:
                state["conflict_status"] = "unsupported"

            step += 1

        elif step == 2:
            print(f"\n{THEME.info('--- Auto Detect ---')}")
            print(f"{state['detected_reason']}")
            ans = ask_yes_no("use_detected_history_q", default=True, allow_back=True, repo_dir=repo_dir, type=state["detected_type"])
            if ans == "<BACK>":
                step -= 1
                continue
            if ans is True: state["history_type"] = state["detected_type"]
            else:
                h_ans = ask_choice("choose_history_type", ["opt_hist_clean", "opt_hist_merged"], default_index=0 if state["detected_type"] == "clean" else 1, allow_back=True, repo_dir=repo_dir)
                if h_ans == "<BACK>": continue
                state["history_type"] = "clean" if h_ans == "opt_hist_clean" else "merged"
            bp = get_effective_base_point(repo_dir, state["base_branch"], state["history_type"])
            if not bp:
                pause_continue()
                continue
            state["base_point"] = bp
            state["commit_total"] = commit_count_since(repo_dir, bp)
            state["commits"] = get_commit_preview(repo_dir, bp, limit=50)
            if state["commit_total"] == 0:
                print(f"\n{THEME.warn(_t('no_commits_to_squash'))}")
                pause_continue()
                step -= 1
                continue
            step += 1

        elif step == 3:
            ans = ask_yes_no("create_backup_q", default=state["do_backup"], allow_back=True, repo_dir=repo_dir)
            if ans == "<BACK>":
                step -= 1
                continue
            state["do_backup"] = ans
            step += 1

        elif step == 4:
            preview_lines = [format_commit_line(c) for c in state["commits"]]
            if state["commit_total"] > len(state["commits"]):
                preview_lines += [THEME.dim("..."), THEME.dim("(Truncated)")]
            print_box("Preview Commits to Squash", preview_lines)
            ans = ask_non_empty("final_commit_msg", default=state["final_msg"], allow_back=True, repo_dir=repo_dir)
            if ans == "<BACK>":
                step -= 1
                continue
            state["final_msg"] = ans
            step += 1

        elif step == 5:
            ans = ask_yes_no("auto_push_q", default=state["auto_push"], allow_back=True, repo_dir=repo_dir)
            if ans == "<BACK>":
                step -= 1
                continue
            state["auto_push"] = ans
            step += 1

        elif step == 6:
            show_action_plan(state["base_point"], state["final_msg"], state["base_branch"], branch, state["commit_total"], state["auto_push"])
            ans = ask_yes_no("continue_steps_q", default=True, allow_back=True, repo_dir=repo_dir)
            if ans == "<BACK>":
                step -= 1
                continue
            if not ans:
                print(f"\n{THEME.err(_t('ee_rage_quit'))}")
                maybe_restore_auto_stash(repo_dir, auto_stashed)
                return
            break

        # --- BẮT ĐẦU CHẠY GIT ---
        # LƯU TRẠNG THÁI GỐC ĐỂ ROLLBACK
        original_commit = git_output("git rev-parse HEAD", cwd=repo_dir)

        backup_branch_name = None
        if state["do_backup"]:
            backup_branch_name = create_backup(repo_dir, branch)
            print(f"\n{THEME.ok(_t('created_backup'))} {THEME.branch(backup_branch_name)}")

        run(f"git reset --soft {state['base_point']}", cwd=repo_dir)
        run(f"git commit -m {quote_arg(state['final_msg'])}", cwd=repo_dir)

        conflict_occurred = False
        try:
            run(f"git rebase origin/{state['base_branch']}", cwd=repo_dir)
        except RuntimeError:
            if is_rebase_in_progress(repo_dir):
                print(THEME.warn("Rebase stopped. Switching to recovery mode."))
                result = handle_rebase_recovery(repo_dir)
                if result == "completed":
                    conflict_occurred = True
                elif result in ("aborted", "menu"):
                    # Gợi ý Rollback nếu user chủ động hủy rebase
                    if ask_yes_no("rollback_q", default=True, repo_dir=repo_dir):
                        perform_rollback(repo_dir, original_commit)
                    else:
                        print(THEME.warn(_t("rollback_abort")))
                    maybe_restore_auto_stash(repo_dir, auto_stashed)
                    return
            else:
                # Gợi ý Rollback nếu dính lỗi runtime Git không mong muốn
                if ask_yes_no("rollback_q", default=True, repo_dir=repo_dir):
                    perform_rollback(repo_dir, original_commit)
                else:
                    print(THEME.warn(_t("rollback_abort")))
                maybe_restore_auto_stash(repo_dir, auto_stashed)
                return

        # --- CHẠY BƯỚC VERIFY POST-REBASE ---
        verify_passed = run_verification(repo_dir, state, branch, backup_branch_name, conflict_occurred)

        if not verify_passed:
            # Nếu Verify thất bại và user có bật Auto Push
            if state["auto_push"]:
                if ask_yes_no("verify_push_q", False, repo_dir=repo_dir):
                    # User quyết định khô máu Push Force
                    try:
                        run(f"git push --force-with-lease -u origin {quote_arg(branch)}", cwd=repo_dir)
                    except RuntimeError:
                        run(f"git push -f -u origin {quote_arg(branch)}", cwd=repo_dir)
                    maybe_restore_auto_stash(repo_dir, auto_stashed)
                    print(f"\n{THEME.ok(_t('flow_done'))}")
                    return
                else:
                    print(THEME.warn(_t("warn_cancel_auto_push")))

            # Nếu Verify thất bại, hỏi user có muốn Rollback cứu cánh không
            if ask_yes_no("rollback_q", default=True, repo_dir=repo_dir):
                perform_rollback(repo_dir, original_commit)
            else:
                print(THEME.warn(_t("rollback_abort")))
            maybe_restore_auto_stash(repo_dir, auto_stashed)
            return
        else:
            # Verify passed hoàn hảo, tiến hành push (nếu có)
            if state["auto_push"]:
                try:
                    run(f"git push --force-with-lease -u origin {quote_arg(branch)}", cwd=repo_dir)
                except RuntimeError:
                    run(f"git push -f -u origin {quote_arg(branch)}", cwd=repo_dir)

        maybe_restore_auto_stash(repo_dir, auto_stashed)
        print(f"\n{THEME.ok(_t('flow_done'))}")

# ============================================================
# Main loop
# ============================================================
def choose_language() -> None:
    global CURRENT_LANG
    clear_screen()
    print(f"\n{THEME.info('=== CÀI ĐẶT NGÔN NGỮ / TONE ===')}")
    print(f"  {THEME.choice('1.')} Tiếng Việt (Chuyên nghiệp) - Dành cho dev đứng đắn")
    print(f"  {THEME.choice('2.')} Tiếng Việt (Cợt nhả) - Thích hợp để troll sếp")
    print(f"  {THEME.choice('3.')} Tiếng Việt (Chợ búa, toxic) - Cảnh báo: Chửi mạnh, dành cho người lười")
    print(f"  {THEME.choice('4.')} English (Professional) - Standard dev life")

    while True:
        ans = input(f"{THEME.info('?')} Chọn số (1-4) {THEME.dim('[Bỏ qua / Giữ nguyên]')}: ").strip()
        if not ans:
            break
        if ans == "1": CURRENT_LANG = "vn_pro"; break
        if ans == "2": CURRENT_LANG = "vn_joke"; break
        if ans == "3": CURRENT_LANG = "vn_toxic"; break
        if ans == "4": CURRENT_LANG = "en_pro"; break
        print(THEME.warn("Nhập từ 1 đến 4 đi má / Please enter 1 to 4."))

def main() -> None:
    choose_language()
    clear_screen()
    ensure_git_installed()
    repo_dir = resolve_repo_dir()
    clear_screen()

    hour = datetime.now().hour
    if hour >= 23 or hour <= 4:
        print(f"\n{THEME.warn(_t('ee_night_owl'))}")

    while True:
        show_startup(repo_dir)

        if is_rebase_in_progress(repo_dir):
            print(THEME.warn("Repo in dirty rebase state."))
            choice = ask_choice("choose_action", ["m_recover", "m_checkout", "m_change", "m_refresh", "m_lang", "m_emoji", "m_exit"], 0, repo_dir=repo_dir)
        else:
            choice = ask_choice("main_menu", ["m_start", "m_checkout", "m_change", "m_refresh", "m_lang", "m_emoji", "m_exit"], 0, repo_dir=repo_dir)

        if choice == "m_recover":
            clear_screen()
            show_startup(repo_dir)
            try: handle_rebase_recovery(repo_dir)
            except Exception:
                print(THEME.err("Unexpected error in recovery:"))
                traceback.print_exc()
            continue

        if choice == "m_start":
            clear_screen()
            try: run_feature_flow(repo_dir)
            except RuntimeError as e:
                print(THEME.warn(_t("flow_stopped")))
            except Exception:
                print(THEME.err(_t("flow_error")))
                traceback.print_exc()
            continue

        if choice == "m_checkout":
            handle_checkout(repo_dir)
            continue

        if choice == "m_change":
            clear_screen()
            show_startup(repo_dir)
            repo_dir = ask_repo_path()
            clear_screen()
            continue

        if choice == "m_refresh":
            clear_screen()
            continue

        if choice == "m_lang":
            choose_language()
            clear_screen()
            continue

        if choice == "m_emoji":
            global EMOJI_MODE
            EMOJI_MODE = not EMOJI_MODE
            clear_screen()
            msg = "Đã BẬT Emoji Mode 😏🔥 (Quẩy thôi!)" if EMOJI_MODE else "Đã TẮT Emoji Mode 😶 (Quay về thực tại)"
            print(THEME.ok(msg))
            continue

        if choice == "m_exit":
            print(THEME.ok(_t("goodbye")))
            pause_exit(0)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n{THEME.warn('Canceled by user.')}")
        pause_exit(130)
    except Exception:
        print(f"\n{THEME.err('Unexpected fatal error:')}")
        traceback.print_exc()
        pause_exit(1)
