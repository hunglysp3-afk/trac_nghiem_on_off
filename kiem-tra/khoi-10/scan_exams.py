# -*- coding: utf-8 -*-
"""
TOOL QUÉT FILE ĐỀ THI TỰ ĐỘNG - THPT HÙNG VƯƠNG
Tự động quét các file .html trong thư mục, bóc tách Lớp & Số thứ tự,
đối chiếu với cài đặt giờ thi trong cai_dat_thi.json và cập nhật thẳng vào index.html.
"""

import os
import re
import json
import sys

# Đảm bảo in tiếng Việt mượt mà trên console Windows & Linux
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding='utf-8')


def parse_filename(filename):
    """
    Bóc tách tên file thành Lớp và Dải số thứ tự.
    Ví dụ:
      A2_1_15.html     -> Lớp: 11A2, Từ: 1, Đến: 15
      11A5_16_30.html  -> Lớp: 11A5, Từ: 16, Đến: 30
      A22_31_50.html   -> Lớp: 11A22, Từ: 31, Đến: 50
    """
    name_no_ext = os.path.splitext(filename)[0]
    
    # 1. Tìm tên lớp: A2, A5, A22 hoặc 11A2, 11A5...
    class_match = re.search(r'(?:1)?([A-Za-z]\d+)', name_no_ext, re.IGNORECASE)
    if not class_match:
        return None
    
    raw_class = class_match.group(1).upper()
    class_id = raw_class if raw_class.startswith("1") else f"1{raw_class}"
    
    # 2. Loại bỏ phần tên lớp ở đầu để tìm chính xác dải số thứ tự (ví dụ: A2_16_30 -> 16_30)
    remaining = re.sub(r'^(?:1)?[A-Za-z]\d+[_\-–]?', '', name_no_ext)
    range_match = re.search(r'(\d+)[_\-–](\d+)', remaining)
    if range_match:
        start_num = int(range_match.group(1))
        end_num = int(range_match.group(2))
        title = f"{class_id}: Số {start_num} đến {end_num}"
        desc = f"Khu vực bài thi dành cho số thứ tự {start_num} - {end_num}"
    else:
        start_num = 999
        title = f"{class_id}: Phòng thi ({name_no_ext})"
        desc = f"Phòng thi trực tuyến lớp {class_id}"
        
    return {
        "class_id": class_id,
        "start_num": start_num,
        "title": title,
        "desc": desc,
        "file": filename
    }

