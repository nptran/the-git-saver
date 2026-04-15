#!/usr/bin/env python3
import os
import re
import shlex
import subprocess
import sys
import traceback
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Tuple

# ============================================================
# I18N - Hệ thống ngôn ngữ & Emoji Mode 😏🔥
# ============================================================
CURRENT_LANG = "vn_pro"
EMOJI_MODE = False

EMOJI_MAP = {
    "press_exit": "🛑", "no_git_err": "❌", "no_git_warn": "⚠️", "invalid_yn": "🤔",
    "not_empty": "✍️", "choose_num": "🔢", "invalid_choice": "🤦", "default_marker": "✨",
    "main_menu": "📋", "m_start": "🚀", "m_checkout": "🔀", "m_change": "📂", "m_refresh": "🔄",
    "m_lang": "🗣️", "m_emoji": "🤪", "m_exit": "🏃", "m_recover": "🚑",
    "enter_repo": "🔍", "repo_not_exist": "👻", "not_git_repo": "🚫", "cwd_not_git": "🤷",
    "found_closest": "🎯", "use_this": "👉", "pls_choose_repo": "👇",
    "no_local_changes": "✨", "wt_dirty_warn": "🔥", "what_do_changes": "🤷‍♂️",
    "opt_stash": "📦", "opt_no_stash": "⚔️", "opt_cancel": "⛔", "stashed_ok": "✅",
    "warn_no_stash": "💀", "sure_no_stash": "🥶", "canceled_return": "🔙",
    "restore_stash_q": "♻️", "kept_stash": "🔒", "restored_stash": "🔓",
    "rebase_paused_1": "🚧", "rebase_paused_2": "🛠️", "rebase_paused_3": "🚦",
    "rebase_paused_4": "💥", "choose_action": "🕹️", "opt_show_status": "👀",
    "opt_show_conflict": "⚔️", "opt_continue": "➡️", "opt_abort": "🛑",
    "opt_return": "🔙", "rebase_not_done": "⏳", "rebase_success": "🎉",
    "on_base_branch": "🏠", "checkout_feature_first": "🔀", "base_branch_name": "🌳",
    "fetch_origin_q": "☁️", "merged_reason": "🍝", "clean_reason": "🧼",
    "use_detected_history_q": "🤖", "opt_hist_clean": "✨", "opt_hist_merged": "🌪️",
    "no_commits_to_squash": "🫙", "create_backup_q": "🛡️", "created_backup": "💾",
    "final_commit_msg": "📝", "auto_push_q": "🚀", "continue_steps_q": "🏁",
    "flow_done": "🏆", "goodbye": "👋😏", "choose_history_type": "🗂️",
    
    # Error Emojis
    "err_network": "🔌", "err_conflict": "⚔️💥", "err_overwrite": "🛑📝", 
    "err_push_rejected": "⛔", "err_unknown": "👽",

    # Checkout flow Emojis
    "ask_checkout_now": "✈️", "list_branches": "🌿", "checkout_success": "✅", "checkout_fail": "💥",
    "fetching_remote": "☁️🔄", "branch_search_found": "🎯", "branch_search_single": "✨",
    "branch_count_few": "🌱", "branch_count_many": "🌳💀",

    # Easter Eggs Emojis
    "ee_night_owl": "🦉🌙", "ee_massive_stash": "🦝📦", "ee_spam_commit": "🤡🗑️"
}

