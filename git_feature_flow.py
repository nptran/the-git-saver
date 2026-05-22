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
from typing import List, Optional, Tuple, Any

# ============================================================
# CƠ CHẾ LOAD CẤU HÌNH THÔNG MINH (NO-CODE SEPARATION)
# ============================================================
CURRENT_LANG = "vn_pro"
EMOJI_MODE = False
SHOW_CMD_LOG = True  # Mặc định True cho vn_pro, sẽ được set lại trong main()
CMD_HISTORY_BUFFER = []  # Nơi lưu trữ các lệnh đã chạy trong phiên

# Biến lưu trạng thái GitHub CLI
GH_AVAILABLE = False
GH_ERROR_KEY = ""


# ============================================================
# GITHUB CLI MODULE
# ============================================================
def init_gh_cli() -> None:
    """Quét ngầm trạng thái GitHub CLI lúc khởi động hoặc refresh"""
    global GH_AVAILABLE, GH_ERROR_KEY
    try:
        # Check xem có cài CLI chưa
        result = subprocess.run(
            "gh --version", shell=True, text=True, capture_output=True
        )
        if result.returncode != 0:
            GH_AVAILABLE = False
            GH_ERROR_KEY = "no_gh_err"
            return

        # Check xem đã login chưa
        auth = subprocess.run(
            "gh auth status", shell=True, text=True, capture_output=True
        )
        if auth.returncode != 0:
            GH_AVAILABLE = False
            GH_ERROR_KEY = "no_gh_auth_err"
            return

        GH_AVAILABLE = True
        GH_ERROR_KEY = ""
    except Exception:
        GH_AVAILABLE = False
        GH_ERROR_KEY = "no_gh_err"


def ensure_gh_installed() -> None:
    result = subprocess.run("gh --version", shell=True, text=True, capture_output=True)
    if result.returncode != 0:
        print(THEME.err(_t("no_gh_err")))
        pause_continue()
        return False

    auth = subprocess.run("gh auth status", shell=True, text=True, capture_output=True)
    if auth.returncode != 0:
        print(THEME.err(_t("no_gh_auth_err")))
        pause_continue()
        return False
    return True


def check_valid_pr(repo_dir: str, source: str, target: str, regex_pattern: str) -> bool:
    print(THEME.info(f"Đang kiểm tra Pull Request từ {source} -> {target}..."))
    cmd = f"gh pr list --base {target} --head {source} --state open --json title"
    output = run(cmd, cwd=repo_dir, capture=True, silent=True)

    try:
        prs = json.loads(output)
        for pr in prs:
            if re.match(regex_pattern, pr["title"]):
                print(THEME.ok(f"Đã xác nhận PR hợp lệ: {pr['title']}"))
                return True
    except Exception as e:
        print(THEME.err(f"Lỗi parse JSON từ gh cli: {e}"))

    print(
        THEME.err(_t("pr_not_found", source=source, target=target, regex=regex_pattern))
    )
    return False


def is_merge_in_progress(repo_dir: str) -> bool:
    git_dir = get_git_dir(repo_dir)
    return (git_dir / "MERGE_HEAD").exists()


