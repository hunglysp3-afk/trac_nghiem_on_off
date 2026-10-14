# -*- coding: utf-8 -*-
"""
TOOL QUÉT FILE ĐỀ THI TỰ ĐỘNG - HỖ TRỢ TOÀN DIỆN MỌI KHỐI LỚP (10, 11, 12)
Tự động quét các file .html trong thư mục, bóc tách chính xác Khối lớp (10, 11, 12) & Số thứ tự,
đối chiếu với cài đặt giờ thi trong cai_dat_thi.json và cập nhật thẳng vào index.html.
"""

import os
import re
import json
import sys

# Đảm bảo in tiếng Việt mượt mà trên console Windows & Linux
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding='utf-8')


def detect_default_grade(current_dir, class_configs):
    """
    Tự động phát hiện khối lớp mặc định từ cai_dat_thi.json hoặc tên thư mục.
    """
    if class_configs:
        for key in class_configs.keys():
            match = re.search(r'^(10|11|12)', str(key))
            if match:
                return match.group(1)
                
    folder_name = os.path.basename(current_dir).lower()
    match = re.search(r'(?:khoi|k|vat_li|ly)?_?(10|11|12)', folder_name)
    if match:
        return match.group(1)
        
    return "11"  # Mặc định nếu không có thông tin