LANGUAGES = {
    "press_exit": {
        "vn_pro": "\nNhấn Enter để thoát...", "vn_joke": "\nNhấn Enter để sủi bọt...", "vn_toxic": "\nĐập Enter để cút nhanh...", "en_pro": "\nPress Enter to exit..."
    },
    "no_git_err": {
        "vn_pro": "Không tìm thấy Git trong PATH.", "vn_joke": "Sếp ơi, máy sếp chưa cài Git à? Kì cục vậy.", "vn_toxic": "Đéo thấy Git đâu trong PATH! Mày dev bằng niềm tin à?", "en_pro": "Git not found in PATH."
    },
    "no_git_warn": {
        "vn_pro": "Hãy cài Git for Windows và đảm bảo lệnh 'git' chạy được trong terminal.", "vn_joke": "Lên Google tải Git về cài dùm tui nha sếp.", "vn_toxic": "Vác mặt đi tải Git for Windows cài vào ngay. Đếch hiểu kiểu gì.", "en_pro": "Please install Git and ensure 'git' command works in your terminal."
    },
    "invalid_yn": {
        "vn_pro": "Vui lòng nhập y hoặc n.", "vn_joke": "Gõ y hoặc n thôi ní ơi, đừng làm khó nhau.", "vn_toxic": "Mù à? Gõ y hoặc n thôi!", "en_pro": "Please enter y or n."
    },
    "not_empty": {
        "vn_pro": "Không được để trống.", "vn_joke": "Nhập gì đó vào đi sếp, để trống sao chạy.", "vn_toxic": "Bỏ trống thế đéo nào được? Gõ vào!", "en_pro": "Cannot be empty."
    },
    "choose_num": {
        "vn_pro": "Chọn số:", "vn_joke": "Bấm số đi sếp:", "vn_toxic": "Bấm cmn số vào:", "en_pro": "Choose number:"
    },
    "invalid_choice": {
        "vn_pro": "Lựa chọn không hợp lệ.", "vn_joke": "Bấm sai rồi kìa, chọn lại đi.", "vn_toxic": "Lác à? Chọn sai bét, chọn lại!", "en_pro": "Invalid choice."
    },
    "default_marker": {
        "vn_pro": "(mặc định)", "vn_joke": "(cái này auto nè)", "vn_toxic": "(mặc định rồi, lười thì ấn enter)", "en_pro": "(default)"
    },

    # Menus
    "main_menu": {
        "vn_pro": "Menu chính", "vn_joke": "Menu xịn xò", "vn_toxic": "Làm mẹ gì thì chọn đi", "en_pro": "Main menu"
    },
    "m_start": {
        "vn_pro": "Bắt đầu luồng squash + rebase", "vn_joke": "Bắt đầu dọn dẹp (squash + rebase)", "vn_toxic": "Chạy squash + rebase dọn rác đi", "en_pro": "Start squash + rebase flow"
    },
    "m_checkout": {
        "vn_pro": "Checkout / Đổi nhánh (Tìm kiếm)", "vn_joke": "Lượn sang nhánh khác (Search nhanh)", "vn_toxic": "Tìm và Cút sang nhánh khác", "en_pro": "Checkout branch (Search)"
    },
    "m_change": {
        "vn_pro": "Đổi repo khác", "vn_joke": "Đổi sang project khác múa", "vn_toxic": "Đổi repo khác nhanh", "en_pro": "Change repo"
    },
    "m_refresh": {
        "vn_pro": "Làm mới trạng thái repo", "vn_joke": "F5 cho đời tươi mát", "vn_toxic": "Refresh mẹ lại xem nào", "en_pro": "Refresh current repo status"
    },
    "m_lang": {
        "vn_pro": "Đổi Ngôn ngữ / Tone", "vn_joke": "Đổi giọng điệu (Tone)", "vn_toxic": "Đổi giọng chửi", "en_pro": "Change Language / Tone"
    },
    "m_emoji": {
        "vn_pro": "Bật/Tắt Emoji Mode", "vn_joke": "Bật/Tắt múa Emoji", "vn_toxic": "Bật/Tắt cái Emoji rác rưởi", "en_pro": "Toggle Emoji Mode"
    },
    "m_exit": {
        "vn_pro": "Thoát", "vn_joke": "Chuồn thôi", "vn_toxic": "Cút", "en_pro": "Exit"
    },
    "m_recover": {
        "vn_pro": "Mở trình khôi phục rebase", "vn_joke": "Cấp cứu ca rebase lỗi", "vn_toxic": "Vào sửa đống nát rebase", "en_pro": "Open rebase recovery"
    },

    # Repo detection
    "enter_repo": {
        "vn_pro": "Nhập đường dẫn Git repo: ", "vn_joke": "Ném cái link thư mục Git vô đây: ", "vn_toxic": "Paste cái đường dẫn repo vào lẹ lên: ", "en_pro": "Enter Git repo path: "
    },
    "repo_not_exist": {
        "vn_pro": "Đường dẫn không tồn tại hoặc không phải thư mục.", "vn_joke": "Đường dẫn ma à sếp? Không có thư mục này.", "vn_toxic": "Đường dẫn xạo chó à? Không thấy thư mục này đâu!", "en_pro": "Path does not exist or is not a directory."
    },
    "not_git_repo": {
        "vn_pro": "Thư mục này không phải Git repo.", "vn_joke": "Thư mục này trống không, chả thấy Git đâu sếp ơi.", "vn_toxic": "Chỗ này đéo phải Git repo, nhập sai rồi thằng ngáo!", "en_pro": "This directory is not a Git repo."
    },
    "cwd_not_git": {
        "vn_pro": "Thư mục hiện tại không phải Git repo.", "vn_joke": "Đang đứng ở chỗ không có Git sếp ạ.", "vn_toxic": "Thư mục hiện tại đéo có Git. Mù đường à?", "en_pro": "Current directory is not a Git repo."
    },
    "found_closest": {
        "vn_pro": "Phát hiện Git repo gần nhất: {guessed}", "vn_joke": "Mò ra được repo gần đây nè: {guessed}", "vn_toxic": "Thấy cái repo rác ở gần đây: {guessed}", "en_pro": "Detected closest Git repo: {guessed}"
    },
    "use_this": {
        "vn_pro": "Dùng repo này?", "vn_joke": "Chiến repo này luôn không sếp?", "vn_toxic": "Quất repo này không?", "en_pro": "Use this repo?"
    },
    "pls_choose_repo": {
        "vn_pro": "Vui lòng chọn Git repo muốn thao tác.", "vn_joke": "Chọn thư mục đi rồi tui làm cho.", "vn_toxic": "Chọn cái repo nào cần xử đi, mệt ghê.", "en_pro": "Please select the Git repo to operate on."
    },

    # Worktree changes
    "no_local_changes": {
        "vn_pro": "(Không có thay đổi local)", "vn_joke": "(Gọn gàng sạch sẽ không tì vết)", "vn_toxic": "(Đéo có file nào bị sửa)", "en_pro": "(No local changes)"
    },
    "wt_dirty_warn": {
        "vn_pro": "Phát hiện working tree đang có thay đổi chưa commit.", "vn_joke": "Ối sếp ơi, code đang gõ dở chưa commit kìa, vội thế?", "vn_toxic": "Đm sửa code xong vứt đấy đéo commit hả? Rác đầy working tree kìa!", "en_pro": "Detected uncommitted changes in the working tree."
    },
    "what_do_changes": {
        "vn_pro": "Bạn muốn làm gì với các thay đổi local này?", "vn_joke": "Giờ tính sao với đống code dở dang này?", "vn_toxic": "Tính làm cái quái gì với đống rác này?", "en_pro": "What do you want to do with these local changes?"
    },
    "opt_stash": {
        "vn_pro": "Auto stash rồi chạy tiếp (khuyến nghị)", "vn_joke": "Giấu code cẩn thận (stash) rồi quẩy tiếp", "vn_toxic": "Stash mẹ đống code lại rồi chạy tiếp", "en_pro": "Auto stash and continue (recommended)"
    },
    "opt_no_stash": {
        "vn_pro": "Vẫn chạy tiếp, không stash", "vn_joke": "Kệ nó, chơi khô máu luôn (không stash)", "vn_toxic": "Đéo cần stash, liều thì ăn nhiều", "en_pro": "Continue without stashing"
    },
    "opt_cancel": {
        "vn_pro": "Hủy và quay về menu", "vn_joke": "Quay xe sếp ơi, về menu", "vn_toxic": "Chim cút về menu", "en_pro": "Cancel and return"
    },
    "stashed_ok": {
        "vn_pro": "Đã stash local changes.", "vn_joke": "Giấu code xong rồi nha, yên tâm.", "vn_toxic": "Đã stash cái đống rác của mày lại rồi.", "en_pro": "Stashed local changes successfully."
    },
    "warn_no_stash": {
        "vn_pro": "Cẩn thận: local changes có thể bị gom vào commit cuối hoặc gây conflict khó hiểu.", "vn_joke": "Tới công chuyện nha, tí lỗi ráng chịu à.", "vn_toxic": "Cảnh báo cmn luôn: đéo stash tí conflict ráng mà tự gỡ ngu người nhé!", "en_pro": "Warning: changes might be included in final commit or cause obscure conflicts."
    },
    "sure_no_stash": {
        "vn_pro": "Bạn chắc chắn muốn tiếp tục mà không stash?", "vn_joke": "Chắc kèo là không giấu code (stash) không?", "vn_toxic": "Vẫn cố chấp đéo stash đúng không?", "en_pro": "Are you sure you want to continue without stashing?"
    },
    "canceled_return": {
        "vn_pro": "Đã hủy thao tác hiện tại. Quay về menu chính.", "vn_joke": "Đã quay xe thành công, về menu.", "vn_toxic": "Hủy cmnr. Quay về menu.", "en_pro": "Operation canceled. Returning to main menu."
    },
    "restore_stash_q": {
        "vn_pro": "Có restore lại local changes từ stash không?", "vn_joke": "Xong xuôi, có bứng code từ stash ra lại không?", "vn_toxic": "Có muốn pop lại đống stash ban nãy ra không?", "en_pro": "Restore local changes from stash?"
    },
    "kept_stash": {
        "vn_pro": "Đã giữ stash lại, chưa restore.", "vn_joke": "Code vẫn giấu trong stash nhe sếp.", "vn_toxic": "Vẫn vứt trong stash đấy, đéo pop đâu.", "en_pro": "Kept stash, not restored."
    },
    "restored_stash": {
        "vn_pro": "Đã restore local changes từ stash.", "vn_joke": "Đã trả lại code nguyên vẹn từ stash cho sếp.", "vn_toxic": "Đã nhả đống rác từ stash ra lại rồi đấy.", "en_pro": "Restored local changes from stash successfully."
    },

    # Rebase state
    "rebase_paused_1": {
        "vn_pro": "Rebase đang tạm dừng. Có thể do conflict hoặc cần bạn hoàn tất bước hiện tại.", "vn_joke": "Đang rebase thì kẹt xe sếp ạ. Chắc conflict ở đâu đó.", "vn_toxic": "Rebase đang nghẽn cmnr. Chắc do mày gõ conflict ngu học nào đó.", "en_pro": "Rebase is paused. Possibly due to conflicts or an incomplete step."
    },
    "rebase_paused_2": {
        "vn_pro": "Hãy resolve conflict trong file, rồi git add các file đã sửa.", "vn_joke": "Xử lý đống file đỏ chót kia đi, rồi git add tụi nó nha.", "vn_toxic": "Tự đi mà gỡ conflict trong file, xong thì git add mẹ nó vào.", "en_pro": "Please resolve conflicts, then git add the fixed files."
    },
    "rebase_paused_3": {
        "vn_pro": "Sau đó chọn Continue để tiếp tục, hoặc Abort để hủy rebase.", "vn_joke": "Xong xuôi thì chọn Continue đi tiếp, lười thì Abort bỏ ngang.", "vn_toxic": "Xong thì Continue, còn hoảng quá thì Abort mẹ đi cho lành.", "en_pro": "Then select Continue to proceed, or Abort to cancel rebase."
    },
    "rebase_paused_4": {
        "vn_pro": "Số file conflict hiện tại: {count}", "vn_joke": "Số file đang choảng nhau: {count}", "vn_toxic": "Có {count} cái file đang nát bét conflict:", "en_pro": "Current conflict files count: {count}"
    },
    "choose_action": {
        "vn_pro": "Chọn hành động", "vn_joke": "Sếp mún sao", "vn_toxic": "Tính làm đéo gì bây giờ", "en_pro": "Choose action"
    },
    "opt_show_status": {
        "vn_pro": "Show git status", "vn_joke": "Coi thử git status xem sao", "vn_toxic": "Xem git status", "en_pro": "Show git status"
    },
    "opt_show_conflict": {
        "vn_pro": "Show conflicted files", "vn_joke": "Liếc danh sách file conflict", "vn_toxic": "Xem mấy file nát conflict", "en_pro": "Show conflicted files"
    },
    "opt_continue": {
        "vn_pro": "Continue rebase", "vn_joke": "Continue thôi (đi tiếp)", "vn_toxic": "Continue rebase luôn sợ đéo gì", "en_pro": "Continue rebase"
    },
    "opt_abort": {
        "vn_pro": "Abort rebase", "vn_joke": "Abort (hủy kéo lại từ đầu)", "vn_toxic": "Abort mẹ đi cho rảnh nợ", "en_pro": "Abort rebase"
    },
    "opt_return": {
        "vn_pro": "Return to main menu", "vn_joke": "Tạm cất đó, về menu", "vn_toxic": "Tạm về menu chính", "en_pro": "Return to main menu"
    },
    "rebase_not_done": {
        "vn_pro": "Rebase vẫn chưa xong. Có thể còn conflict hoặc bạn chưa git add đủ file.", "vn_joke": "Chưa xong sếp ơi, check kĩ xem gỡ hết conflict chưa, nhớ git add nữa.", "vn_toxic": "Rebase đéo xong! Gỡ conflict ngu chưa git add à?", "en_pro": "Rebase is not done. Conflicts might remain or you missed git add."
    },
    "rebase_success": {
        "vn_pro": "Rebase completed successfully.", "vn_joke": "Tuyệt vời, rebase mượt mà như Sunsilk.", "vn_toxic": "Rebase xong cmnr, ngon lành.", "en_pro": "Rebase completed successfully."
    },
    "on_base_branch": {
        "vn_pro": "Bạn đang đứng trên base branch '{base}'.", "vn_joke": "Ủa sếp, đang đứng ở {base} múa may gì rứa?", "vn_toxic": "Đang đứng trên {base} thì squash cái đéo gì? Nháo à?", "en_pro": "You are currently on the base branch '{base}'."
    },
    "checkout_feature_first": {
        "vn_pro": "Hãy checkout sang feature branch trước rồi chạy lại.", "vn_joke": "Bay qua feature branch đi rồi quay lại tui làm cho.", "vn_toxic": "Checkout sang nhánh feature ngay rồi hẵng xài tool!", "en_pro": "Please checkout your feature branch first, then retry."
    },
    "base_branch_name": {
        "vn_pro": "Base branch name", "vn_joke": "Nhập tên branch gốc (VD: develop)", "vn_toxic": "Nhập tên branch gốc vào đây", "en_pro": "Base branch name"
    },
    "fetch_origin_q": {
        "vn_pro": "Fetch latest từ origin trước khi phân tích và chạy flow?", "vn_joke": "Fetch mới nhất từ server về múa cho chuẩn không sếp?", "vn_toxic": "Có fetch mẹ code mới nhất từ origin về không?", "en_pro": "Fetch latest from origin before analyzing?"
    },
    "merged_reason": {
        "vn_pro": "Phát hiện {count} merge commit kể từ merge-base {base}. Branch có vẻ không clean.", "vn_joke": "Thấy tận {count} cục merge kể từ base {base}. Nhánh nát quá sếp ơi.", "vn_toxic": "Đm có {count} cục merge rác kể từ {base}. Nhánh đéo clean tí nào.", "en_pro": "Detected {count} merge commits since merge-base {base}. Branch seems merged."
    },
    "clean_reason": {
        "vn_pro": "Không phát hiện merge commit kể từ merge-base {base}. Branch có vẻ clean.", "vn_joke": "Ngon lành, nhánh sạch sẽ không có merge rác nào từ base {base}.", "vn_toxic": "Nhánh có vẻ sạch, đéo có cục merge nào từ base {base}.", "en_pro": "No merge commits found since merge-base {base}. Branch seems clean."
    },
    "use_detected_history_q": {
        "vn_pro": "Dùng loại history auto-detect là '{type}'?", "vn_joke": "Tool bắt mạch là '{type}', quất luôn không sếp?", "vn_toxic": "Tự nhận diện history là '{type}', quất luôn không lằng nhằng?", "en_pro": "Use auto-detected history type '{type}'?"
    },
    "choose_history_type": {
        "vn_pro": "Chọn loại lịch sử commit:", "vn_joke": "Nhánh này thuộc hệ gì sếp:", "vn_toxic": "Tự khai xem nhánh nát hay sạch:", "en_pro": "Select commit history type:"
    },
    "opt_hist_clean": {
        "vn_pro": "clean - branch sạch, chưa từng merge develop vào feature", "vn_joke": "clean - sạch bong sáng bóng, chưa merge develop vào bao giờ", "vn_toxic": "clean - nhánh sạch, đéo merge bậy bạ vào", "en_pro": "clean - clean branch, develop never merged into feature"
    },
    "opt_hist_merged": {
        "vn_pro": "merged - đã từng merge develop vào feature / history không sạch", "vn_joke": "merged - đã từng lỡ tay merge develop vào / nát bét", "vn_toxic": "merged - history nát vcl do merge bậy bạ", "en_pro": "merged - develop was merged into feature / unclean history"
    },
    "no_commits_to_squash": {
        "vn_pro": "Không có commit nào để squash. Quay về menu chính.", "vn_joke": "Chưa code gì mà đòi squash ba? Về menu nha.", "vn_toxic": "Đéo có commit nào mà cũng đòi squash. Về menu!", "en_pro": "No commits to squash. Returning to main menu."
    },
    "create_backup_q": {
        "vn_pro": "Có tạo backup branch trước khi rewrite history không?", "vn_joke": "Làm cái branch backup cất tủ cho an tâm không sếp?", "vn_toxic": "Có backup lại nhánh không? Lỡ nát còn có cái mà bú.", "en_pro": "Create a backup branch before rewriting history?"
    },
    "created_backup": {
        "vn_pro": "Đã tạo backup branch: ", "vn_joke": "Đã sao lưu an toàn ra nhánh: ", "vn_toxic": "Tạo backup xong cmnr ở nhánh: ", "en_pro": "Created backup branch: "
    },
    "final_commit_msg": {
        "vn_pro": "Final commit message", "vn_joke": "Chốt câu commit cuối cùng xem nào", "vn_toxic": "Ghi cái commit message vào (ghi cho đàng hoàng)", "en_pro": "Final commit message"
    },
    "auto_push_q": {
        "vn_pro": "Sau khi rebase xong có push luôn bằng --force-with-lease không?", "vn_joke": "Làm xong auto push đè lên remote luôn không sếp (an toàn)?", "vn_toxic": "Rebase xong có push force đè luôn remote không?", "en_pro": "Auto push using --force-with-lease after successful rebase?"
    },
    "continue_steps_q": {
        "vn_pro": "Tiếp tục thực hiện các bước trên?", "vn_joke": "Chốt đơn, bắt đầu chạy dây chuyền nha sếp?", "vn_toxic": "Duyệt chưa? Để tao bắt đầu chạy?", "en_pro": "Continue executing the above steps?"
    },
    "flow_done": {
        "vn_pro": "Hoàn tất. Feature branch đã được squash và rebase xong.", "vn_joke": "Xong cmnr sếp ơi. Nhánh sạch bóng, rebase mượt mà.", "vn_toxic": "Ngon lành cành đào. Squash và rebase xong cmnr.", "en_pro": "Done. Feature branch has been successfully squashed and rebased."
    },
    "goodbye": {
        "vn_pro": "Tạm biệt.", "vn_joke": "Bái bai sếp, múa code vui vẻ.", "vn_toxic": "Cút đi code tiếp đi.", "en_pro": "Goodbye."
    },
    
    # Error Dictionary
    "err_network": {
        "vn_pro": "Lỗi mạng hoặc xác thực. Vui lòng kiểm tra lại kết nối internet, VPN hoặc quyền truy cập repo.",
        "vn_joke": "Rớt mạng rồi sếp ơi, hoặc repo private mà sếp quên xin quyền kìa.",
        "vn_toxic": "Mù hay sao đéo thấy lỗi mạng? Check lại Wifi, VPN với quyền access đi cái!",
        "en_pro": "Network or authentication error. Please check your internet connection, VPN, or repo permissions."
    },
    "err_conflict": {
        "vn_pro": "Xung đột (conflict) mã nguồn. Git không thể tự gộp, bạn cần mở IDE để giải quyết thủ công.",
        "vn_joke": "Choảng nhau rồi! Code sếp với code thiên hạ đang uýnh nhau, mở IDE lên can đi.",
        "vn_toxic": "Conflict banh xác cmnr! Bấm vào IDE mà gỡ tay đi chứ tool đéo cứu được vụ này.",
        "en_pro": "Merge conflict detected. Git cannot automatically merge, manual resolution required."
    },
    "err_overwrite": {
        "vn_pro": "Lệnh bị chặn do bạn có thay đổi chưa lưu có thể bị ghi đè. Hãy giấu code (stash) hoặc commit trước.",
        "vn_joke": "Tính ghi đè mất code đang viết dở à? May mà Git nó cản. Giấu code (stash) đi đã.",
        "vn_toxic": "Ngu à? Chuyển nhánh/Rebase lúc file đang sửa dở nó đè mất code thì khóc. Stash mẹ nó lại!",
        "en_pro": "Operation aborted to prevent overwriting uncommitted changes. Please stash or commit first."
    },
    "err_push_rejected": {
        "vn_pro": "Push bị từ chối. Thường do nhánh trên remote có code mới hơn local, hoặc do rule bảo vệ nhánh.",
        "vn_joke": "Bị server sút ra rồi! Chắc ai đó đã push code mới hơn, sếp phải pull về trước nha.",
        "vn_toxic": "Server nó đéo cho push! Một là do code mày cũ hơn remote, hai là nhánh bị khóa cmnr. Tự check đi!",
        "en_pro": "Push rejected. Usually because the remote branch is ahead of your local branch, or due to branch protection rules."
    },
    "err_unknown": {
        "vn_pro": "Gặp lỗi Git không xác định. Vui lòng đọc kỹ thông báo lỗi màu đỏ ở trên.",
        "vn_joke": "Lỗi này lạ quá tool chưa được học. Sếp chịu khó tự ngâm cứu log tiếng Anh bên trên nha.",
        "vn_toxic": "Lỗi củ lìn gì đây? Tao chịu, tự căng mắt ra mà đọc cái dòng đỏ lòm bên trên đi!",
        "en_pro": "An unknown Git error occurred. Please read the standard error message above carefully."
    },

    # Checkout features
    "ask_checkout_now": {
        "vn_pro": "Bạn có muốn checkout sang nhánh khác ngay bây giờ không?",
        "vn_joke": "Muốn bay qua nhánh khác luôn không sếp?",
        "vn_toxic": "Có nhảy sang nhánh khác luôn không hay đứng đây rặn?",
        "en_pro": "Do you want to checkout to another branch now?"
    },
    "list_branches": {
        "vn_pro": "Danh sách các nhánh (local & remote):",
        "vn_joke": "Mấy nhánh hiện có (cả trên server) nè sếp:",
        "vn_toxic": "Nhìn cmn list nhánh (local + remote) này đi:",
        "en_pro": "Available branches (local & remote):"
    },
    "choose_branch_checkout": {
        "vn_pro": "Nhập số, tên, hoặc TỪ KHÓA để lọc nhánh (nhập 'f' để tải nhánh mới, Enter để hủy):",
        "vn_joke": "Bấm số, tên, hoặc keyword (gõ 'f' để kéo nhánh mới, Enter quay xe):",
        "vn_toxic": "Gõ số, tên, hoặc keyword (gõ 'f' fetch ngay, Enter thì cút):",
        "en_pro": "Enter number, name, or keyword (type 'f' to fetch remote, Enter to cancel):"
    },
    "branch_not_found": {
        "vn_pro": "Không tìm thấy nhánh hợp lệ với từ khóa này.",
        "vn_joke": "Tìm hụt rồi, không có nhánh nào chữ này đâu sếp.",
        "vn_toxic": "Đéo có nhánh nào khớp cái từ khóa lố lăng này! Lác à?",
        "en_pro": "No matching branches found."
    },
    "checkout_success": {
        "vn_pro": "Đã chuyển sang nhánh '{branch}'.",
        "vn_joke": "Đã hạ cánh an toàn xuống '{branch}'.",
        "vn_toxic": "Đã nhảy sang '{branch}' cmnr.",
        "en_pro": "Checked out to '{branch}'."
    },
    "checkout_fail": {
        "vn_pro": "Lỗi khi checkout. Có thể do có file thay đổi chưa commit gây xung đột.",
        "vn_joke": "Kẹt rồi sếp, dọn đống code đang sửa dở đi đã rồi mới bay được.",
        "vn_toxic": "Đéo sang được! Dọn cái đống file đang gõ dở đi đã!",
        "en_pro": "Checkout failed. You might have local changes that would be overwritten."
    },
    "fetching_remote": {
        "vn_pro": "Đang tải dữ liệu nhánh mới nhất từ server...",
        "vn_joke": "Đang gọi điện lên server kéo nhánh mới về nè sếp...",
        "vn_toxic": "Đang kéo mẹ đống nhánh rác trên server về, đợi xíu...",
        "en_pro": "Fetching latest branches from remote..."
    },
    "branch_search_found": {
        "vn_pro": "Tìm thấy {count} nhánh khớp với '{kw}'. Vui lòng chọn lại:",
        "vn_joke": "Lọc ra được {count} mống có chữ '{kw}' nè sếp, chọn số đi:",
        "vn_toxic": "Tìm được {count} cái nhánh rác chứa '{kw}'. Bấm số chọn lẹ:",
        "en_pro": "Found {count} branches matching '{kw}'. Please select:"
    },
    "branch_search_single": {
        "vn_pro": "Tìm thấy 1 nhánh duy nhất khớp từ khóa, tự động chọn: {target}",
        "vn_joke": "Có đúng 1 mống khớp, auto nhảy luôn nha: {target}",
        "vn_toxic": "Có mỗi 1 nhánh khớp, nhắm mắt quất luôn: {target}",
        "en_pro": "Found exactly 1 matching branch, auto-selecting: {target}"
    },
    "branch_count_few": {
        "vn_pro": "Repo rất gọn gàng với {count} nhánh.",
        "vn_joke": "Có lèo tèo {count} nhánh. Dăm ba cái nhánh này tính ra còn ít hơn số logic phải vặn vẹo lúc dùng Pyspark bóc tách ba cái file Excel gộp dòng bữa nọ nữa.",
        "vn_toxic": "Đéo mẹ cả repo có đúng {count} cái nhánh rách? Có làm việc không hay bú fame?",
        "en_pro": "Repository is very clean with only {count} branches."
    },
    "branch_count_many": {
        "vn_pro": "Lưu ý: Repo hiện có {count} nhánh. Nên cân nhắc dọn dẹp các nhánh đã cũ.",
        "vn_joke": "Ối dồi ôi {count} nhánh! Đẻ nhánh đẻ rễ lắm thế này, lúc tìm khéo còn lú hơn cả monitor mấy trăm cái Databricks jobs đang chạy trên production sếp ạ!",
        "vn_toxic": "Tận {count} cái nhánh rác! Mày tính đẻ nhánh ra để ăn lẩu à? Vô dọn mẹ bớt đi nhìn ngứa cả mắt!",
        "en_pro": "Notice: Repository has {count} branches. Consider cleaning up stale branches."
    },
    
    # Easter Eggs Dictionary
    "ee_night_owl": {
        "vn_pro": "Ghi chú: Đã khuya, hãy chú ý giữ gìn sức khỏe nhé.",
        "vn_joke": "Trời đánh tránh giờ ngủ. Cú đêm cày code cẩn thận rụng tóc nha sếp!",
        "vn_toxic": "Đêm hôm đéo đi ngủ đi ngồi múa Git? Tính bán mạng cho tư bản à?",
        "en_pro": "Notice: It's late night. Please take some rest."
    },
    "ee_spam_commit": {
        "vn_pro": "Ghi chú: Số lượng commit khá lớn ({count} commits).",
        "vn_joke": "Mẹ ơi {count} commits! Sếp gõ phím dạo hay sao mà rác kinh thế?",
        "vn_toxic": "Tận {count} commits? Mày commit từng dòng code một hay gì mà rác vcl thế?",
        "en_pro": "Notice: Detected a large number of commits ({count})."
    },
    "ee_massive_stash": {
        "vn_pro": "Đã phát hiện lượng lớn file thay đổi ({count} files).",
        "vn_joke": "Ối giời thay đổi tận {count} files! Sếp đập đi xây lại cả cái project à?",
        "vn_toxic": "Sửa tận {count} files đéo chịu commit? Thích ôm bom cảm tử đúng không?",
        "en_pro": "Detected a massive amount of uncommitted changes ({count} files)."
    }
}