def load_json_config(filename: str) -> dict:
    if getattr(sys, "frozen", False):
        external_base = os.path.dirname(sys.executable)
        internal_base = sys._MEIPASS
    else:
        external_base = os.path.dirname(os.path.abspath(__file__))
        internal_base = external_base

    external_path = os.path.join(external_base, "config", filename)
    internal_path = os.path.join(internal_base, "config", filename)

    if os.path.exists(external_path):
        try:
            with open(external_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"[Cảnh báo] File custom {filename} bị lỗi cú pháp JSON: {e}")

    if os.path.exists(internal_path):
        try:
            with open(internal_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass

    print(f"🚨 LỖI HỆ THỐNG: Bị thiếu file cấu hình {filename}!")
    return {}


EMOJI_MAP = load_json_config("emoji_map.json")
LANGUAGES = load_json_config("languages.json")


# ============================================================
# CƠ CHẾ LƯU TRỮ CHỈ SỐ (STATS MEMORY)
# ============================================================
def get_stats_path() -> str:
    if getattr(sys, "frozen", False):
        current_dir = os.path.dirname(sys.executable)
    else:
        current_dir = os.path.dirname(os.path.abspath(__file__))

    # Logic vị trí thông minh
    if os.path.basename(current_dir).lower() == "dist":
        base_path = os.path.dirname(current_dir)
    else:
        base_path = current_dir

    return os.path.join(base_path, "data", "stats.json")


def ensure_data_dir():
    """Đảm bảo thư mục data tồn tại ngay lập tức"""
    path = get_stats_path()
    data_dir = os.path.dirname(path)
    if not os.path.exists(data_dir):
        try:
            os.makedirs(data_dir, exist_ok=True)
        except Exception as e:
            # Nếu không tạo được thư mục, in thông báo để user biết (không dùng _t vì lúc này
            # chưa chắc load xong config)
            print(
                f"\n[!] Critical Error: Cannot create data directory at {data_dir}: {e}"
            )


def load_stats() -> dict:
    # Luôn đảm bảo thư mục tồn tại trước khi làm bất cứ việc gì liên quan đến file
    ensure_data_dir()
    path = get_stats_path()
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            pass
    return {"rebase_count": 0, "first_run": datetime.now().strftime("%Y-%m-%d")}


def increment_rebase_stat():
    # Đảm bảo thư mục tồn tại trước khi ghi
    ensure_data_dir()

    path = get_stats_path()
    stats = load_stats()
    stats["rebase_count"] = stats.get("rebase_count", 0) + 1
    stats["last_run"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(stats, f, indent=4)
    except Exception as e:
        print(f"\n{THEME.err('! Lỗi ghi file stats.json:')} {e}")

    return stats["rebase_count"]


def _t(key: str, **kwargs) -> str:
    lang_dict = LANGUAGES.get(key, {})

    msg_data = lang_dict.get(CURRENT_LANG)
    if not msg_data:
        msg_data = lang_dict.get("vn_pro", lang_dict.get("en_pro", key))

    if isinstance(msg_data, list):
        msg = random.choice(msg_data)
    else:
        msg = msg_data

    if kwargs:
        try:
            msg = msg.format(**kwargs)
        except Exception:
            pass

    if EMOJI_MODE and key in EMOJI_MAP:
        msg = f"{msg} {EMOJI_MAP.get(key, '')}"

    return msg


# ============================================================
# Quoting Helper (Xử lý chuỗi an toàn cho Windows CMD & Unix)
# ============================================================
def quote_arg(arg: str) -> str:
    if os.name == "nt":
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
        if not self.use_color:
            return text
        return "".join(styles) + text + self.RESET

    def bold(self, text: str) -> str:
        return self.s(text, self.BOLD)

    def dim(self, text: str) -> str:
        return self.s(text, self.DIM)

    def info(self, text: str) -> str:
        return self.s(text, self.BRIGHT_CYAN, self.BOLD)

    def ok(self, text: str) -> str:
        return self.s(text, self.BRIGHT_GREEN, self.BOLD)

    def warn(self, text: str) -> str:
        return self.s(text, self.BRIGHT_YELLOW, self.BOLD)

    def err(self, text: str) -> str:
        return self.s(text, self.BRIGHT_RED, self.BOLD)

    def branch(self, text: str) -> str:
        return self.s(text, self.BRIGHT_BLUE, self.BOLD)

    def commit(self, text: str) -> str:
        return self.s(text, self.BRIGHT_MAGENTA, self.BOLD)

    def count(self, text: str) -> str:
        return self.s(text, self.BRIGHT_YELLOW, self.BOLD)

    def cmd(self, text: str) -> str:
        return self.s(text, self.GREEN, self.BOLD)

    def choice(self, text: str) -> str:
        return self.s(text, self.CYAN, self.BOLD)

    def key(self, text: str) -> str:
        return self.s(text, self.BRIGHT_CYAN, self.BOLD)

    def tag_feat(self, text: str) -> str:
        return self.s(text, self.BRIGHT_GREEN, self.BOLD)

    def tag_fix(self, text: str) -> str:
        return self.s(text, self.BRIGHT_YELLOW, self.BOLD)

    def tag_refactor(self, text: str) -> str:
        return self.s(text, self.BRIGHT_MAGENTA, self.BOLD)

    def tag_other(self, text: str) -> str:
        return self.s(text, self.BRIGHT_CYAN, self.BOLD)


THEME = Theme(
    use_color=supports_color(sys.stdout),
    use_unicode_box=supports_unicode_box(sys.stdout),
)


def box_chars():
    if THEME.use_unicode_box:
        return {
            "tl": "╔",
            "tr": "╗",
            "bl": "╚",
            "br": "╝",
            "h": "═",
            "v": "║",
            "lt": "╠",
            "rt": "╣",
        }
    return {
        "tl": "+",
        "tr": "+",
        "bl": "+",
        "br": "+",
        "h": "-",
        "v": "|",
        "lt": "+",
        "rt": "+",
    }


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
        print(
            THEME.branch(f"{BOX['v']} ")
            + line
            + (" " * padding)
            + THEME.branch(f" {BOX['v']}")
        )
    print(THEME.branch(bottom))


# ============================================================
# Git Error Decoder
# ============================================================
def get_friendly_git_error(stderr_str: str) -> str:
    stderr_lower = stderr_str.lower()

    if (
            "could not resolve host" in stderr_lower
            or "authentication failed" in stderr_lower
            or "permission denied" in stderr_lower
    ):
        return _t("err_network")
    if "conflict" in stderr_lower:
        return _t("err_conflict")
    if (
            "would be overwritten by" in stderr_lower
            or "please commit your changes or stash them" in stderr_lower
    ):
        return _t("err_overwrite")
    if (
            "fetch first" in stderr_lower
            or "non-fast-forward" in stderr_lower
            or "updates were rejected" in stderr_lower
    ):
        return _t("err_push_rejected")

    return _t("err_unknown")


# ============================================================
# Shell / Git helpers
# ============================================================
def run(
        cmd: str,
        cwd: Optional[str] = None,
        check: bool = True,
        capture: bool = False,
        silent: bool = False,
        is_user_cmd: bool = False,
) -> str:
    # Nếu không silent, đẩy vào bộ nhớ tạm
    if not silent:
        prefix = " [USER] " if is_user_cmd else " [AUTO] "
        timestamp = datetime.now().strftime("%H:%M:%S")
        # Lưu vào buffer với định dạng đẹp
        CMD_HISTORY_BUFFER.append(
            f"{THEME.dim(timestamp)}{THEME.ok(prefix)}{THEME.cmd(cmd)}"
        )

    if capture:
        result = subprocess.run(
            cmd, shell=True, text=True, capture_output=True, cwd=cwd
        )
        stdout_val = result.stdout or ""
        stderr_val = result.stderr or ""
    else:
        result = subprocess.run(
            cmd, shell=True, text=True, stderr=subprocess.PIPE, cwd=cwd
        )
        stdout_val = ""
        stderr_val = result.stderr or ""

    if check and result.returncode != 0:
        if stderr_val:
            print(THEME.err(stderr_val.rstrip()), file=sys.stderr)

        if cwd:
            print(THEME.warn(f"Working directory: {cwd}"))

        friendly_msg = get_friendly_git_error(stderr_val)
        print(f"\n{THEME.branch(BOX['tl'] + BOX['h'] * 50)}")
        print(
            f"{THEME.branch(BOX['v'])} {THEME.info('💡 GIẢI MÃ LỖI / ERROR DECODER:')}"
        )
        print(f"{THEME.branch(BOX['v'])} {friendly_msg}")
        print(f"{THEME.branch(BOX['bl'] + BOX['h'] * 50)}\n")

        raise RuntimeError(f"Command failed: {cmd}")

    return stdout_val.strip()


def git_output(cmd: str, cwd: Optional[str] = None, check: bool = True) -> str:
    # Mọi lệnh lấy output (thường là lệnh đọc trạng thái) thì nên im lặng cho đỡ rối UI
    return run(cmd, cwd=cwd, check=check, capture=True, silent=True)


def ensure_git_installed() -> None:
    result = subprocess.run("git --version", shell=True, text=True, capture_output=True)
    if result.returncode != 0:
        print(THEME.err(_t("no_git_err")))
        print(THEME.warn(_t("no_git_warn")))
        pause_exit(1)


# ============================================================
# Smart Git Command Interceptor (Thiết Quân Luật -C & Check Code)
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

    ans = (
        input(f"\n{THEME.info('?')} {_t('smart_git_confirm')} {THEME.ok('[Y/n]')}: ")
        .strip()
        .lower()
    )
    if ans in ("", "y", "yes"):
        # Tách phần tham số sau chữ 'git '
        args = command[3:].strip()
        safe_repo = quote_arg(repo_dir)

        # Thiết quân luật cờ -C để đảm bảo chạy đúng repo
        exact_command = f"git -C {safe_repo} {args}"

        try:
            # GỌI HÀM RUN CỦA TOOL:
            # - Không dùng silent vì muốn nó hiện trong Log Panel sau khi refresh
            # - is_user_cmd=True để đánh dấu prefix [USER] trong buffer
            run(exact_command, cwd=repo_dir, check=True, is_user_cmd=True)

            # Nếu chạy đến đây tức là returncode = 0 (vì hàm run có check=True)
            print(THEME.ok(_t("smart_git_done")))

        except RuntimeError:
            # Lỗi lệnh Git (Return code != 0) đã được hàm run() handle in thông báo lỗi
            pass
        except Exception as e:
            # Lỗi hệ thống (Python/Subprocess)
            print(THEME.err(f"Lỗi hệ thống khi thực thi: {e}"))

        pause_continue()
        return True
    else:
        ans2 = (
            input(
                f"{THEME.info('?')} Có muốn dùng cụm '{command}' như câu trả lời bình thường thay "
                f"vì lệnh Git không? [y/N]: "
            )
            .strip()
            .lower()
        )
        if ans2 in ("y", "yes"):
            return False
        else:
            print(THEME.warn(_t("smart_git_cancel")))
            return True


# ============================================================
# Prompt helpers (Hỗ trợ <REFRESH> và <GIT_RUN>)
# ============================================================
def ask_yes_no(
        question_key: str,
        default: bool = True,
        allow_back: bool = False,
        repo_dir: Optional[str] = None,
        **kwargs,
) -> Any:
    suffix = THEME.ok("[Y/n]") if default else THEME.warn("[y/N]")
    back_hint = THEME.dim(_t("type_back")) if allow_back else ""
    refresh_hint = THEME.dim(" (r: Refresh)")
    while True:
        answer = input(
            f"{THEME.info('?')} {_t(question_key, **kwargs)} {suffix}{back_hint}{refresh_hint}: "
        ).strip()

        if answer.lower() == "r":
            return "<REFRESH>"

        if repo_dir and answer.lower().startswith("git "):
            if handle_smart_git_command(answer, repo_dir):
                clear_screen()
                return "<GIT_RUN>"

        ans_lower = answer.lower()
        if allow_back and ans_lower == "<":
            return "<BACK>"
        if not ans_lower:
            return default
        if ans_lower in ("y", "yes"):
            return True
        if ans_lower in ("n", "no"):
            return False
        print(THEME.warn(_t("invalid_yn")))


def ask_non_empty(
        question_key: str,
        default: Optional[str] = None,
        allow_back: bool = False,
        repo_dir: Optional[str] = None,
) -> Any:
    back_hint = THEME.dim(_t("type_back")) if allow_back else ""
    refresh_hint = THEME.dim(" (r: Refresh)")
    while True:
        if default is None:
            answer = input(
                f"{THEME.info('?')} {_t(question_key)}{back_hint}{refresh_hint}: "
            ).strip()
        else:
            answer = input(
                f"{THEME.info('?')} {_t(question_key)} {THEME.dim('[' + default + ']')}"
                f"{back_hint}{refresh_hint}: "
            ).strip()

        if answer.lower() == "r":
            return "<REFRESH>"

        if repo_dir and answer.lower().startswith("git "):
            if handle_smart_git_command(answer, repo_dir):
                clear_screen()
                return "<GIT_RUN>"

        if allow_back and answer == "<":
            return "<BACK>"
        if not answer and default is not None:
            return default
        if answer:
            return answer
        print(THEME.warn(_t("not_empty")))


def ask_choice(
        question_key: str,
        option_keys: List[str],
        default_index: int = 0,
        allow_back: bool = False,
        repo_dir: Optional[str] = None,
        disabled_keys: List[str] = None,
) -> str:
    if disabled_keys is None:
        disabled_keys = []
    while True:
        print(f"\n{THEME.info('?')} {_t(question_key)}")
        for i, opt_key in enumerate(option_keys, start=1):
            marker = (
                f" {THEME.ok(_t('default_marker'))}" if i - 1 == default_index else ""
            )
            display = _t(opt_key)

            # HIỂN THỊ TRẠNG THÁI CHO EMOJI
            if opt_key == "m_emoji":
                state_str = "ON 🟢" if EMOJI_MODE else "OFF 🔴"
                display = f"{display} [{state_str}]"

            # HIỂN THỊ TRẠNG THÁI CHO COMMAND LOG
            if opt_key == "m_cmd_log":
                state_str = "ON 🖥️" if SHOW_CMD_LOG else "OFF ❌"
                display = f"{display} [{state_str}]"

            # XỬ LÝ LÀM MỜ NẾU OPTION BỊ DISABLE
            if opt_key in disabled_keys:
                print(f"  {THEME.dim(str(i) + '. ' + display + ' 🚫')}")
            else:
                print(f"  {THEME.choice(str(i) + '.')} {display}{marker}")

        if allow_back:
            print(f"  {THEME.choice('<.')} {_t('opt_back')}")

        answer = input(
            f"{THEME.info('?')} {_t('choose_num')} {THEME.dim('(r: Refresh) ')}"
        ).strip()

        if answer.lower() == "r":
            return "<REFRESH>"

        if repo_dir and answer.lower().startswith("git "):
            if handle_smart_git_command(answer, repo_dir):
                clear_screen()
                return "<GIT_RUN>"

        if allow_back and answer == "<":
            return "<BACK>"
        if not answer:
            return option_keys[default_index]
        if answer.isdigit():
            idx = int(answer) - 1
            if 0 <= idx < len(option_keys):
                return option_keys[idx]
        clear_screen()
        print(THEME.warn(_t("invalid_choice")))


# ============================================================
# Repo detection helpers (Đường dẫn tuyệt đối)
# ============================================================
def is_git_repo(path: str) -> bool:
    result = subprocess.run(
        "git rev-parse --is-inside-work-tree",
        shell=True,
        text=True,
        capture_output=True,
        cwd=path,
    )
    return result.returncode == 0


def find_git_repo_upwards(start_path: str) -> Optional[str]:
    current = Path(start_path).resolve()
    for candidate in [current] + list(current.parents):
        if (candidate / ".git").exists():
            return str(candidate)
    return None


def ask_repo_path() -> str:
    while True:
        repo_path = input(f"{THEME.info('?')} {_t('enter_repo')}").strip().strip('"')
        if not repo_path:
            print(THEME.warn(_t("not_empty")))
            continue

        repo_path = os.path.abspath(repo_path)

        if not os.path.isdir(repo_path):
            print(THEME.err(_t("repo_not_exist")))
            continue
        if not is_git_repo(repo_path):
            print(THEME.err(_t("not_git_repo")))
            continue
        return repo_path


def resolve_repo_dir() -> str:
    cwd = os.path.abspath(os.getcwd())
    if is_git_repo(cwd):
        return cwd
    guessed = find_git_repo_upwards(cwd)
    if guessed:
        print(THEME.warn(_t("cwd_not_git")))
        print(THEME.ok(_t("found_closest", guessed=guessed)))
        if ask_yes_no("use_this", True) is True:
            return guessed
    print(THEME.warn(_t("pls_choose_repo")))
    return ask_repo_path()


# ============================================================
# Working tree helpers (Tự làm mới vòng lặp)
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
    while True:
        changes = get_worktree_status(repo_dir)
        if not changes:
            return False

        print(THEME.warn(_t("wt_dirty_warn")))
        show_worktree_changes(changes)

        choice = ask_choice(
            "what_do_changes",
            ["opt_stash", "opt_no_stash", "opt_cancel"],
            default_index=0,
            repo_dir=repo_dir,
        )

        if choice in ("<GIT_RUN>", "<REFRESH>"):
            clear_screen()
            continue

        if choice == "opt_stash":
            run('git stash push -u -m "git-feature-flow auto-stash"', cwd=repo_dir)
            print(THEME.ok(_t("stashed_ok")))
            return True

        if choice == "opt_no_stash":
            print(THEME.warn(_t("warn_no_stash")))
            ans = ask_yes_no("sure_no_stash", False, repo_dir=repo_dir)
            if ans in ("<GIT_RUN>", "<REFRESH>"):
                clear_screen()
                continue
            if ans is True:
                return False
            print(THEME.warn(_t("canceled_return")))
            return None

        print(THEME.warn(_t("canceled_return")))
        return None


def maybe_restore_auto_stash(repo_dir: str, auto_stashed: bool) -> None:
    if not auto_stashed:
        return
    restore = ask_yes_no("restore_stash_q", True, repo_dir=repo_dir)
    if restore is True:
        run("git stash pop", cwd=repo_dir)
        print(THEME.ok(_t("restored_stash")))
    else:
        print(THEME.warn(_t("kept_stash")))


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
    colored = pattern.sub(
        lambda m: hl_ansi + m.group(0) + THEME.RESET + base_ansi, b_name
    )
    return base_ansi + colored + THEME.RESET


def handle_checkout(repo_dir: str) -> bool:
    local_branches_str = git_output(
        "git branch --format=%(refname:short)", cwd=repo_dir
    )
    local_branches = [
        clean_branch_name(b) for b in local_branches_str.splitlines() if b.strip()
    ]

    remote_branches_str = git_output(
        "git branch -r --format=%(refname:short)", cwd=repo_dir
    )
    remote_branches_raw = [
        clean_branch_name(b) for b in remote_branches_str.splitlines() if b.strip()
    ]
    remote_branches = [
        b for b in remote_branches_raw if "origin/HEAD" not in b and b != "origin"
    ]

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
    if total_count >= 50:
        alert_msg = THEME.warn(_t("branch_count_many", count=total_count))
    elif total_count <= 5:
        alert_msg = THEME.ok(_t("branch_count_few", count=total_count))

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

        if ans.lower() == "r":
            continue

        if ans.lower().startswith("git "):
            if handle_smart_git_command(ans, repo_dir):
                continue

        if not ans:
            return False

        if ans.lower() == "f":
            alert_msg = THEME.info(_t("fetching_remote"))
            print(f"\n{alert_msg}")
            run("git fetch origin --prune", cwd=repo_dir)
            return handle_checkout(repo_dir)

        target = None
        if ans.isdigit():
            idx = int(ans) - 1
            if 0 <= idx < len(current_list):
                target = current_list[idx]
        elif ans in current_list:
            target = ans
        else:
            matches = [b for b in all_branches if ans.lower() in b.lower()]
            if not matches:
                alert_msg = THEME.warn(_t("branch_not_found"))
                # Reset lại danh sách hiển thị về toàn bộ nhánh khi search xịt
                current_list = all_branches
                search_kw = ""
                continue
            elif len(matches) == 1:
                target = matches[0]
                print(THEME.info(_t("branch_search_single", target=target)))
            else:
                search_kw = ans
                alert_msg = THEME.info(
                    _t("branch_search_found", count=len(matches), kw=ans)
                )
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
    if not git_path.is_absolute():
        git_path = Path(repo_dir) / git_path
    return git_path


def is_rebase_in_progress(repo_dir: str) -> bool:
    git_dir = get_git_dir(repo_dir)
    return (git_dir / "rebase-merge").exists() or (git_dir / "rebase-apply").exists()


def get_conflicted_files(repo_dir: str) -> List[str]:
    output = git_output(
        "git diff --name-only --diff-filter=U", cwd=repo_dir, check=False
    )
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
        if len(files) > 30:
            lines += [THEME.dim("..."), THEME.dim("(Truncated)")]
    print_box("Conflicted Files", lines)


def handle_rebase_recovery(repo_dir: str) -> str:
    while True:
        if not is_rebase_in_progress(repo_dir):
            print(THEME.ok(_t("rebase_ext_success")))
            return "completed"

        conflict_files = get_conflicted_files(repo_dir)
        lines = [
            _t("rebase_paused_1"),
            _t("rebase_paused_2"),
            _t("rebase_paused_3"),
            _t("rebase_paused_4", count=len(conflict_files)),
        ]
        print_box("Rebase Recovery", lines)

        choice = ask_choice(
            "choose_action",
            [
                "opt_show_status",
                "opt_show_conflict",
                "opt_continue",
                "opt_abort",
                "opt_return",
            ],
            0,
            repo_dir=repo_dir,
        )

        if choice in ("<GIT_RUN>", "<REFRESH>"):
            clear_screen()
            continue

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
                        ans = ask_yes_no("rebase_skip_q", True, repo_dir=repo_dir)
                        if ans in ("<GIT_RUN>", "<REFRESH>"):
                            continue
                        if ans is True:
                            try:
                                run(
                                    "git -c core.editor=true rebase --skip",
                                    cwd=repo_dir,
                                )
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
            ans = ask_yes_no("opt_abort_confirm", False, repo_dir=repo_dir)
            if ans in ("<GIT_RUN>", "<REFRESH>"):
                continue
            if not ans:
                continue
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


def check_potential_conflict(
        repo_dir: str, base_branch: str
) -> Tuple[bool, List[str], bool]:
    cmd = f"git merge-tree --write-tree origin/{base_branch} HEAD"
    try:
        result = subprocess.run(
            cmd, shell=True, text=True, capture_output=True, cwd=repo_dir
        )
        if result.returncode == 0:
            return False, [], True
        elif result.returncode == 1:
            c_lines = [
                line.strip()
                for line in result.stdout.splitlines()
                if "CONFLICT" in line
            ]
            return True, c_lines, True
        else:
            return False, [], False
    except Exception:
        return False, [], False


def create_backup(repo_dir: str, branch: str) -> str:
    ts = datetime.now().strftime("%Y%m%d-%H%M%S")
    backup_branch = f"backup/{branch.replace('/', '-')}-{ts}"
    run(f"git branch {quote_arg(backup_branch)}", cwd=repo_dir)
    return backup_branch


def get_effective_base_point(
        repo_dir: str, base_branch: str, history_type: str
) -> Optional[str]:
    cmd = (
        f"git merge-base HEAD origin/{base_branch}"
        if history_type == "clean"
        else f"git merge-base --fork-point origin/{base_branch} HEAD"
    )
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
    merge_commit_count = int(
        git_output(f"git rev-list --merges --count {merge_base}..HEAD", cwd=repo_dir)
    )

    if merge_commit_count > 0:
        return "merged", _t("merged_reason", count=merge_commit_count, base=merge_base)
    return "clean", _t("clean_reason", base=merge_base)


def get_commit_preview(repo_dir: str, base_point: str, limit: int = 50) -> List[str]:
    output = git_output(
        f"git log --oneline --no-decorate {base_point}..HEAD -n {limit}", cwd=repo_dir
    )
    return output.splitlines() if output else []


def get_diff_patch_id(repo_dir: str, base_ref: str, target_ref: str) -> str:
    diff_output = git_output(
        f"git diff {base_ref}...{target_ref}", cwd=repo_dir, check=False
    )
    if not diff_output.strip():
        return "empty"

    try:
        p = subprocess.Popen(
            ["git", "patch-id", "--stable"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=repo_dir,
        )
        out, err = p.communicate(input=diff_output.encode("utf-8"))
        if p.returncode == 0 and out:
            return out.decode("utf-8").split()[0]
    except Exception:
        pass

    cleaned = re.sub(r"@@.*?@@", "", diff_output)
    cleaned = re.sub(r"\s+", "", cleaned)
    return cleaned


def run_verification(
        repo_dir: str,
        state: dict,
        branch: str,
        backup_branch: Optional[str],
        conflict_occurred: bool,
) -> bool:
    print(f"\n{THEME.branch(BOX['tl'] + BOX['h'] * 80)}")
    print(f"{THEME.branch(BOX['v'])} {THEME.info(_t('verify_title'))}")

    passed = True
    behind = 0

    run(f"git fetch origin {state['base_branch']}", cwd=repo_dir, capture=True)

    try:
        rev_count = git_output(
            f"git rev-list --left-right --count origin/{state['base_branch']}...HEAD",
            cwd=repo_dir,
        )
        behind, ahead = map(int, rev_count.split())
        if behind > 0:
            print(
                f"{THEME.branch(BOX['v'])} "
                f"{THEME.err(_t('verify_ahead_fail', base=state['base_branch'], behind=behind))}"
            )
            passed = False
        else:
            print(
                f"{THEME.branch(BOX['v'])} "
                f"{THEME.ok(_t('verify_ahead_ok', base=state['base_branch'], ahead=ahead))}"
            )
    except Exception:
        print(
            f"{THEME.branch(BOX['v'])} {THEME.warn('Không thể kiểm tra Ahead/Behind.')}"
        )

    reference_ref = backup_branch if backup_branch else f"origin/{branch}"
    if not git_output(
            f"git rev-parse --verify {reference_ref}", cwd=repo_dir, check=False
    ):
        reference_ref = None

    if not reference_ref:
        print(f"{THEME.branch(BOX['v'])} {THEME.err(_t('verify_no_ref'))}")
    else:
        old_patch_id = get_diff_patch_id(repo_dir, state["base_point"], reference_ref)
        new_patch_id = get_diff_patch_id(
            repo_dir, f"origin/{state['base_branch']}", "HEAD"
        )

        if old_patch_id == new_patch_id:
            print(f"{THEME.branch(BOX['v'])} {THEME.ok(_t('verify_patch_ok'))}")
        else:
            passed = False
            print(f"{THEME.branch(BOX['v'])} {THEME.warn(_t('verify_patch_diff'))}")
            if conflict_occurred:
                print(
                    f"{THEME.branch(BOX['v'])} {THEME.dim(_t('verify_conflict_reason'))}"
                )
            else:
                print(
                    f"{THEME.branch(BOX['v'])} {THEME.err(_t('verify_missing_reason'))}"
                )

            diff_cmd = f"git diff {reference_ref} HEAD"
            print(
                f"{THEME.branch(BOX['v'])} {THEME.info(_t('verify_diff_cmd'))} "
                f"{THEME.cmd(diff_cmd)}"
            )

    print(f"{THEME.branch(BOX['bl'] + BOX['h'] * 80)}\n")
    return passed


# ============================================================
# Rollback Engine
# ============================================================
def perform_rollback(repo_dir: str, original_commit: str) -> None:
    print(f"\n{THEME.warn(_t('rollback_in_progress'))}")
    if is_rebase_in_progress(repo_dir):
        run("git rebase --abort", cwd=repo_dir, check=False)
    run(f"git reset --hard {original_commit}", cwd=repo_dir)
    print(THEME.ok(_t("rollback_success")))


# ============================================================
# Commit line formatting
# ============================================================
COMMIT_TYPE_RE = re.compile(
    r"^(feat|fix|refactor|chore|docs|test)(\(.+?\))?:", re.IGNORECASE
)


def highlight_commit_message(message: str) -> str:
    match = COMMIT_TYPE_RE.match(message)
    if not match:
        return message
    commit_type, prefix = match.group(1).lower(), match.group(0)
    if commit_type == "feat":
        colored_prefix = THEME.tag_feat(prefix)
    elif commit_type == "fix":
        colored_prefix = THEME.tag_fix(prefix)
    elif commit_type == "refactor":
        colored_prefix = THEME.tag_refactor(prefix)
    else:
        colored_prefix = THEME.tag_other(prefix)
    return colored_prefix + message[len(prefix):]


def format_commit_line(line: str) -> str:
    parts = line.split(" ", 1)
    if len(parts) == 1:
        return f"• {THEME.commit(parts[0])}"
    return f"• {THEME.commit(parts[0])} {highlight_commit_message(parts[1])}"


# ============================================================
# UI blocks - WIZARD DASHBOARD
# ============================================================
def show_startup(repo_dir: str) -> None:
    try:
        branch = current_branch(repo_dir)
    except Exception:
        branch = "(unknown / initial)"

    stats = load_stats()
    total = stats.get("rebase_count", 0)

    # Xác định danh hiệu (Rank)
    rank = "Newbie"
    if total >= 30:
        rank = "Grandmaster Trash Cleaner 👑"
    elif total >= 15:
        rank = "Senior Garbage Man 🧹"
    elif total > 0:
        rank = "Junior Sweeper 🧺"

    # Nếu là mode toxic, đổi tên danh hiệu cho bựa
    if CURRENT_LANG == "vn_toxic":
        if total >= 30:
            rank = "CHÚA TỂ DỌN RÁC 💀"
        elif total >= 15:
            rank = "THẰNG NGHIỆN SQUASH 💉"
        elif total > 0:
            rank = "KẺ HỐT RÁC THUÊ 🚮"

    lines = [
        f"{THEME.key('Repo')}     : {repo_dir}",
        f"{THEME.key('Branch')}   : {THEME.branch(branch)}",
        f"{THEME.key('Success')}  : {THEME.count(str(total))} times ({THEME.warn(rank)})",
    ]
    print_box("Feature Branch Squash + Rebase Assistant", lines)


def show_wizard_dashboard(state: dict, current_step: int) -> None:
    def check(step_idx: int) -> str:
        if current_step > step_idx:
            return THEME.ok("[✓]")
        if current_step == step_idx:
            return THEME.warn("[►]")
        return THEME.dim("[ ]")

    lines = []

    v0 = THEME.branch(state.get("base_branch", "")) if current_step > 0 else "..."
    lines.append(f"{check(0)} {_t('dash_base_branch').ljust(18)} : {v0}")

    v1 = "Yes" if state.get("do_fetch") else "No"
    v1 = THEME.choice(v1) if current_step > 1 else "..."
    lines.append(f"{check(1)} {_t('dash_fetch').ljust(18)} : {v1}")

    if state.get("conflict_status"):
        c_stat = state["conflict_status"]
        if c_stat == "clean":
            c_str = THEME.ok(_t("dash_predict_clean"))
        elif c_stat == "conflict":
            c_str = THEME.err(
                _t("dash_predict_conflict", count=state.get("conflict_count", 0))
            )
        else:
            c_str = THEME.dim("N/A")
        lines.append(f"       └─ {THEME.dim(_t('dash_predict') + ':')} {c_str}")

    v2 = THEME.choice(state.get("history_type", "")) if current_step > 2 else "..."
    lines.append(f"{check(2)} {_t('dash_history').ljust(18)} : {v2}")
    if current_step > 2 and state.get("commit_total", 0) > 0:
        lines.append(
            f"       └─ {THEME.dim('Commits to squash:')} {THEME.count(str(state['commit_total']))}"
        )

    v3 = "Yes" if state.get("do_backup") else "No"
    v3 = THEME.choice(v3) if current_step > 3 else "..."
    lines.append(f"{check(3)} {_t('dash_backup').ljust(18)} : {v3}")

    v4 = THEME.commit(state.get("final_msg", "")) if current_step > 4 else "..."
    lines.append(f"{check(4)} {_t('dash_msg').ljust(18)} : {v4}")

    v5 = "Yes" if state.get("auto_push") else "No"
    v5 = THEME.choice(v5) if current_step > 5 else "..."
    lines.append(f"{check(5)} {_t('dash_push').ljust(18)} : {v5}")

    print_box(_t("dash_title"), lines)

    if current_step > 2 and state.get("commit_total", 0) >= 20:
        print(f"  {THEME.warn(_t('ee_spam_commit', count=state['commit_total']))}")


def show_action_plan(
        base_point: str,
        final_message: str,
        base_branch: str,
        feature_branch: str,
        commit_count: int,
        auto_push: bool,
) -> None:
    pad_base = base_branch.ljust(15)
    pad_feat = feature_branch.ljust(15)

    sketch = [
        f"{THEME.dim('[TRƯỚC / BEFORE]')}",
        f" {THEME.branch(pad_base)} ──○──○──◉──○──○ (origin)",
        "                         \\",
        f" {THEME.branch(pad_feat)}          ○──○──○ ({commit_count} commits)",
        "",
        f"{THEME.dim('[SAU / AFTER]')}",
        f" {THEME.branch(pad_base)} ──○──○──◉──○──○ (origin)",
        "                                     \\",
        f" {THEME.branch(pad_feat)}                      🌟 (1 squashed)",
    ]
    print_box("Rebase Flow Sketch", sketch)

    lines = [
        THEME.cmd(f"1. git reset --soft {base_point}"),
        THEME.cmd(f'2. git commit -m "{final_message}"'),
        THEME.cmd(f"3. git rebase origin/{base_branch}"),
    ]
    if auto_push:
        lines.append(THEME.cmd("4. git push --force-with-lease"))
    print_box("Commands to execute", lines)


# ============================================================
# Core flow (STATE MACHINE WIZARD)
# ============================================================
def run_feature_flow(repo_dir: str) -> None:
    if is_rebase_in_progress(repo_dir):
        print(THEME.warn("Repo is in rebase progress state."))
        if handle_rebase_recovery(repo_dir) in ("completed", "aborted", "menu"):
            return

    # Bước khởi tạo state
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
        "conflict_count": 0,
    }

    auto_stashed = False
    step = 0
    max_step = 6

    while step <= max_step:
        # Luôn lấy lại tên nhánh để đồng bộ với tác động bên ngoài
        branch = current_branch(repo_dir)

        clear_screen()
        print(f"\n{THEME.ok('Current branch:')} {THEME.branch(branch)}")

        # HIỆN LOG PANEL TRONG WIZARD (Gom nhóm các lệnh fetch/sync đã chạy)
        print_cmd_log_panel()

        show_wizard_dashboard(state, current_step=step)

        # JIT Check: Kiểm tra bẩn repo trước mỗi bước nhập liệu
        changes = get_worktree_status(repo_dir)
        if changes and not auto_stashed:
            res = handle_dirty_worktree(repo_dir)
            if res is None:
                return  # User chọn Cancel
            auto_stashed = res
            continue  # Quay lại đầu vòng lặp để cập nhật UI

        if step == 0:
            state["conflict_status"] = None
            ans = ask_non_empty(
                "base_branch_name",
                state["base_branch"],
                allow_back=True,
                repo_dir=repo_dir,
            )
            if ans in ("<GIT_RUN>", "<REFRESH>"):
                continue
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
            ans = ask_yes_no(
                "fetch_origin_q",
                default=state["do_fetch"],
                allow_back=True,
                repo_dir=repo_dir,
            )
            if ans in ("<GIT_RUN>", "<REFRESH>"):
                continue
            if ans == "<BACK>":
                step -= 1
                continue
            state["do_fetch"] = ans
            if ans:
                # Fetch toàn diện (sử dụng hàm run mặc định để đẩy vào buffer)
                run(
                    'git fetch origin "+refs/heads/*:refs/remotes/origin/*" --prune',
                    cwd=repo_dir,
                )

                # Đồng bộ hóa Fast-forward nếu có commit mới trên server
                try:
                    # Lấy commit ID của local và server để so sánh
                    local_head = git_output("git rev-parse HEAD", cwd=repo_dir)
                    remote_ref = f"origin/{branch}"

                    # Kiểm tra xem origin branch có tồn tại không
                    if git_output(
                            f"git rev-parse --verify {remote_ref}",
                            cwd=repo_dir,
                            check=False,
                    ):
                        remote_head = git_output(
                            f"git rev-parse {remote_ref}", cwd=repo_dir
                        )

                        if local_head != remote_head:
                            # Kiểm tra xem có phải là Fast-forward được không (local là tổ tiên
                            # của remote)
                            is_ancestor = (
                                    subprocess.run(
                                        f"git merge-base --is-ancestor {local_head} {remote_head}",
                                        shell=True,
                                        cwd=repo_dir,
                                        capture_output=True,
                                    ).returncode
                                    == 0
                            )

                            if is_ancestor:
                                print(
                                    THEME.warn(
                                        f" Nhận diện có commit mới trên server ({remote_ref})."
                                    )
                                )
                                print(
                                    THEME.info(
                                        ">>> Đang tự động Fast-forward local lên bản mới nhất..."
                                    )
                                )
                                run(f"git merge --ff-only {remote_ref}", cwd=repo_dir)
                            else:
                                # Trường hợp Diverged (cả local và server đều có commit mới khác
                                # nhau)
                                print(
                                    THEME.err(
                                        "\n🚨 NGUY HIỂM: Nhánh Local và Server đang bị lệch pha ("
                                        "Diverged)!"
                                    )
                                )
                                print(
                                    THEME.warn(
                                        "Vui lòng tự tay 'git pull' hoặc xử lý thủ công trước khi "
                                        "dùng tool."
                                    )
                                )
                                pause_continue()
                                return
                except Exception as e:
                    print(THEME.dim(f"(Bỏ qua kiểm tra đồng bộ: {e})"))

            # Sau khi đồng bộ xong mới tính toán lịch sử
            dt, dr = detect_history_type(repo_dir, state["base_branch"])
            state["detected_type"] = dt
            state["detected_reason"] = dr

            # Dự đoán conflict
            has_conflict, c_lines, supported = check_potential_conflict(
                repo_dir, state["base_branch"]
            )
            if supported:
                state["conflict_status"] = "conflict" if has_conflict else "clean"
                state["conflict_count"] = len(c_lines) if has_conflict else 0
            step += 1

        elif step == 2:
            print(f"\n{THEME.info('--- Auto Detect ---')}")
            print(f"{state['detected_reason']}")
            ans = ask_yes_no(
                "use_detected_history_q",
                default=True,
                allow_back=True,
                repo_dir=repo_dir,
                type=state["detected_type"],
            )
            if ans in ("<GIT_RUN>", "<REFRESH>"):
                continue
            if ans == "<BACK>":
                step -= 1
                continue
            if ans is True:
                state["history_type"] = state["detected_type"]
            else:
                h_ans = ask_choice(
                    "choose_history_type",
                    ["opt_hist_clean", "opt_hist_merged"],
                    default_index=0,
                    allow_back=True,
                    repo_dir=repo_dir,
                )
                if h_ans in ("<GIT_RUN>", "<REFRESH>"):
                    continue
                if h_ans == "<BACK>":
                    continue
                state["history_type"] = (
                    "clean" if h_ans == "opt_hist_clean" else "merged"
                )
            bp = get_effective_base_point(
                repo_dir, state["base_branch"], state["history_type"]
            )
            if not bp:
                pause_continue()
                continue
            state["base_point"] = bp
            state["commit_total"] = commit_count_since(repo_dir, bp)
            state["commits"] = get_commit_preview(repo_dir, bp, limit=50)
            if state["commit_total"] == 0:
                print(f"\n{THEME.warn(_t('no_commits_to_squash'))}")
                pause_continue()
                step = 0  # Quay về chọn lại base branch vì nhánh này hiện tại khớp base rồi
                continue
            step += 1

        elif step == 3:
            ans = ask_yes_no(
                "create_backup_q",
                default=state["do_backup"],
                allow_back=True,
                repo_dir=repo_dir,
            )
            if ans in ("<GIT_RUN>", "<REFRESH>"):
                continue
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
            ans = ask_non_empty(
                "final_commit_msg",
                default=state["final_msg"],
                allow_back=True,
                repo_dir=repo_dir,
            )
            if ans in ("<GIT_RUN>", "<REFRESH>"):
                continue
            if ans == "<BACK>":
                step -= 1
                continue
            state["final_msg"] = ans
            step += 1

        elif step == 5:
            ans = ask_yes_no(
                "auto_push_q",
                default=state["auto_push"],
                allow_back=True,
                repo_dir=repo_dir,
            )
            if ans in ("<GIT_RUN>", "<REFRESH>"):
                continue
            if ans == "<BACK>":
                step -= 1
                continue
            state["auto_push"] = ans
            step += 1

        elif step == 6:
            show_action_plan(
                state["base_point"],
                state["final_msg"],
                state["base_branch"],
                branch,
                state["commit_total"],
                state["auto_push"],
            )
            ans = ask_yes_no(
                "continue_steps_q", default=True, allow_back=True, repo_dir=repo_dir
            )
            if ans in ("<GIT_RUN>", "<REFRESH>"):
                continue
            if ans == "<BACK>":
                step -= 1
                continue
            if not ans:
                print(f"\n{THEME.err(_t('ee_rage_quit'))}")
                maybe_restore_auto_stash(repo_dir, auto_stashed)
                return
            break

    # --- BẮT ĐẦU THỰC THI (SQUASH + REBASE) ---

    # Just-In-Time (JIT) Check: Quét chặn phút chót tránh xung đột IDE
    current_changes = get_worktree_status(repo_dir)
    if current_changes and not auto_stashed:
        print(f"\n{THEME.err(_t('jit_warning'))}\n{THEME.warn(_t('jit_abort'))}")
        pause_continue()
        return

    # LƯU TRẠNG THÁI GỐC ĐỂ ROLLBACK
    original_commit = git_output("git rev-parse HEAD", cwd=repo_dir)

    backup_branch_name = None
    if state["do_backup"]:
        backup_branch_name = create_backup(repo_dir, branch)
        print(f"\n{THEME.ok(_t('created_backup'))} {THEME.branch(backup_branch_name)}")

    # Gom commit
    run(f"git reset --soft {state['base_point']}", cwd=repo_dir)
    run(f"git commit -m {quote_arg(state['final_msg'])}", cwd=repo_dir)

    # Rebase
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
                ans = ask_yes_no("rollback_q", default=True, repo_dir=repo_dir)
                if ans is True or ans in ("<GIT_RUN>", "<REFRESH>"):
                    perform_rollback(repo_dir, original_commit)
                else:
                    print(THEME.warn(_t("rollback_abort")))
                maybe_restore_auto_stash(repo_dir, auto_stashed)
                return
        else:
            ans = ask_yes_no("rollback_q", default=True, repo_dir=repo_dir)
            if ans is True or ans in ("<GIT_RUN>", "<REFRESH>"):
                perform_rollback(repo_dir, original_commit)
            else:
                print(THEME.warn(_t("rollback_abort")))
            maybe_restore_auto_stash(repo_dir, auto_stashed)
            return

    # Verify & Push
    verify_passed = run_verification(
        repo_dir, state, branch, backup_branch_name, conflict_occurred
    )

    if not verify_passed:
        if state["auto_push"]:
            if ask_yes_no("verify_push_q", False, repo_dir=repo_dir) is True:
                try:
                    run(
                        f"git push --force-with-lease -u origin {quote_arg(branch)}",
                        cwd=repo_dir,
                    )
                except RuntimeError:
                    run(f"git push -f -u origin {quote_arg(branch)}", cwd=repo_dir)
                maybe_restore_auto_stash(repo_dir, auto_stashed)
                print(f"\n{THEME.ok(_t('flow_done'))}")
                return
            else:
                print(THEME.warn(_t("warn_cancel_auto_push")))

        rb_ans = ask_yes_no("rollback_q", default=True, repo_dir=repo_dir)
        if rb_ans is True or rb_ans in ("<GIT_RUN>", "<REFRESH>"):
            perform_rollback(repo_dir, original_commit)
        else:
            print(THEME.warn(_t("rollback_abort")))
        maybe_restore_auto_stash(repo_dir, auto_stashed)
        return
    else:
        if state["auto_push"]:
            try:
                run(
                    f"git push --force-with-lease -u origin {quote_arg(branch)}",
                    cwd=repo_dir,
                )
            except RuntimeError:
                run(f"git push -f -u origin {quote_arg(branch)}", cwd=repo_dir)

    maybe_restore_auto_stash(repo_dir, auto_stashed)

    # Stats & Easter Egg
    total_success = increment_rebase_stat()
    ee_key = "ee_rebase_milestone"
    if CURRENT_LANG == "vn_toxic":
        if total_success >= 30:
            ee_key = "vn_toxic_level_3"
        elif total_success >= 15:
            ee_key = "vn_toxic_level_2"
        else:
            ee_key = "vn_toxic_level_1"

    # Hiển thị Easter Egg ở các mốc chia hết cho 5 hoặc lần đầu tiên
    if total_success % 5 == 0 or total_success == 1:
        print(f"\n{THEME.info('⭐ ' + _t(ee_key, count=total_success))}")

    print(f"\n{THEME.ok(_t('flow_done'))}")


def print_cmd_log_panel():
    if not SHOW_CMD_LOG or not CMD_HISTORY_BUFFER:
        return

    # Giới hạn chỉ hiện 10 lệnh gần nhất để đỡ tràn màn hình
    display_history = CMD_HISTORY_BUFFER[-10:]
    if len(CMD_HISTORY_BUFFER) > 10:
        display_history = [THEME.dim("... (older commands hidden)")] + display_history

    print_box(_t("cmd_log_title"), display_history)


# ============================================================
# Main loop
# ============================================================
def choose_language() -> None:
    global CURRENT_LANG, SHOW_CMD_LOG
    clear_screen()
    print(f"\n{THEME.warn('=== CÀI ĐẶT NGÔN NGỮ / TONE ===')}")
    print("  1. Tiếng Việt (Chuyên nghiệp) - Dành cho dev đứng đắn")
    print("  2. Tiếng Việt (Cợt nhả) - Thích hợp để troll sếp")
    print("  3. Tiếng Việt (Chợ búa, toxic) - Cảnh báo: Chửi mạnh, dành cho người lười")
    print("  4. English (Professional) - Standard dev life")

    while True:
        # Lấy input và xóa khoảng trắng thừa ở 2 đầu
        ans = input(f"{THEME.key('? Chọn số (1-4) [Bỏ qua / Giữ nguyên]: ')}").strip()

        # Nếu nhấn Enter bỏ qua
        if not ans:
            break

        # Kiểm tra điều kiện (So sánh chuỗi để tránh lỗi ép kiểu)
        if ans == "1":
            CURRENT_LANG = "vn_pro"
            SHOW_CMD_LOG = True
            break
        elif ans == "2":
            CURRENT_LANG = "vn_joke"
            SHOW_CMD_LOG = False
            break
        elif ans == "3":
            CURRENT_LANG = "vn_toxic"
            SHOW_CMD_LOG = False
            break
        elif ans == "4":
            CURRENT_LANG = "en_pro"
            SHOW_CMD_LOG = True
            break
        else:
            # Chửi đúng theo vibe toxic nếu nhập sai
            msg = "Nhập từ 1 đến 4 đi má / Please enter 1 to 4."
            print(f"{THEME.err(msg)}")


# ============================================================
# PIPELINE DEPLOY CHUẨN
# ============================================================
def run_deploy_flow(repo_dir: str) -> None:
    if not ensure_gh_installed():
        return

    clear_screen()
    print(f"\n{THEME.branch('=== PIPELINE DEPLOY CHUẨN ===')}")
    choice = ask_choice(
        "Chọn luồng Deploy:",
        ["1. Develop -> Test", "2. Test -> Main", "3. Hủy"],
        0,
        repo_dir=repo_dir,
    )

    if choice == "3. Hủy" or choice in ("<GIT_RUN>", "<REFRESH>", "<BACK>"):
        return

    source, target, regex = (
        ("develop", "test", r"^Test \d{4}-\d{2}-\d{2}\.\d+$")
        if "Develop" in choice
        else ("test", "main", r"^Release \d{4}-\d{2}-\d{2}\.\d+$")
    )

    # Bước 1: Check PR bằng GitHub CLI
    if not check_valid_pr(repo_dir, source, target, regex):
        pause_continue()
        return

    print(f"\n{THEME.info('>>> Bắt đầu luồng Merge an toàn...')}")

    # Bước 2: Fetch & Checkout
    run("git fetch origin --prune", cwd=repo_dir)
    run(f"git checkout {target}", cwd=repo_dir)
    run(f"git pull origin {target}", cwd=repo_dir)

    # Bước 3: Merge --no-ff
    try:
        run(
            f'git merge origin/{source} --no-ff -m "chore: merge {source} to {target} for '
            f'deployment"',
            cwd=repo_dir,
        )
    except RuntimeError:
        if is_merge_in_progress(repo_dir):
            print(THEME.err(_t("merge_paused")))
            print(
                THEME.warn(
                    "Vui lòng xử lý conflict, dùng lệnh 'git add', sau đó 'git commit' thủ công."
                )
            )
            pause_continue()
            return
        else:
            print(THEME.err("Merge thất bại không rõ lý do."))
            pause_continue()
            return

    # Bước 4: Verify Local (Ahead/Behind local so với source)
    print(THEME.info("\n>>> Verify Lần 1 (Local)..."))
    left_right = git_output(
        "git rev-list --left-right --count HEAD...origin/main", cwd=repo_dir
    )
    ahead, behind = map(int, left_right.split())
    if behind > 0:
        print(
            THEME.err(
                f"FAIL: Local {target} vẫn đang behind {source} {behind} commit! Merge có vấn đề."
            )
        )
        pause_continue()
        return
    print(THEME.ok("PASS: Local đã update đầy đủ commit từ source."))

    # Bước 5: Push
    if (
            ask_yes_no(
                f"Merge xong. Đẩy (Push) lên origin/{target} ngay?", True, repo_dir=repo_dir
            )
            is True
    ):
        run(f"git push origin {target}", cwd=repo_dir)

        # Bước 6: Verify Origin
        print(THEME.info("\n>>> Verify Lần 2 (Origin)..."))
        orig_left_right = git_output(
            f"git rev-list --left-right --count origin/{target}...origin/{source}",
            cwd=repo_dir,
        )
        o_ahead, o_behind = map(int, orig_left_right.split())
        if o_behind > 0:
            print(
                THEME.err(
                    f"FAIL: Origin {target} vẫn behind origin/{source} {o_behind} commit!"
                )
            )
        else:
            print(THEME.ok(f"PASS: Deploy thành công lên {target}!"))

    pause_continue()


# =============================================================
# PIPELINE BACKPORT HOTFIX (THỬ NGHIỆM)
# =============================================================
def run_hotfix_flow(repo_dir: str) -> None:
    clear_screen()
    print(
        f"\n{THEME.err('=== ⚠️ LUỒNG BACKPORT HOTFIX (MAIN -> TEST & DEVELOP) ⚠️ ===')}"
    )
    print(
        THEME.warn(
            "Lưu ý: Luồng này sử dụng chiến lược Merge (--no-ff) để đẩy ngược code từ Main."
        )
    )
    print(
        THEME.warn(
            "Tuyệt đối KHÔNG DÙNG REBASE ở luồng này để tránh phá vỡ nhánh dùng chung."
        )
    )

    if ask_yes_no("Bạn có hiểu và muốn tiếp tục?", False, repo_dir=repo_dir) is False:
        return

    targets = ["test", "develop"]
    run("git fetch origin --prune", cwd=repo_dir)

    for target in targets:
        print(f"\n{THEME.branch(f'--- XỬ LÝ NHÁNH: {target.upper()} ---')}")
        run(f"git checkout {target}", cwd=repo_dir)
        run(f"git pull origin {target}", cwd=repo_dir)

        try:
            run(
                f'git merge origin/main --no-ff -m "chore: backport hotfix from main to {target}"',
                cwd=repo_dir,
            )
        except RuntimeError:
            if is_merge_in_progress(repo_dir):
                print(THEME.err(f"Bị CONFLICT khi đổ hotfix vào {target}!"))
                print(
                    THEME.warn(
                        "Tool sẽ tạm dừng. Hãy dùng IDE gỡ conflict, 'git add' và 'git commit'."
                    )
                )
                print(
                    THEME.warn(
                        "Sau khi xong, chạy lại tính năng này để xử lý nhánh tiếp theo."
                    )
                )
                pause_continue()
                return

        # Verify
        left_right = git_output(
            "git rev-list --left-right --count HEAD...origin/main", cwd=repo_dir
        )
        _, behind = map(int, left_right.split())
        if behind > 0:
            print(THEME.err(f"FAIL: {target} chưa nhận đủ code từ main!"))
            pause_continue()
            return

        run(f"git push origin {target}", cwd=repo_dir)
        print(THEME.ok(f"✅ Đã backport Hotfix thành công vào {target}."))

    print(f"\n{THEME.ok('🎉 HOÀN TẤT LUỒNG HOTFIX!')}")
    pause_continue()


def main() -> None:
    # Đảm bảo thư mục data tồn tại ngay khi bật tool
    ensure_data_dir()
    # Quét GitHub CLI ngay khi khởi động
    init_gh_cli()

    choose_language()
    clear_screen()
    ensure_git_installed()
    repo_dir = resolve_repo_dir()
    clear_screen()

    hour = datetime.now().hour
    if hour >= 23 or hour <= 4:
        print(f"\n{THEME.warn(_t('ee_night_owl'))}")

    while True:
        # Cập nhật giao diện chính
        clear_screen()
        show_startup(repo_dir)

        # HIỂN THỊ CONSOLE LOG PANEL (GOM NHÓM LỆNH)
        print_cmd_log_panel()

        # Tạo mảng chứa các option bị vô hiệu hóa
        disabled_opts = []
        if not GH_AVAILABLE:
            disabled_opts.extend(["m_deploy", "m_hotfix"])

        if is_rebase_in_progress(repo_dir) or is_merge_in_progress(repo_dir):
            print(THEME.warn("Repo đang kẹt trong trạng thái Rebase/Merge."))
            choice = ask_choice(
                "choose_action",
                [
                    "m_recover",
                    "m_checkout",
                    "m_change",
                    "m_refresh",
                    "m_lang",
                    "m_emoji",
                    "m_cmd_log",
                    "m_exit",
                ],
                0,
                repo_dir=repo_dir,
            )
        else:
            menu_options = [
                "m_start",  # 1. Squash
                "m_deploy",  # 2. Deploy
                "m_hotfix",  # 3. Hotfix
                "m_checkout",  # 4.
                "m_change",  # 5.
                "m_refresh",  # 6.
                "m_lang",  # 7.
                "m_emoji",  # 8.
                "m_cmd_log",  # 9.
                "m_exit",  # 10.
            ]
            # Truyền mảng disabled vào UI
            choice = ask_choice(
                "main_menu",
                menu_options,
                0,
                repo_dir=repo_dir,
                disabled_keys=disabled_opts,
            )

        # Xử lý các lựa chọn hệ thống
        if choice in ("<GIT_RUN>", "<REFRESH>", "m_refresh"):
            # Làm sạch buffer log khi chủ động refresh
            CMD_HISTORY_BUFFER.clear()
            init_gh_cli()  # Quét lại nhỡ đâu user vừa cài đặt/login gh xong
            clear_screen()
            continue

        if choice == "m_recover":
            clear_screen()
            show_startup(repo_dir)
            try:
                handle_rebase_recovery(repo_dir)
            except Exception:
                print(THEME.err("Unexpected error in recovery:"))
                traceback.print_exc()
            continue

        if choice == "m_start":
            clear_screen()
            try:
                run_feature_flow(repo_dir)
            except RuntimeError:
                print(THEME.warn(_t("flow_stopped")))
            except Exception:
                print(THEME.err(_t("flow_error")))
                traceback.print_exc()
            continue

        if choice == "m_deploy":
            if not GH_AVAILABLE:
                print(f"\n{THEME.err(_t(GH_ERROR_KEY))}")
                pause_continue()
                continue
            run_deploy_flow(repo_dir)
            continue

        if choice == "m_hotfix":
            if not GH_AVAILABLE:
                print(f"\n{THEME.err(_t(GH_ERROR_KEY))}")
                pause_continue()
                continue
            run_hotfix_flow(repo_dir)
            continue

        if choice == "m_checkout":
            handle_checkout(repo_dir)
            continue

        if choice == "m_change":
            clear_screen()
            # Đổi repo thì nên xóa log của repo cũ
            CMD_HISTORY_BUFFER.clear()
            show_startup(repo_dir)
            repo_dir = ask_repo_path()
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
            msg = (
                "Đã BẬT Emoji Mode 😏🔥 (Quẩy thôi!)"
                if EMOJI_MODE
                else "Đã TẮT Emoji Mode 😶 (Quay về thực tại)"
            )
            print(THEME.ok(msg))
            continue

        if choice == "m_cmd_log":
            global SHOW_CMD_LOG
            SHOW_CMD_LOG = not SHOW_CMD_LOG
            clear_screen()

            status = "HIỆN 🖥️" if SHOW_CMD_LOG else "ẨN ❌"
            if CURRENT_LANG == "vn_toxic":
                msg = f"Command Log Panel: {status} (Đỡ rác mắt chưa thằng l*n?)"
            elif CURRENT_LANG == "vn_joke":
                msg = f"Command Log Panel: {status} (👨‍💻 Trẻ trâu đú đởn mode)"
            else:
                msg = f"Command Log Panel: {status}"

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
