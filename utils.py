"""
工具函数模块 - 提供通用的辅助功能
"""

import os
import time
from typing import Optional

def format_time(seconds: float) -> str:
    """格式化时间显示"""
    if seconds < 60:
        return f"{seconds:.1f}秒"
    elif seconds < 3600:
        minutes = int(seconds // 60)
        seconds = seconds % 60
        return f"{minutes}分{seconds:.1f}秒"
    else:
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        seconds = seconds % 60
        return f"{hours}小时{minutes}分{seconds:.1f}秒"

def format_file_size(size_bytes: int) -> str:
    """格式化文件大小显示"""
    if size_bytes == 0:
        return "0B"
    
    size_names = ["B", "KB", "MB", "GB", "TB"]
    i = 0
    while size_bytes >= 1024 and i < len(size_names) - 1:
        size_bytes /= 1024.0
        i += 1
    
    return f"{size_bytes:.1f}{size_names[i]}"

def ensure_directory(path: str) -> bool:
    """确保目录存在，如果不存在则创建"""
    try:
        os.makedirs(path, exist_ok=True)
        return True
    except Exception:
        return False

def is_valid_image_file(file_path: str, supported_extensions: list) -> bool:
    """检查是否为有效的图片文件"""
    if not os.path.isfile(file_path):
        return False
    
    file_ext = os.path.splitext(file_path)[1].lower()
    return file_ext in supported_extensions

def get_relative_path(full_path: str, base_path: str) -> str:
    """获取相对路径"""
    try:
        return os.path.relpath(full_path, base_path)
    except ValueError:
        return full_path

class ProgressTracker:
    """进度跟踪器"""
    
    def __init__(self, total: int, description: str = "处理中"):
        self.total = total
        self.current = 0
        self.description = description
        self.start_time = time.time()
    
    def update(self, increment: int = 1):
        """更新进度"""
        self.current += increment
        self._display_progress()
    
    def _display_progress(self):
        """显示进度"""
        if self.total > 0:
            percentage = (self.current / self.total) * 100
            elapsed_time = time.time() - self.start_time
            
            if self.current > 0:
                estimated_total = (elapsed_time / self.current) * self.total
                remaining_time = estimated_total - elapsed_time
                time_info = f"剩余时间: {format_time(remaining_time)}"
            else:
                time_info = ""
            
            print(f"\r{self.description}: {self.current}/{self.total} ({percentage:.1f}%) {time_info}", end="", flush=True)
    
    def finish(self):
        """完成进度跟踪"""
        total_time = time.time() - self.start_time
        print(f"\n✅ {self.description}完成！总用时: {format_time(total_time)}")