def _t(key: str, **kwargs) -> str:
    msg = LANGUAGES.get(key, {}).get(CURRENT_LANG, key)
    if kwargs:
        msg = msg.format(**kwargs)
    if EMOJI_MODE and key in EMOJI_MAP:
        msg = f"{msg} {EMOJI_MAP[key]}"
    return msg

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
# Git Error Decoder (Tự động giải mã lỗi)
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
# Prompt helpers
# ============================================================
def ask_yes_no(question_key: str, default: bool = True, **kwargs) -> bool:
    suffix = THEME.ok("[Y/n]") if default else THEME.warn("[y/N]")
    while True:
        answer = input(f"{THEME.info('?')} {_t(question_key, **kwargs)} {suffix}: ").strip().lower()
        if not answer: return default
        if answer in ("y", "yes"): return True
        if answer in ("n", "no"): return False
        print(THEME.warn(_t("invalid_yn")))

def ask_non_empty(question_key: str, default: Optional[str] = None) -> str:
    while True:
        if default is None:
            answer = input(f"{THEME.info('?')} {_t(question_key)}: ").strip()
        else:
            answer = input(f"{THEME.info('?')} {_t(question_key)} {THEME.dim('[' + default + ']')}: ").strip()
            if not answer: return default
        if answer: return answer
        print(THEME.warn(_t("not_empty")))