def parse_filename(filename, default_grade="11", class_configs=None):
    """
    Bóc tách tên file thành Lớp và Dải số thứ tự cho MỌI KHỐI LỚP (10, 11, 12).
    Hỗ trợ cả tên đầy đủ lẫn viết tắt:
      - 10A11_1_15.html  -> Lớp: 10A11, STT: 1 - 15
      - A11_1_15.html    -> Khớp với 10A11 nếu có trong config, hoặc {default_grade}A11
      - 11A5_16_30.html  -> Lớp: 11A5, STT: 16 - 30
      - 12A3_31_50.html  -> Lớp: 12A3, STT: 31 - 50
    """
    name_no_ext = os.path.splitext(filename)[0]
    class_id = None
    
    # 1. Khớp ưu tiên với danh sách lớp trong cai_dat_thi.json (sắp xếp key dài trước để tránh nhầm)
    if class_configs:
        sorted_keys = sorted(class_configs.keys(), key=len, reverse=True)
        for cfg_key in sorted_keys:
            # Lấy phần chữ và số (ví dụ: "10A11" -> "A11")
            short_match = re.search(r'([A-Za-z]+\d*)', cfg_key)
            short_name = short_match.group(1).upper() if short_match else cfg_key.upper()
            
            # Khớp nếu tên file bắt đầu bằng cfg_key (10A11) hoặc short_name (A11)
            pattern = rf'^(?:lop|khoi)?[_\- ]*(?:{re.escape(cfg_key)}|{re.escape(short_name)})(?:[_\- ]|$)'
            if re.search(pattern, name_no_ext, re.IGNORECASE):
                class_id = cfg_key.upper()
                break

    # 2. Nếu chưa có trong config, tự động trích xuất từ tên file
    if not class_id:
        # Tên file có sẵn số khối (10, 11, 12)
        match_full = re.search(r'^(?:lop|khoi)?[_\- ]*((?:10|11|12)[A-Za-z]+\d*)', name_no_ext, re.IGNORECASE)
        if match_full:
            class_id = match_full.group(1).upper()
        else:
            # Tên file viết tắt (vd: A2, A5...) -> ghép với khối mặc định
            match_short = re.search(r'^(?:lop|khoi)?[_\- ]*([A-Za-z]+\d*)', name_no_ext, re.IGNORECASE)
            if match_short:
                short_class = match_short.group(1).upper()
                class_id = f"{default_grade}{short_class}"
            else:
                return None

    # 3. Bóc tách dải số thứ tự (ví dụ: 1_15, 16_30, 31_50)
    remaining = re.sub(rf'^(?:lop|khoi)?[_\- ]*(?:{re.escape(class_id)}|[A-Za-z]+\d*)[_\- ]*', '', name_no_ext, flags=re.IGNORECASE)
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

    default_grade = detect_default_grade(current_dir, class_configs)

    # 2. Quét các file .html trong thư mục
    ignore_files = {"index.html", "index (1).html", "template.html"}
    classes_data = {}
    
    for fname in sorted(os.listdir(current_dir)):
        if not fname.lower().endswith(".html"):
            continue
        if fname.lower() in ignore_files:
            continue
            
        parsed = parse_filename(fname, default_grade=default_grade, class_configs=class_configs)
        if not parsed:
            continue
            
        cid = parsed["class_id"]
        # CHỈ chấp nhận các lớp đã được khai báo chính thức trong cai_dat_thi.json (nếu có cấu hình)
        if class_configs and cid not in class_configs:
            continue

        if cid not in classes_data:
            classes_data[cid] = []
        classes_data[cid].append(parsed)

    # Đảm bảo TẤT CẢ các lớp trong cai_dat_thi.json đều xuất hiện (kể cả khi chưa có file riêng)
    if class_configs:
        for cid in class_configs.keys():
            if cid not in classes_data or not classes_data[cid]:
                className = class_configs[cid].get("ten_lop", f"Lớp {cid}")
                short_match = re.search(r'([A-Za-z]+\d*)', cid)
                short_name = short_match.group(1) if short_match else cid
                classes_data[cid] = [
                    {"title": f"{className}: Số 1 đến 15", "desc": "Khu vực bài thi dành cho số thứ tự 1 - 15", "file": f"{short_name}_1_15.html", "start_num": 1},
                    {"title": f"{className}: Số 16 đến 30", "desc": "Khu vực bài thi dành cho số thứ tự 16 - 30", "file": f"{short_name}_16_30.html", "start_num": 16},
                    {"title": f"{className}: Số 31 đến 50", "desc": "Khu vực bài thi dành cho số thứ tự 31 - 50", "file": f"{short_name}_31_50.html", "start_num": 31}
                ]


    # 3. Tổng hợp thành cấu trúc hoàn chỉnh
    final_classes = []
    detected_grades = set()
    
    # Sắp xếp các lớp tự nhiên (10A1 -> 10A2 -> 11A2 -> 12A1...)
    def natural_sort_key(s):
        return [int(text) if text.isdigit() else text.lower() for text in re.split(r'(\d+)', s)]
        
    for cid in sorted(classes_data.keys(), key=natural_sort_key):
        rooms = classes_data[cid]
        rooms.sort(key=lambda r: r.get("start_num", 0))
        
        # Nhận diện khối lớp
        grade_match = re.search(r'^(10|11|12)', cid)
        if grade_match:
            detected_grades.add(grade_match.group(1))
            
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

    # 4. Xác định tiêu đề khối lớp linh hoạt cho giao diện
    if len(detected_grades) == 1:
        grade_str = list(detected_grades)[0]
        grade_title = f"Khảo Thí Trực Tuyến - Vật Lý {grade_str}"
        breadcrumb_grade = f"Khối {grade_str}"
    elif len(detected_grades) > 1:
        grade_title = "Khảo Thí Trực Tuyến - Vật Lý THPT"
        breadcrumb_grade = "Các Khối Lớp"
    else:
        grade_title = "Khảo Thí Trực Tuyến - Vật Lý"
        breadcrumb_grade = "Khảo Thí"

    # 5. Xuất danh sách ra file JSON để tham chiếu
    output_json_path = os.path.join(current_dir, "danh_sach_thi.json")
    with open(output_json_path, "w", encoding="utf-8") as f:
        json.dump(final_classes, f, ensure_ascii=False, indent=2)
    print(f"[+] Đã cập nhật: {output_json_path}")

    # 6. Cập nhật thẳng vào file index.html và index (1).html
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
            content = re.sub(pattern, target_block, content, flags=re.DOTALL)
            
            # Cập nhật linh hoạt tiêu đề khối lớp trên giao diện HTML
            content = re.sub(r'<span id="gradeBreadcrumb"[^>]*>.*?</span>', f'<span id="gradeBreadcrumb" style="color: var(--text-main); font-weight: 600;">{breadcrumb_grade}</span>', content)
            content = re.sub(r'<span id="gradeTitle"[^>]*>.*?</span>', f'<span id="gradeTitle">{grade_title}</span>', content)
            
            # Cập nhật thẻ <title> ở phần đầu trang
            content = re.sub(r'<title>.*?</title>', f'<title>{grade_title}</title>', content)
            
            with open(target_path, "w", encoding="utf-8") as f:
                f.write(content)
            print(f"[+] Đã chèn dữ liệu tự động vào {target_name} thành công!")
        else:
            print(f"[!] Chưa tìm thấy tag AUTO_EXAM_DATA trong {target_name}")

    grade_info = f"Khối {', '.join(sorted(detected_grades))}" if detected_grades else "Đa khối"
    print(f"==> HOÀN TẤT: Đã quét {len(final_classes)} lớp ({grade_info}) với tổng cộng {sum(len(c['rooms']) for c in final_classes)} phòng thi.")


if __name__ == "__main__":
    main()