def main():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    # 1. Đọc file cấu hình cài đặt giờ và pass nếu có
    config_file = os.path.join(current_dir, "cai_dat_thi.json")
    class_configs = {}
    if os.path.exists(config_file):
        try:
            with open(config_file, "r", encoding="utf-8") as f:
                class_configs = json.load(f)
        except Exception as e:
            print(f"[!] Lỗi khi đọc cai_dat_thi.json: {e}")

    # 2. Quét các file .html trong thư mục
    ignore_files = {"index.html", "index (1).html", "template.html"}
    classes_data = {}
    
    for fname in sorted(os.listdir(current_dir)):
        if not fname.lower().endswith(".html"):
            continue
        if fname.lower() in ignore_files:
            continue
            
        parsed = parse_filename(fname)
        if not parsed:
            continue
            
        cid = parsed["class_id"]
        if cid not in classes_data:
            classes_data[cid] = []
        classes_data[cid].append(parsed)

    # Nếu chưa có file nào trong thư mục, tạo sẵn danh sách mẫu cho 3 lớp
    if not classes_data:
        print("[*] Chưa thấy file đề con, sử dụng danh mục mẫu chuẩn...")
        classes_data = {
            "11A2": [
                {"title": "Lớp 11A2: Số 1 đến 15", "desc": "Khu vực bài thi dành cho số thứ tự 1 - 15", "file": "A2_1_15.html", "start_num": 1},
                {"title": "Lớp 11A2: Số 16 đến 30", "desc": "Khu vực bài thi dành cho số thứ tự 16 - 30", "file": "A2_16_30.html", "start_num": 16},
                {"title": "Lớp 11A2: Số 31 đến 50", "desc": "Khu vực bài thi dành cho số thứ tự 31 - 50", "file": "A2_31_50.html", "start_num": 31}
            ],
            "11A5": [
                {"title": "Lớp 11A5: Số 1 đến 15", "desc": "Khu vực bài thi dành cho số thứ tự 1 - 15", "file": "A5_1_15.html", "start_num": 1},
                {"title": "Lớp 11A5: Số 16 đến 30", "desc": "Khu vực bài thi dành cho số thứ tự 16 - 30", "file": "A5_16_30.html", "start_num": 16},
                {"title": "Lớp 11A5: Số 31 đến 50", "desc": "Khu vực bài thi dành cho số thứ tự 31 - 50", "file": "A5_31_50.html", "start_num": 31}
            ],
            "11A22": [
                {"title": "Lớp 11A22: Số 1 đến 15", "desc": "Khu vực bài thi dành cho số thứ tự 1 - 15", "file": "A22_1_15.html", "start_num": 1},
                {"title": "Lớp 11A22: Số 16 đến 30", "desc": "Khu vực bài thi dành cho số thứ tự 16 - 30", "file": "A22_16_30.html", "start_num": 16},
                {"title": "Lớp 11A22: Số 31 đến 50", "desc": "Khu vực bài thi dành cho số thứ tự 31 - 50", "file": "A22_31_50.html", "start_num": 31}
            ]
        }

    # 3. Tổng hợp thành cấu trúc hoàn chỉnh
    final_classes = []
    
    # Sắp xếp các lớp theo thứ tự tự nhiên (ví dụ 11A2 -> 11A5 -> 11A22)
    def natural_sort_key(s):
        return [int(text) if text.isdigit() else text.lower() for text in re.split(r'(\d+)', s)]
        
    for cid in sorted(classes_data.keys(), key=natural_sort_key):
        rooms = classes_data[cid]
        rooms.sort(key=lambda r: r.get("start_num", 0))
        
        cfg = class_configs.get(cid, {})
        class_entry = {
            "id": cid,
            "name": cfg.get("ten_lop", f"Lớp {cid}"),
            "password": cfg.get("pass", cid.lower()),
            "startTime": cfg.get("gio_mo", "2026-04-20 10:35"),
            "durationMinutes": cfg.get("thoi_luong", 15),
            "rooms": [
                {
                    "title": r["title"],
                    "desc": r["desc"],
                    "file": r["file"]
                }
                for r in rooms
            ]
        }
        
        # Nếu có chỉ định đích danh giờ đóng
        if "gio_dong" in cfg and cfg["gio_dong"]:
            class_entry["endTimeFixed"] = cfg["gio_dong"]
            
        final_classes.append(class_entry)

    # 4. Xuất danh sách ra file JSON để tham chiếu
    output_json_path = os.path.join(current_dir, "danh_sach_thi.json")
    with open(output_json_path, "w", encoding="utf-8") as f:
        json.dump(final_classes, f, ensure_ascii=False, indent=2)
    print(f"[+] Đã cập nhật: {output_json_path}")

    # 5. Cập nhật thẳng vào file index.html và index (1).html
    js_data_string = json.dumps(final_classes, ensure_ascii=False, indent=4)
    target_block = f"/* AUTO_EXAM_DATA_START */\nconst EXAM_CLASSES = {js_data_string};\n/* AUTO_EXAM_DATA_END */"

    for target_name in ["index.html", "index (1).html"]:
        target_path = os.path.join(current_dir, target_name)
        if not os.path.exists(target_path):
            continue
            
        with open(target_path, "r", encoding="utf-8") as f:
            content = f.read()

        pattern = r'/\* AUTO_EXAM_DATA_START \*/.*?/\* AUTO_EXAM_DATA_END \*/'
        if re.search(pattern, content, flags=re.DOTALL):
            new_content = re.sub(pattern, target_block, content, flags=re.DOTALL)
            with open(target_path, "w", encoding="utf-8") as f:
                f.write(new_content)
            print(f"[+] Đã chèn dữ liệu tự động vào {target_name} thành công!")
        else:
            print(f"[!] Chưa tìm thấy tag AUTO_EXAM_DATA trong {target_name}, sẽ cập nhật khi file HTML được nâng cấp.")

    print(f"==> HOÀN TẤT: Đã quét {len(final_classes)} lớp với tổng cộng {sum(len(c['rooms']) for c in final_classes)} phòng thi.")

if __name__ == "__main__":
    main()