def ask_choice(question_key: str, option_keys: List[str], default_index: int = 0) -> str:
    print(f"\n{THEME.info('?')} {_t(question_key)}")
    for i, opt_key in enumerate(option_keys, start=1):
        marker = f" {THEME.ok(_t('default_marker'))}" if i - 1 == default_index else ""
        
        display = _t(opt_key)
        if opt_key == "m_emoji":
            state = "ON 🟢" if EMOJI_MODE else "OFF 🔴"
            display = f"{display} [{state}]"
            
        print(f"  {THEME.choice(str(i) + '.')} {display}{marker}")
        
    while True:
        answer = input(f"{THEME.info('?')} {_t('choose_num')} ").strip()
        if not answer: return option_keys[default_index]
        if answer.isdigit():
            idx = int(answer) - 1
            if 0 <= idx < len(option_keys): return option_keys[idx]
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
        if not os.path.isdir(repo_path):
            print(THEME.err(_t("repo_not_exist")))
            continue
        if not is_git_repo(repo_path):
            print(THEME.err(_t("not_git_repo")))
            continue
        return repo_path

def resolve_repo_dir() -> str:
    cwd = os.getcwd()
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

    choice = ask_choice("what_do_changes", ["opt_stash", "opt_no_stash", "opt_cancel"], default_index=0)

    if choice == "opt_stash":
        # Easter Egg: Thánh Ôm Bom
        if len(changes) >= 30:
            print(f"\n{THEME.warn(_t('ee_massive_stash', count=len(changes)))}")
            
        run('git stash push -u -m "git-feature-flow auto-stash"', cwd=repo_dir)
        print(THEME.ok(_t("stashed_ok")))
        return True

    if choice == "opt_no_stash":
        print(THEME.warn(_t("warn_no_stash")))
        if not ask_yes_no("sure_no_stash", False):
            print(THEME.warn(_t("canceled_return")))
            return None
        return False

    print(THEME.warn(_t("canceled_return")))
    return None

