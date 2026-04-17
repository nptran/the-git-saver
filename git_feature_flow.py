#!/usr/bin/env python3
import os
import re
import shlex
import subprocess
import sys
import traceback
import random
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Tuple, Any, Union

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
    "rebase_ext_success": "🤖", "rebase_skip_q": "⏭️",
    "on_base_branch": "🏠", "checkout_feature_first": "🔀", "base_branch_name": "🌳",
    "fetch_origin_q": "☁️", "merged_reason": "🍝", "clean_reason": "🧼",
    "use_detected_history_q": "🤖", "opt_hist_clean": "✨", "opt_hist_merged": "🌪️",
    "no_commits_to_squash": "🫙", "create_backup_q": "🛡️", "created_backup": "💾",
    "final_commit_msg": "📝", "auto_push_q": "🚀", "continue_steps_q": "🏁",
    "flow_done": "🏆", "goodbye": "👋😏", "choose_history_type": "🗂️",
    "dash_title": "📊",
    
    # Error Emojis
    "err_network": "🔌", "err_conflict": "⚔️💥", "err_overwrite": "🛑📝", 
    "err_push_rejected": "⛔", "err_unknown": "👽",

    # Checkout flow Emojis
    "ask_checkout_now": "✈️", "list_branches": "🌿", "checkout_success": "✅", "checkout_fail": "💥",
    "fetching_remote": "☁️🔄", "branch_search_found": "🎯", "branch_search_single": "✨",
    "branch_count_few": "🌱", "branch_count_many": "🌳💀",

    # Verify Emojis
    "verify_title": "🔍", "verify_ahead_ok": "✅", "verify_ahead_fail": "❌",
    "verify_patch_ok": "🛡️", "verify_patch_diff": "⚠️", "verify_no_ref": "🚨",

    # Smart Git
    "smart_git_detect": "🧠", "smart_git_confirm": "🕹️", "smart_git_done": "✅", "smart_git_cancel": "🔙",
    
    # Predict Conflict
    "predict_conflict_warn": "🚨", "predict_conflict_clean": "🛣️",
    "dash_predict_clean": "✅", "dash_predict_conflict": "💥",
    
    # Action Status
    "abort_success": "✅", "continue_fail": "💥", "flow_stopped": "🛑", "flow_error": "👽"
}

