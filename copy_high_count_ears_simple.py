#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
复制高数量耳号工具
用于复制score目录中大于等于2个有效文件夹的耳号到new文件夹
"""

import os
import shutil
from typing import Dict


class HighCountEarCopier:
    """高数量耳号复制器"""
    
    def __init__(self, score_dir: str, target_dir: str = "new"):
        """
        初始化复制器
        
        Args:
            score_dir: score目录路径
            target_dir: 目标目录名称，默认为"new"
        """
        self.score_dir = score_dir
        self.target_dir = target_dir
        self.min_count = 2  # 最小文件夹数量阈值（包含2个）
        
    def copy_high_count_ears(self) -> Dict[str, int]:
        """
        复制包含大于等于指定数量有效文件夹的耳号到新文件夹
        同时复制undetected文件夹，方便人工检查
        
        Returns:
            统计信息字典
        """
        if not os.path.exists(self.score_dir):
            print(f"❌ score目录不存在: {self.score_dir}")
            return {}
        
        # 创建目标文件夹
        target_path = os.path.join(os.path.dirname(self.score_dir), self.target_dir)
        os.makedirs(target_path, exist_ok=True)
        
        print(f"📁 开始复制包含大于等于{self.min_count}个有效文件夹的耳号...")
        print(f"📁 同时复制undetected文件夹，方便人工检查")
        print(f"📂 源目录: {self.score_dir}")
        print(f"📂 目标目录: {target_path}")
        print("-" * 60)
        
        copied_count = 0
        total_size = 0
        detailed_stats = {}
        undetected_count = 0
        
        # 遍历score目录
        for date_folder in os.listdir(self.score_dir):
            date_path = os.path.join(self.score_dir, date_folder)
            if not os.path.isdir(date_path):
                continue
            
            print(f"📅 处理日期: {date_folder}")
            detailed_stats[date_folder] = {}
            
            # 处理undetected文件夹
            if date_folder == 'undetected':
                undetected_path = os.path.join(self.score_dir, 'undetected')
                target_undetected_path = os.path.join(target_path, 'undetected')
                
                if not os.path.exists(target_undetected_path):
                    try:
                        shutil.copytree(undetected_path, target_undetected_path, dirs_exist_ok=True)
                        undetected_size = self._get_folder_size(undetected_path)
                        total_size += undetected_size
                        undetected_count += 1
                        print(f"  ✅ 复制undetected文件夹 -> {os.path.basename(target_undetected_path)}")
                    except Exception as e:
                        print(f"  ❌ 复制undetected文件夹失败: {e}")
                else:
                    print(f"  ⏭️ undetected文件夹已存在")
                continue
            
            for ear_folder in os.listdir(date_path):
                ear_path = os.path.join(date_path, ear_folder)
                if not os.path.isdir(ear_path):
                    continue
                
                # 检查是否是重命名后的耳号文件夹（格式：耳号-数量）
                if '-' not in ear_folder:
                    continue
                
                try:
                    ear_number, folder_count_str = ear_folder.rsplit('-', 1)
                    folder_count = int(folder_count_str)
                    
                    # 检查是否满足条件（大于等于2个有效文件夹）
                    if folder_count >= self.min_count:
                        # 构建目标路径
                        target_ear_path = os.path.join(target_path, f"{date_folder}_{ear_folder}")
                        
                        if not os.path.exists(target_ear_path):
                            try:
                                # 复制整个耳号文件夹
                                shutil.copytree(ear_path, target_ear_path, dirs_exist_ok=True)
                                
                                # 计算文件夹大小
                                folder_size = self._get_folder_size(ear_path)
                                total_size += folder_size
                                
                                print(f"  ✅ 复制: {ear_folder} ({folder_count} 个有效文件夹) -> {os.path.basename(target_ear_path)}")
                                copied_count += 1
                                
                                # 记录统计信息
                                detailed_stats[date_folder][ear_number] = folder_count
                                
                            except Exception as e:
                                print(f"  ❌ 复制失败 {ear_folder}: {e}")
                        else:
                            print(f"  ⏭️ 目标已存在: {os.path.basename(target_ear_path)}")
                    else:
                        print(f"  ⏭️ 跳过: {ear_folder} ({folder_count} 个文件夹，不满足条件)")
                    
                except ValueError:
                    print(f"  ⚠️  跳过: {ear_folder} (格式不正确)")
                    continue
        
        # 显示复制结果
        self._display_copy_results(copied_count, undetected_count, total_size, target_path, detailed_stats)
        
        return detailed_stats
    
    def _get_folder_size(self, folder_path: str) -> int:
        """计算文件夹大小（字节）"""
        total_size = 0
        try:
            for dirpath, dirnames, filenames in os.walk(folder_path):
                for filename in filenames:
                    file_path = os.path.join(dirpath, filename)
                    if os.path.exists(file_path):
                        total_size += os.path.getsize(file_path)
        except Exception:
            pass
        return total_size
    
    def _format_size(self, size_bytes: int) -> str:
        """格式化文件大小显示"""
        if size_bytes == 0:
            return "0B"
        
        size_names = ["B", "KB", "MB", "GB", "TB"]
        i = 0
        while size_bytes >= 1024 and i < len(size_names) - 1:
            size_bytes /= 1024.0
            i += 1
        
        return f"{size_bytes:.1f}{size_names[i]}"
    
    def _display_copy_results(self, copied_count: int, undetected_count: int, total_size: int, target_path: str, detailed_stats: Dict):
        """显示复制结果"""
        print("\n" + "=" * 60)
        print("📊 复制完成统计")
        print("=" * 60)
        print(f"📁 复制的耳号数量: {copied_count}")
        print(f"📁 复制的undetected文件夹数量: {undetected_count}")
        print(f"💾 总大小: {self._format_size(total_size)}")
        print(f"📂 目标文件夹: {target_path}")
        
        if copied_count > 0 or undetected_count > 0:
            print(f"\n📋 详细统计（按日期）")
            print("-" * 40)
            
            for date in sorted(detailed_stats.keys()):
                if detailed_stats[date]:  # 只显示有数据的日期
                    print(f"📅 日期: {date}")
                    # 按文件夹数量排序
                    sorted_ears = sorted(detailed_stats[date].items(), 
                                       key=lambda x: x[1], reverse=True)
                    for ear_number, folder_count in sorted_ears:
                        print(f"  🏷️  耳号 {ear_number}: {folder_count} 个有效文件夹")
                    print()
        else:
            print("\n⚠️  没有找到满足条件的耳号文件夹或undetected文件夹")
        
        print("=" * 60)


def main():
    """主函数"""
    print("=" * 60)
    print("📁 高数量耳号复制工具")
    print("=" * 60)
    print("功能：复制score目录中大于等于2个有效文件夹的耳号到new文件夹")
    print()
    
    # 获取用户输入的score目录路径
    while True:
        score_dir = input("请输入score目录的完整路径: ").strip()
        
        # 去除引号
        if score_dir.startswith('"') and score_dir.endswith('"'):
            score_dir = score_dir[1:-1]
        elif score_dir.startswith("'") and score_dir.endswith("'"):
            score_dir = score_dir[1:-1]
        
        if os.path.exists(score_dir):
            break
        else:
            print(f"❌ 路径不存在: {score_dir}")
            print("请重新输入正确的路径")
    
    print(f"\n✅ 找到score目录: {score_dir}")
    
    # 创建复制器并执行复制
    copier = HighCountEarCopier(score_dir, "new")
    
    try:
        print("\n🚀 开始复制操作...")
        copier.copy_high_count_ears()
        print("\n🎉 复制操作完成！")
        
        # 询问是否打开目标文件夹
        target_path = os.path.join(os.path.dirname(score_dir), "new")
        if os.path.exists(target_path):
            open_folder = input(f"\n是否打开目标文件夹 {target_path}? (y/n): ").strip().lower()
            if open_folder in ['y', 'yes', '是']:
                try:
                    os.startfile(target_path)  # Windows
                except AttributeError:
                    try:
                        import subprocess
                        subprocess.run(['open', target_path])  # macOS
                    except FileNotFoundError:
                        subprocess.run(['xdg-open', target_path])  # Linux
                    print(f"📂 已尝试打开文件夹: {target_path}")
        
    except Exception as e:
        print(f"\n❌ 复制过程中发生错误: {e}")
    
    input("\n按回车键退出...")


if __name__ == "__main__":
    main()