def maybe_restore_auto_stash(repo_dir: str, auto_stashed: bool) -> None:
    if not auto_stashed: return
    restore = ask_yes_no("restore_stash_q", True)
    if not restore:
        print(THEME.warn(_t("kept_stash")))
        return
    run("git stash pop", cwd=repo_dir)
    print(THEME.ok(_t("restored_stash")))

# ============================================================
# Git branch logic & Advanced Checkout Flow
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
    # Xử lý triệt để dấu nháy đơn do Windows CMD tự chèn vào
    return b.strip().strip("'").strip('"')

def highlight_b(b_name: str, kw: str, is_loc: bool) -> str:
    # Logic nhả màu an toàn với nền Vàng nổi bật
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
    # Lấy danh sách local
    local_branches_str = git_output("git branch --format=%(refname:short)", cwd=repo_dir)
    local_branches = [clean_branch_name(b) for b in local_branches_str.splitlines() if b.strip()]
    
    # Lấy danh sách remote 
    remote_branches_str = git_output("git branch -r --format=%(refname:short)", cwd=repo_dir)
    remote_branches_raw = [clean_branch_name(b) for b in remote_branches_str.splitlines() if b.strip()]
    
    # Lọc bỏ origin/HEAD và cái tên remote rác
    remote_branches = [b for b in remote_branches_raw if "origin/HEAD" not in b and b != "origin"]
    
    # Lọc bỏ nhánh remote đã có tracking local
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
    
    # Phân tích số lượng nhánh để chèn bình luận vui nhộn
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
        
        if not ans: 
            return False
            
        if ans.lower() == 'f':
            alert_msg = THEME.info(_t("fetching_remote"))
            print(f"\n{alert_msg}")
            run("git fetch origin --prune", cwd=repo_dir)
            return handle_checkout(repo_dir)
            
        target = None
        
        # Check nếu là số index
        if ans.isdigit():
            idx = int(ans) - 1
            if 0 <= idx < len(current_list):
                target = current_list[idx]
        # Check nếu nhập trúng tên
        elif ans in current_list:
            target = ans
        # Search keyword
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
                
        # Thực hiện checkout
        if target:
            try:
                if target.startswith("origin/"):
                    clean_name = target.replace("origin/", "", 1)
                    run(f"git checkout -t {shlex.quote(target)}", cwd=repo_dir)
                    print(THEME.ok(_t("checkout_success", branch=clean_name)))
                else:
                    run(f"git checkout {shlex.quote(target)}", cwd=repo_dir)
                    print(THEME.ok(_t("checkout_success", branch=target)))
                return True
            except RuntimeError:
                print(THEME.err(_t("checkout_fail")))
                return False