LANGUAGES = {
    "press_exit": {
        "vn_pro": "\nNhấn Enter để thoát...", 
        "vn_joke": ["\nNhấn Enter để sủi bọt...", "\nĐập Enter để chìm vào lãng quên...", "\nBấm Enter để cút... à nhầm, để thoát..."], 
        "vn_toxic": ["\nĐập Enter để cút nhanh...", "\nBấm cmn Enter đi còn đợi gì?", "\nCút lẹ, ấn Enter!"], 
        "en_pro": "\nPress Enter to exit..."
    },
    "press_continue": {
        "vn_pro": "Nhấn Enter để tiếp tục...", 
        "vn_joke": ["Gõ Enter để đi tiếp nha...", "Enter cái cho đời nó trôi sếp ơi..."], 
        "vn_toxic": ["Đập Enter để thử lại!", "Bấm mẹ Enter đi lề mề thế?"], 
        "en_pro": "Press Enter to continue..."
    },
    "no_git_err": {
        "vn_pro": "Không tìm thấy Git trong PATH.", "vn_joke": "Sếp ơi, máy sếp chưa cài Git à? Kì cục vậy.", "vn_toxic": "Đéo thấy Git đâu trong PATH! Mày dev bằng niềm tin à?", "en_pro": "Git not found in PATH."
    },
    "no_git_warn": {
        "vn_pro": "Hãy cài Git for Windows và đảm bảo lệnh 'git' chạy được trong terminal.", "vn_joke": "Lên Google tải Git về cài dùm tui nha sếp.", "vn_toxic": "Vác mặt đi tải Git for Windows cài vào ngay. Đếch hiểu kiểu gì.", "en_pro": "Please install Git and ensure 'git' command works in your terminal."
    },
    "invalid_yn": {
        "vn_pro": "Vui lòng nhập y hoặc n.", 
        "vn_joke": ["Gõ y hoặc n thôi ní ơi, đừng làm khó nhau.", "Sếp gõ gì trớt quớt vậy? y hoặc n thôi.", "Nhập sai gòi, y hay n nè?"], 
        "vn_toxic": ["Mù à? Gõ y hoặc n thôi!", "Bấm phím liệt à? Có y với n cũng gõ đéo xong.", "Gõ chữ y hoặc n, đéo biết chữ à?"], 
        "en_pro": "Please enter y or n."
    },
    "not_empty": {
        "vn_pro": "Không được để trống.", 
        "vn_joke": ["Nhập gì đó vào đi sếp, để trống sao chạy.", "Đừng có Enter suông thế chứ.", "Gõ phím đi sếp, đừng lười."], 
        "vn_toxic": ["Bỏ trống thế đéo nào được? Gõ vào!", "Mù à? Kêu nhập mà đéo nhập?", "Gõ cái gì vào giùm tao cái!"], 
        "en_pro": "Cannot be empty."
    },
    "choose_num": {
        "vn_pro": "Chọn số:", "vn_joke": "Bấm số đi sếp:", "vn_toxic": "Bấm cmn số vào:", "en_pro": "Choose number:"
    },
    "invalid_choice": {
        "vn_pro": "Lựa chọn không hợp lệ.", 
        "vn_joke": ["Bấm sai rồi kìa, chọn lại đi.", "Ui da chọc mù mắt tui rồi, chọn đúng số đi má.", "Lựa lộn rồi sếp ơi."], 
        "vn_toxic": ["Lác à? Chọn sai bét, chọn lại!", "Có mấy cái số cũng chọn đéo xong?", "Bấm linh tinh cái đéo gì đấy?"], 
        "en_pro": "Invalid choice."
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

    # Dashboard & Flow controls
    "dash_title": {"vn_pro": "BẢNG ĐIỀU KHIỂN REBASE", "vn_joke": "BẢNG ĐIỀU KHIỂN XỊN SÒ", "vn_toxic": "MENU CHÍNH", "en_pro": "REBASE WIZARD DASHBOARD"},
    "dash_base_branch": {"vn_pro": "1. Nhánh gốc", "vn_joke": "1. Nhánh cội nguồn", "vn_toxic": "1. Nhánh làm gốc", "en_pro": "1. Base branch"},
    "dash_fetch": {"vn_pro": "2. Tải mới (Fetch)", "vn_joke": "2. Kéo code mới", "vn_toxic": "2. Fetch origin", "en_pro": "2. Fetch origin"},
    "dash_history": {"vn_pro": "3. Loại lịch sử", "vn_joke": "3. Độ nát nhánh", "vn_toxic": "3. Hệ lịch sử", "en_pro": "3. History type"},
    "dash_backup": {"vn_pro": "4. Tạo Backup", "vn_joke": "4. Mua bảo hiểm", "vn_toxic": "4. Backup nhánh", "en_pro": "4. Backup branch"},
    "dash_msg": {"vn_pro": "5. Lời nhắn (Msg)", "vn_joke": "5. Lời trăng trối", "vn_toxic": "5. Commit rác", "en_pro": "5. Commit Msg"},
    "dash_push": {"vn_pro": "6. Auto Push", "vn_joke": "6. Push tự động", "vn_toxic": "6. Force push", "en_pro": "6. Auto Push"},
    "opt_back": {
        "vn_pro": "Quay lại bước trước", "vn_joke": "De xe lại (Quay về)", "vn_toxic": "Ấn nhầm, cho tao quay lại", "en_pro": "Go back to previous step"
    },
    "type_back": {
        "vn_pro": " (< Quay lại)", "vn_joke": " (gõ '<' để de xe)", "vn_toxic": " (gõ '<' để lùi bước)", "en_pro": " (< Back)"
    },

    # Predict Conflict I18N
    "predict_conflict_warn": {
        "vn_pro": "CẢNH BÁO: Dự đoán sẽ xảy ra CONFLICT khi rebase vào {base}. Bạn có thể sẽ phải giải quyết thủ công.",
        "vn_joke": ["Báo động đỏ! Tool ngửi thấy mùi conflict nồng nặc với nhánh {base}.", "Tới công chuyện rồi sếp! Check thử thấy conflict chà bá với {base}."],
        "vn_toxic": ["ĐM CẢNH BÁO! Code mày đang đá nhau chan chát với {base}. Chuẩn bị dọn rác conflict đi!", "Toang cmnr! Dự đoán dính conflict đỏ lòm với {base}. Xem kĩ đi!"],
        "en_pro": "WARNING: Predicted conflicts when rebasing onto {base}. Manual resolution will be required."
    },
    "predict_conflict_clean": {
        "vn_pro": "Tin tốt: Không dự đoán có conflict với nhánh {base}. Đường đã thông hè đã thoáng.",
        "vn_joke": ["Ngon lành cành đào, radar không quét thấy cục conflict nào với {base} sếp ơi.", "Đường thông hè thoáng, đéo thấy conflict nào với {base} nha sếp."],
        "vn_toxic": ["Check rồi, đéo có conflict với {base}. Chắc do ăn ở tốt.", "May cho mày là đéo dính conflict nào với nhánh {base} đấy."],
        "en_pro": "Good news: No potential conflicts predicted with {base}. Clear path ahead."
    },
    "dash_predict": {
        "vn_pro": "Dự báo conflict", "vn_joke": "Bói conflict", "vn_toxic": "Soi conflict", "en_pro": "Conflict predict"
    },
    "dash_predict_clean": {
        "vn_pro": "Sạch sẽ", "vn_joke": "Ngon lành", "vn_toxic": "Đéo có", "en_pro": "Clean"
    },
    "dash_predict_conflict": {
        "vn_pro": "Có xung đột ({count} file)", "vn_joke": "Toang ({count} file choảng nhau)", "vn_toxic": "Nát cmnr ({count} file)", "en_pro": "Conflict ({count} files)"
    },

    # Smart Git Feature
    "smart_git_detect": {
        "vn_pro": "Chế độ Smart Git: Nhận diện lệnh hợp lệ.", 
        "vn_joke": "Sếp múa raw command à? Kích hoạt Smart Git!", 
        "vn_toxic": "Gõ tay lệnh Git à? Thích thể hiện thì tao chiều!", 
        "en_pro": "Smart Git Mode: Detected valid command."
    },
    "smart_git_confirm": {
        "vn_pro": "Bạn có chắc muốn chạy lệnh này ngay bây giờ không?", 
        "vn_joke": "Chắc kèo là quất lệnh này luôn nha sếp?", 
        "vn_toxic": "Chốt chạy lệnh này chưa? Nát repo đéo đền đâu!", 
        "en_pro": "Are you sure you want to execute this command now?"
    },
    "smart_git_done": {
        "vn_pro": "Thực thi hoàn tất. Trở lại luồng công việc hiện tại.", 
        "vn_joke": "Quẩy Git xong rồi, quay lại việc chính nha sếp.", 
        "vn_toxic": "Chạy xong cmnr, về lại chỗ cũ mà làm việc tiếp đi.", 
        "en_pro": "Execution completed. Returning to current flow."
    },
    "smart_git_cancel": {
        "vn_pro": "Đã hủy chạy lệnh Git. Trở lại bình thường.", 
        "vn_joke": "Quay xe! Bỏ lệnh Git, trả lại màn hình cho sếp.", 
        "vn_toxic": "Hủy cmnr. Gõ cho cố rồi sợ à?", 
        "en_pro": "Git command canceled. Returning to normal."
    },
    "git_cmd_status": {
        "vn_pro": "Xem trạng thái các file (đã sửa, đã add) và nhánh hiện tại.",
        "vn_joke": "Coi thử code đang nát tới đâu, có file nào đỏ lòm không.",
        "vn_toxic": "Xem mẹ cái list file rác mày vừa gõ bậy bạ vào chưa commit.",
        "en_pro": "Show the working tree status."
    },
    "git_cmd_log": {
        "vn_pro": "Xem lịch sử các commit đã thực hiện.",
        "vn_joke": "Lật lại án tích xem ai là người gây ra đống bug này.",
        "vn_toxic": "Xem gia phả commit xem thằng l` nào code đoạn này.",
        "en_pro": "Show commit logs."
    },
    "git_cmd_branch": {
        "vn_pro": "Xem, tạo, hoặc xóa các nhánh (branches).",
        "vn_joke": "Kiểm kê xem repo đang đẻ ra bao nhiêu cái nhánh rồi.",
        "vn_toxic": "Xem cái list nhánh rác rưởi mà team mày tạo ra.",
        "en_pro": "List, create, or delete branches."
    },
    "git_cmd_checkout": {
        "vn_pro": "Đổi nhánh hoặc khôi phục file về trạng thái cũ.",
        "vn_joke": "Dịch chuyển tức thời sang nhánh khác múa code.",
        "vn_toxic": "Cút sang nhánh khác để code.",
        "en_pro": "Switch branches or restore working tree files."
    },
    "git_cmd_add": {
        "vn_pro": "Thêm file thay đổi vào Staging Area (chuẩn bị commit).",
        "vn_joke": "Gom file lại để chuẩn bị đóng gói (commit).",
        "vn_toxic": "Nhặt rác bỏ vào thùng (staging) chuẩn bị vứt (commit).",
        "en_pro": "Add file contents to the index."
    },
    "git_cmd_commit": {
        "vn_pro": "Gói các file trong Staging Area thành một phiên bản lưu trữ (commit).",
        "vn_joke": "Đóng dấu, chốt đơn những file vừa sửa vào lịch sử.",
        "vn_toxic": "Lưu mẹ cái đống code nhăng cuội này vào lịch sử.",
        "en_pro": "Record changes to the repository."
    },
    "git_cmd_push": {
        "vn_pro": "Đẩy (upload) các commit từ local lên remote server.",
        "vn_joke": "Quăng code lên server cho thiên hạ trầm trồ (hoặc ăn chửi).",
        "vn_toxic": "Đẩy cái đống rác của mày lên server đập vào mặt team.",
        "en_pro": "Update remote refs along with associated objects."
    },
    "git_cmd_pull": {
        "vn_pro": "Kéo (download) code mới nhất từ server về và gộp vào nhánh hiện tại.",
        "vn_joke": "Kéo code của mấy đồng nghiệp về xem có bị conflict không.",
        "vn_toxic": "Bợ code mới trên server về, chuẩn bị tinh thần mà gỡ conflict đi.",
        "en_pro": "Fetch from and integrate with another repository or a local branch."
    },
    "git_cmd_fetch": {
        "vn_pro": "Tải thông tin nhánh và commit mới từ server (không tự động gộp).",
        "vn_joke": "Dòm lén xem server có gì mới không chứ chưa thèm kéo về.",
        "vn_toxic": "Hỏi server xem có thằng nào vừa push code không, đéo ảnh hưởng mẹ gì code mày.",
        "en_pro": "Download objects and refs from another repository."
    },
    "git_cmd_stash": {
        "vn_pro": "Tạm cất (giấu) các thay đổi chưa commit đi chỗ khác.",
        "vn_joke": "Giấu đống code đang gõ dở vào xó tủ để đổi nhánh.",
        "vn_toxic": "Nhét cái đống bùi nhùi chưa xong của mày vào kho, cho đỡ ngứa mắt.",
        "en_pro": "Stash the changes in a dirty working directory away."
    },
    "git_cmd_reset": {
        "vn_pro": "Reset nhánh hiện tại về một commit cũ (có thể làm mất code tùy tham số).",
        "vn_joke": "Cỗ máy thời gian, quay ngược quá khứ (xài ngu là bay màu code nha).",
        "vn_toxic": "Quay lùi lịch sử. Cẩn thận mất mẹ hết đống code vừa gõ đấy!",
        "en_pro": "Reset current HEAD to the specified state."
    },
    "git_cmd_rebase": {
        "vn_pro": "Bứng các commit của nhánh hiện tại đặt lên đầu một nhánh khác.",
        "vn_joke": "Đắp thẳng code của mình lên ngọn cây code của người khác cho đẹp.",
        "vn_toxic": "Viết lại lịch sử dối trá. Lác mắt là dọn conflict ngập mặt cmnl.",
        "en_pro": "Reapply commits on top of another base tip."
    },
    "git_cmd_unknown": {
        "vn_pro": "Lệnh Git tùy chỉnh. Cẩn thận khi thực thi, tool không nắm rõ lệnh này.",
        "vn_joke": "Lệnh gì lạ quắc, tool chưa học. Sếp tự chịu trách nhiệm nha.",
        "vn_toxic": "Gõ cái lệnh l` gì lạ hoắc thế? Nát repo tự chịu trách nhiệm nhé!",
        "en_pro": "Custom Git command. Be careful."
    },

    # Verify I18N
    "verify_title": {"vn_pro": "XÁC MINH KẾT QUẢ REBASE (VERIFY)", "vn_joke": "KIỂM ĐỊNH CHẤT LƯỢNG KÉM", "vn_toxic": "SOI RỚT CODE", "en_pro": "POST-REBASE VERIFICATION"},
    "verify_ahead_ok": {
        "vn_pro": "Nhánh hiện tại đã đi trước (ahead) {base} {ahead} commit.",
        "vn_joke": ["Ngon lành, nhánh đã vượt lên trên {base} {ahead} bước.", "Chuẩn cmnr, đang dẫn trước {base} {ahead} commit."],
        "vn_toxic": ["Thấy chưa? Đã ahead {base} {ahead} commit rồi kìa.", "Check ahead OK, đéo bị tuụt hậu so với {base}."],
        "en_pro": "Current branch is ahead of {base} by {ahead} commit(s)."
    },
    "verify_ahead_fail": {
        "vn_pro": "Cảnh báo: Nhánh hiện tại đang BEHIND {base} {behind} commit! Rebase có vẻ chưa chuẩn.",
        "vn_joke": ["Ối giời ơi, rebase xong sao lại tụt hậu {behind} bước so với {base} thế này?", "Lỗi cmnr, xe chạy lùi à? BEHIND {behind} commit kìa sếp."],
        "vn_toxic": ["Ngu học chưa? Rebase kiểu l` gì mà lại BEHIND {base} tận {behind} commit?", "Mở mắt to ra! Nhánh bị tụt hậu {behind} commit so với gốc rồi!"],
        "en_pro": "Warning: Current branch is BEHIND {base} by {behind} commit(s)! Rebase might have failed conceptually."
    },
    "verify_patch_ok": {
        "vn_pro": "Toàn vẹn code (Patch-ID): 100%. Code trước và sau rebase khớp nhau hoàn toàn!",
        "vn_joke": ["Tuyệt đối không rớt miếng thịt nào. Mã Patch-ID khớp 100% nha sếp!", "Xác minh Patch-ID thành công: Code an toàn 100%."],
        "vn_toxic": ["Test Patch-ID qua rồi, đéo rớt một dòng code nào hết.", "Check Patch-ID khớp 100%. Yên tâm đéo mất code đâu."],
        "en_pro": "Code integrity (Patch-ID): 100%. Pre and post rebase patches match perfectly!"
    },
    "verify_patch_diff": {
        "vn_pro": "Toàn vẹn code: Phát hiện CHÊNH LỆCH (diff) giữa code gốc và sau khi rebase.",
        "vn_joke": ["Á đù, dò Patch-ID thấy lệch xíu code rồi nha. Có ai đụng chạm gì không?", "Còi báo động: Có thay đổi logic code sau rebase sếp ơi!"],
        "vn_toxic": ["ĐM CẢNH BÁO! Lệch code mẹ rồi! Patch-ID đéo khớp!", "Chết dở, code sau rebase đéo giống code cũ! Mất code hay gì?"],
        "en_pro": "Code integrity: Detected DIFFERENCES between original and rebased patches."
    },
    "verify_conflict_reason": {
        "vn_pro": "-> Điều này là BÌNH THƯỜNG vì bạn đã giải quyết conflict thủ công. Hãy tự review lại nhé.",
        "vn_joke": "-> Dĩ nhiên rồi, nãy sếp tự gỡ conflict bằng tay mà. Nhớ review lại bằng mắt cho chắc ăn nha.",
        "vn_toxic": "-> Khác là đúng cmnr, nãy mày ngồi sửa conflict bằng tay mà. Mở mắt ra review lại đi!",
        "en_pro": "-> This is EXPECTED since you manually resolved conflicts. Please review manually."
    },
    "verify_missing_reason": {
        "vn_pro": "-> NGUY HIỂM: Rebase tự động nhưng code bị thay đổi. Có thể đã bị mất hoặc ghi đè code rác!",
        "vn_joke": "-> CĂNG NHA: Nãy rebase mượt mà tự nhiên rớt code là sao? Sếp check lại gấp!",
        "vn_toxic": "-> ĐM NGUY HIỂM VCL! Tự động rebase mà bị lệnh code? Chắc chắn mất code mẹ rồi, check gấp!",
        "en_pro": "-> DANGER: Automated rebase altered the patch logic. Code might be lost or silently overwritten!"
    },
    "verify_no_ref": {
        "vn_pro": "CẢNH BÁO: Không có nhánh backup hay remote tracking branch để đối chiếu toàn vẹn code!",
        "vn_joke": ["Liều quá sếp, không có backup lấy gì mà so sánh check code bị rớt hay không?", "Chịu chết, không có nhánh gốc lấy gì mà verify sếp ơi."],
        "vn_toxic": ["Đéo tạo backup thì lấy cái cc gì ra để đối chiếu xem có rớt code không? Ngu thì chịu!", "Chịu! Đéo có backup thì tự cầu nguyện là không rớt code đi."],
        "en_pro": "WARNING: No backup branch or remote tracking branch to verify code integrity against!"
    },
    "verify_diff_cmd": {
        "vn_pro": "Gõ lệnh này để kiểm tra tay sự khác biệt:",
        "vn_joke": "Copy paste lệnh này xem code chênh lệch ở đâu nè:",
        "vn_toxic": "Cóp lệnh l` này ném vào terminal mà soi:",
        "en_pro": "Run this command to check differences manually:"
    },
    "verify_push_q": {
        "vn_pro": "Xác minh (Verify) bị cảnh báo. BẠN CÓ MUỐN BỎ QUA VÀ TIẾP TỤC PUSH FORCE KHÔNG?",
        "vn_joke": ["Cảnh báo đỏ lòm kìa sếp, vẫn nhắm mắt nhắm mũi Push Force lên luôn chứ?", "Verify xịt rồi, liều mạng Push đè lên server không?"],
        "vn_toxic": ["ĐM đang báo lỗi rớt code kìa, CÓ ĐUI MÙ MUỐN CỐ TÌNH PUSH FORCE GHI ĐÈ LÊN SERVER KHÔNG?", "Cảnh báo rõ to rành rành đấy, MÀY VẪN MUỐN PUSH À?"],
        "en_pro": "Verification raised warnings. DO YOU STILL WANT TO PROCEED WITH FORCE PUSH?"
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
        "vn_pro": "Hủy và quay về", "vn_joke": "Quay xe sếp ơi", "vn_toxic": "Cút về chỗ cũ", "en_pro": "Cancel and return"
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
        "vn_pro": "Đã hủy thao tác hiện tại.", 
        "vn_joke": ["Đã quay xe thành công.", "Hủy lệnh! Sếp lật mặt nhanh quá.", "Đã thắng gấp hất văng mọi thao tác."], 
        "vn_toxic": ["Hủy cmnr.", "Lắm trò vãi, đã hủy!", "Chơi hệ lật lọng à? Hủy rồi đấy!"], 
        "en_pro": "Operation canceled."
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
    "rebase_ext_success": {
        "vn_pro": "Phát hiện rebase đã hoàn tất (có thể bạn đã xử lý qua IDE).",
        "vn_joke": "Ủa sếp tự xử rebase trên IDE xong rồi à? Hay quá ta, đi tiếp thôi!",
        "vn_toxic": "Mày tự bấm rebase xong trên IDE rồi chứ gì? Đỡ tốn công tao, đi tiếp!",
        "en_pro": "Detected rebase has been completed externally (e.g., via IDE)."
    },
    "rebase_skip_q": {
        "vn_pro": "Working tree đang sạch nhưng chưa xong. (Có thể bạn đã commit thủ công). Chạy 'git rebase --skip' để đi tiếp?",
        "vn_joke": "Sếp lỡ tay commit thủ công rồi đúng không? Kẹt xe rồi kìa, có muốn Skip qua luôn không?",
        "vn_toxic": "Sửa file xong tự tay commit đúng không thằng ngu? Giờ kẹt cmnr, bấm Skip lẹ đi để t đi tiếp!",
        "en_pro": "Working tree is clean but rebase stuck (Manual commit?). Run 'git rebase --skip' to bypass?"
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
        "vn_pro": "Rebase completed successfully.", 
        "vn_joke": ["Tuyệt vời, rebase mượt mà như Sunsilk.", "Ngon lành cành đào, không vấp miếng conflict nào luôn.", "Đỉnh chóp, rebase cái một xong luôn."], 
        "vn_toxic": ["Rebase xong cmnr, may đéo conflict.", "Xong rồi đấy, phúc tổ 70 đời đéo bị lỗi.", "Êm xui cmnr."], 
        "en_pro": "Rebase completed successfully."
    },
    
    # Missing Action Status Keys added back
    "opt_abort_confirm": {
        "vn_pro": "Bạn có chắc chắn muốn hủy (abort) rebase không?",
        "vn_joke": "Sếp lật bàn hủy rebase ngang hông thật á?",
        "vn_toxic": "Mày có chắc là muốn hủy bỏ rebase vứt hết không?",
        "en_pro": "Are you sure you want to abort rebase?"
    },
    "abort_success": {
        "vn_pro": "Đã hủy rebase thành công.",
        "vn_joke": "Đã sút văng ca rebase này vào sọt rác.",
        "vn_toxic": "Hủy cmn rebase rồi đấy.",
        "en_pro": "Aborted rebase successfully."
    },
    "abort_fail": {
        "vn_pro": "Không thể hủy rebase. Có lỗi xảy ra.",
        "vn_joke": "Hủy không được sếp ơi, kẹt cứng rồi.",
        "vn_toxic": "Đéo hủy được! Lỗi tùm lum rồi.",
        "en_pro": "Cannot abort rebase. An error occurred."
    },
    "continue_fail": {
        "vn_pro": "Không thể tiếp tục rebase. Vui lòng kiểm tra lại trạng thái.",
        "vn_joke": "Vấp ổ gà rồi, không đi tiếp được sếp ạ.",
        "vn_toxic": "Tiếp tục cái đéo gì? Đang lòi ra đống lỗi kia kìa!",
        "en_pro": "Cannot continue rebase. Please check git status."
    },
    "rebase_still_running": {
        "vn_pro": "Rebase vẫn đang chạy, có thể cần thao tác thêm do có nhiều commit.",
        "vn_joke": "Vẫn chưa xong đâu sếp, đi qua được 1 trạm thôi, còn trạm nữa kìa.",
        "vn_toxic": "Rebase đéo xong ngay được đâu, gỡ tiếp cái mớ conflict bùng nhùng kia đi!",
        "en_pro": "Rebase still running, more steps might be needed."
    },
    "rebase_keep_state": {
        "vn_pro": "Giữ nguyên trạng thái rebase hiện tại. Đang về menu chính.",
        "vn_joke": "Lưu game tạm ở đây nhé, cho sếp về menu ngắm cảnh.",
        "vn_toxic": "Kệ mẹ đống nát này ở đây đấy, về menu!",
        "en_pro": "Keeping current rebase state. Returning to main menu."
    },
    "err_no_base_point": {
        "vn_pro": "Không tìm thấy commit gốc (base point) để thực hiện squash.",
        "vn_joke": "Mù đường cmnr, chả thấy cái base point nào để squash cả.",
        "vn_toxic": "Đéo đào ra được cái gốc để squash, nhánh mày như cái tổ quạ ấy!",
        "en_pro": "Cannot find base point to squash."
    },
    "warn_complex_history": {
        "vn_pro": "Lịch sử branch quá phức tạp, hãy dùng git log kiểm tra tay.",
        "vn_joke": "Lịch sử nhánh này nát như tương bần, sếp tự check bằng tay giùm con.",
        "vn_toxic": "Lịch sử rác vcl tool đéo thèm dò, tự mở git log ra mà lác mắt!",
        "en_pro": "Branch history is complex, please check git log manually."
    },
    "warn_cancel_auto_push": {
        "vn_pro": "Đã hủy bước Auto Push đè lên server theo yêu cầu của bạn.",
        "vn_joke": "Thắng gấp! Đã chặn không cho push lên server theo ý sếp.",
        "vn_toxic": "Sợ rớt code thì tao hủy push cmnr đấy, tự thân vận động đi!",
        "en_pro": "Canceled Auto Push step as requested."
    },
    "flow_stopped": {
        "vn_pro": "Thao tác đã dừng. Quay về màn hình chờ.",
        "vn_joke": "Đứng hình chững lại. Quay về bến đỗ thôi sếp.",
        "vn_toxic": "Cút về chỗ cũ. Thao tác đứt gánh rồi.",
        "en_pro": "Operation stopped. Returning to idle."
    },
    "flow_error": {
        "vn_pro": "Gặp lỗi không xác định trong luồng thực thi:",
        "vn_joke": "Ủa cái quái gì vừa xảy ra vậy? Bug lạ quá:",
        "vn_toxic": "ĐM phát sinh lỗi củ lìn gì đây:",
        "en_pro": "Unexpected error in flow:"
    }
}

def _t(key: str, **kwargs) -> str:
    lang_dict = LANGUAGES.get(key, {})
    
    # Smart Fallback: Rơi tự do từ CURRENT_LANG -> vn_pro -> en_pro -> trả về đúng cái key để gỡ lỗi
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
            pass # Lỡ có kwargs dư hoặc format sai cũng không văng tool
            
    # Thêm Emoji nếu đang bật
    if EMOJI_MODE and key in EMOJI_MAP:
        msg = f"{msg} {EMOJI_MAP[key]}"
        
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
        print(f"\n{THEME.branch(BOX['tl'] + BOX['h']*80)}")
        try:
            subprocess.run(command, shell=True, cwd=repo_dir)
        except Exception as e:
            print(THEME.err(f"Lỗi khi thực thi: {e}"))
        print(f"{THEME.branch(BOX['bl'] + BOX['h']*80)}")
        print(THEME.ok(_t('smart_git_done')))
        pause_continue()
        return True
    else:
        ans2 = input(f"{THEME.info('?')} Có muốn dùng cụm '{command}' như câu trả lời bình thường thay vì lệnh Git không? [y/N]: ").strip().lower()
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
    backup_branch_name = None
    if state["do_backup"]:
        backup_branch_name = create_backup(repo_dir, branch)
        print(f"\n{THEME.ok(_t('created_backup'))} {THEME.branch(backup_branch_name)}")

    run(f"git reset --soft {state['base_point']}", cwd=repo_dir)
    # Dùng hàm quote_arg do shlex lỗi trên Windows CMD khi có khoảng trắng
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
            if result in ("aborted", "menu"):
                maybe_restore_auto_stash(repo_dir, auto_stashed)
                return
        else:
            maybe_restore_auto_stash(repo_dir, auto_stashed)
            raise

    # --- CHẠY BƯỚC VERIFY POST-REBASE ---
    verify_passed = run_verification(repo_dir, state, branch, backup_branch_name, conflict_occurred)

    if state["auto_push"]:
        if not verify_passed:
            if not ask_yes_no("verify_push_q", False, repo_dir=repo_dir):
                print(THEME.warn(_t("warn_cancel_auto_push")))
                maybe_restore_auto_stash(repo_dir, auto_stashed)
                return
        run("git push --force-with-lease", cwd=repo_dir)
        
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
