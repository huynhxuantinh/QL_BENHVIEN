#!/usr/bin/env python
"""
Script rename folder hình ảnh từ ID cũ (783-832) sang ID mới (103-152)
"""
import os
import shutil

media_root = r'c:\Users\TIEN\QL_BENHVIEN\media\benh_vien'

# Mapping: old_id -> new_id
# 783-832 (50 folders) -> 103-152 (50 hospitals)
old_id_start = 783
new_id_start = 103
count = 50

print("=== Rename folder hình ảnh bệnh viện ===\n")

# Trước hết, tạo backup bằng cách rename folder có số
for i in range(count):
    old_id = old_id_start + i
    new_id = new_id_start + i
    old_folder = os.path.join(media_root, str(old_id))
    temp_folder = os.path.join(media_root, f'_temp_{old_id}_{new_id}')
    new_folder = os.path.join(media_root, str(new_id))
    
    if not os.path.exists(old_folder):
        print(f"⚠ Folder cũ không tồn tại: {old_id}")
        continue
    
    if os.path.exists(new_folder):
        print(f"⚠ Folder mới đã tồn tại, bỏ qua: {new_id}")
        continue
    
    print(f"Rename: {old_id} → {new_id}")
    shutil.move(old_folder, temp_folder)

print("\n=== Bước 1 hoàn thành: Rename sang temp ===\n")

# Sau đó rename lại từ temp sang ID mới
for i in range(count):
    old_id = old_id_start + i
    new_id = new_id_start + i
    temp_folder = os.path.join(media_root, f'_temp_{old_id}_{new_id}')
    new_folder = os.path.join(media_root, str(new_id))
    
    if os.path.exists(temp_folder):
        shutil.move(temp_folder, new_folder)
        print(f"✓ Đã rename: {new_id}")

print("\n✓ Hoàn thành rename folder!")