# ============================================================
# Rebase state helpers
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
        conflict_files = get_conflicted_files(repo_dir)
        lines = [
            _t("rebase_paused_1"), _t("rebase_paused_2"), _t("rebase_paused_3"),
            _t("rebase_paused_4", count=len(conflict_files)),
        ]
        print_box("Rebase Recovery", lines)

        choice = ask_choice("choose_action", ["opt_show_status", "opt_show_conflict", "opt_continue", "opt_abort", "opt_return"], 0)

        if choice == "opt_show_status":
            show_git_status_box(repo_dir)
            continue
        if choice == "opt_show_conflict":
            show_conflicted_files_box(repo_dir)
            continue
        if choice == "opt_continue":
            try:
                run("git rebase --continue", cwd=repo_dir)
            except RuntimeError:
                if is_rebase_in_progress(repo_dir):
                    print(THEME.warn(_t("rebase_not_done")))
                    continue
                print(THEME.err("Cannot continue rebase."))
                continue
            if is_rebase_in_progress(repo_dir):
                print(THEME.warn("Rebase still running, more steps might be needed."))
                continue
            print(THEME.ok(_t("rebase_success")))
            return "completed"

        if choice == "opt_abort":
            if not ask_yes_no("Are you sure you want to abort?", False): continue
            try:
                run("git rebase --abort", cwd=repo_dir)
                print(THEME.warn("Aborted rebase."))
                return "aborted"
            except RuntimeError:
                print(THEME.err("Cannot abort rebase."))
                continue

        if choice == "opt_return":
            print(THEME.warn("Keeping current rebase state. Returning to menu."))
            return "menu"

def create_backup(repo_dir: str, branch: str) -> str:
    ts = datetime.now().strftime("%Y%m%d-%H%M%S")
    backup_branch = f"backup/{branch.replace('/', '-')}-{ts}"
    run(f"git branch {shlex.quote(backup_branch)}", cwd=repo_dir)
    return backup_branch

def get_effective_base_point(repo_dir: str, base_branch: str, history_type: str) -> Optional[str]:
    cmd = f"git merge-base HEAD origin/{base_branch}" if history_type == "clean" else f"git merge-base --fork-point origin/{base_branch} HEAD"
    base_point = git_output(cmd, cwd=repo_dir, check=False)
    if not base_point:
        print(THEME.err("Cannot find base point."))
        print(THEME.warn("Check git log if history is complex."))
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
# UI blocks
# ============================================================
def show_startup(repo_dir: str) -> None:
    lines = [
        f"{THEME.key('Platform')} : {os.name}",
        f"{THEME.key('Repo')}     : {repo_dir}",
        f"{THEME.key('Rebase')}   : {'in progress' if is_rebase_in_progress(repo_dir) else 'idle'}",
    ]
    print_box("Feature Branch Squash + Rebase Assistant", lines)

def show_summary(repo_dir: str, base_branch: str, detected_type: str, detected_reason: str) -> None:
    lines = [
        f"{THEME.key('Current branch')} : {THEME.branch(current_branch(repo_dir))}",
        f"{THEME.key('Base branch')}    : {THEME.branch(base_branch)}",
        f"{THEME.key('Detected type')}  : {THEME.choice(_t(f'opt_hist_{detected_type}'))}",
        f"{THEME.key('Detail')}         : {detected_reason}",
    ]
    print_box("Git Summary", lines)

def show_scope(base_point: str, commit_total: int, commits: List[str], truncated: bool) -> None:
    lines = [
        f"{THEME.key('Base point')}       : {THEME.commit(base_point)}",
        f"{THEME.key('Commits to squash')}: {THEME.count(str(commit_total))}",
    ]
    print_box("Base Point & Scope", lines)
    
    # Easter Egg: Thánh Xả Rác
    if commit_total >= 20:
        print(f"\n{THEME.warn(_t('ee_spam_commit', count=commit_total))}")
        
    preview_lines = [format_commit_line(c) for c in commits] if commits else [THEME.dim("(No commits in range)")]
    if truncated: preview_lines += [THEME.dim("..."), THEME.dim("(Truncated)")]
    print_box("Preview Commits", preview_lines)

def show_action_plan(base_point: str, final_message: str, base_branch: str, auto_push: bool) -> None:
    lines = [
        THEME.cmd(f"1. git reset --soft {base_point}"),
        THEME.cmd(f'2. git commit -m "{final_message}"'),
        THEME.cmd(f"3. git rebase origin/{base_branch}"),
    ]
    if auto_push: lines.append(THEME.cmd("4. git push --force-with-lease"))
    print_box("Action Plan", lines)

# ============================================================
# Core flow
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

    base_branch = ask_non_empty("base_branch_name", "develop")
    
    if not ensure_not_on_base(base_branch, branch):
        if ask_yes_no("ask_checkout_now", True):
            handle_checkout(repo_dir)
        maybe_restore_auto_stash(repo_dir, auto_stashed)
        return

    if ask_yes_no("fetch_origin_q", True): run("git fetch origin", cwd=repo_dir)

    detected_type, detected_reason = detect_history_type(repo_dir, base_branch)
    show_summary(repo_dir, base_branch, detected_type, detected_reason)

    if ask_yes_no("use_detected_history_q", True, type=detected_type):
        history_type = detected_type
    else:
        history_type_key = ask_choice("choose_history_type", ["opt_hist_clean", "opt_hist_merged", "opt_cancel"], default_index=0 if detected_type == "clean" else 1)
        if history_type_key == "opt_cancel":
            print(THEME.warn(_t("canceled_return")))
            maybe_restore_auto_stash(repo_dir, auto_stashed)
            return
        history_type = "clean" if history_type_key == "opt_hist_clean" else "merged"

    base_point = get_effective_base_point(repo_dir, base_branch, history_type)
    if not base_point:
        maybe_restore_auto_stash(repo_dir, auto_stashed)
        return

    commit_total = commit_count_since(repo_dir, base_point)
    commit_preview = get_commit_preview(repo_dir, base_point, limit=50)
    show_scope(base_point, commit_total, commit_preview, commit_total > len(commit_preview))

    if commit_total == 0:
        print(THEME.warn(_t("no_commits_to_squash")))
        maybe_restore_auto_stash(repo_dir, auto_stashed)
        return

    if ask_yes_no("create_backup_q", True):
        backup_branch = create_backup(repo_dir, branch)
        print(f"{THEME.ok(_t('created_backup'))} {THEME.branch(backup_branch)}")

    final_message = ask_non_empty("final_commit_msg", "feat: update feature")
    auto_push = ask_yes_no("auto_push_q", False)

    show_action_plan(base_point, final_message, base_branch, auto_push)

    if not ask_yes_no("continue_steps_q", True):
        print(THEME.warn(_t("canceled_return")))
        maybe_restore_auto_stash(repo_dir, auto_stashed)
        return

    run(f"git reset --soft {base_point}", cwd=repo_dir)
    run(f"git commit -m {shlex.quote(final_message)}", cwd=repo_dir)

    try:
        run(f"git rebase origin/{base_branch}", cwd=repo_dir)
    except RuntimeError:
        if is_rebase_in_progress(repo_dir):
            print(THEME.warn("Rebase stopped. Switching to recovery mode."))
            result = handle_rebase_recovery(repo_dir)
            if result == "completed":
                if auto_push: run("git push --force-with-lease", cwd=repo_dir)
                maybe_restore_auto_stash(repo_dir, auto_stashed)
                print(f"\n{THEME.ok(_t('flow_done'))}")
                return
            if result in ("aborted", "menu"):
                maybe_restore_auto_stash(repo_dir, auto_stashed)
                return
        maybe_restore_auto_stash(repo_dir, auto_stashed)
        raise

    if auto_push: run("git push --force-with-lease", cwd=repo_dir)
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

    # Easter Egg: Cú đêm (Chỉ báo 1 lần lúc mới bật tool)
    hour = datetime.now().hour
    if hour >= 23 or hour <= 4:
        print(f"\n{THEME.warn(_t('ee_night_owl'))}")

    while True:
        # Không clear screen ngay ở đây để thông báo kết quả thao tác cũ vẫn được hiển thị!
        show_startup(repo_dir)

        if is_rebase_in_progress(repo_dir):
            print(THEME.warn("Repo in dirty rebase state."))
            choice = ask_choice("choose_action", ["m_recover", "m_checkout", "m_change", "m_refresh", "m_lang", "m_emoji", "m_exit"], 0)
        else:
            choice = ask_choice("main_menu", ["m_start", "m_checkout", "m_change", "m_refresh", "m_lang", "m_emoji", "m_exit"], 0)

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
            show_startup(repo_dir)
            try: run_feature_flow(repo_dir)
            except RuntimeError as e:
                print(THEME.warn("Operation stopped / Luồng đã dừng."))
            except Exception:
                print(THEME.err("Unexpected error in flow:"))
                traceback.print_exc()
            continue

        if choice == "m_checkout":
            handle_checkout(repo_dir)
            continue

        if choice == "m_change":
            clear_screen()
            show_startup(repo_dir)
            repo_dir = ask_repo_path()
            clear_screen() # Xóa cho sạch rồi quay lại menu
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
            clear_screen() # Nhảy màn cho mượt
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