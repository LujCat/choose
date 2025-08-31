from model_manager import ModelManager
from file_scanner import FileScanner
from file_processor import FileProcessor
from utils import ProgressTracker
import os

class ImageClassifier:
    """图像分类器主类，整合所有功能模块"""
    
    def __init__(self, model_path="gpu.onnx"):
        self.model_manager = ModelManager(model_path)
        self.file_scanner = FileScanner()
    
    def process_directory(self, root_dir: str):
        """
        处理目录中的所有图片
        
        Args:
            root_dir: 根目录路径
        """
        if not self.model_manager.is_ready():
            print("❌ 模型未准备就绪")
            return
        
        # 创建文件处理器
        file_processor = FileProcessor(root_dir)
        
        # 创建score目录结构
        file_processor.create_score_structure()
        
        # 显示目录结构信息
        print("🔍 正在分析目录结构...")
        directory_structure = self.file_scanner.get_directory_structure(root_dir)
        
        if not directory_structure:
            print("❌ 未找到包含EPCData的目录")
            return
        
        print(f"\n📊 目录结构分析结果:")
        print("=" * 60)
        total_folders = 0
        for dir_name, dir_info in directory_structure.items():
            folder_count = len(dir_info['sub_folders'])
            total_folders += folder_count
            print(f"📁 {dir_name}/")
            print(f"  └── EPCData/ ({folder_count} 个文件夹)")
            for sub_folder in dir_info['sub_folders'][:5]:  # 只显示前5个
                print(f"      └── {sub_folder}")
            if folder_count > 5:
                print(f"      ... 还有 {folder_count - 5} 个文件夹")
        print(f"\n📈 总计: {len(directory_structure)} 个主目录，{total_folders} 个图片文件夹")
        print("=" * 60)
        
        # 扫描图片文件
        print("\n🔍 正在扫描图片文件...")
        image_files = self.file_scanner.scan_for_images(root_dir)
        
        if not image_files:
            print("❌ 未找到符合条件的图片文件")
            return
        
        print(f"\n📁 找到 {len(image_files)} 个图片文件夹")
        print("📋 将按照以下结构组织文件：")
        print("   score/日期/耳号/分数/具体文件夹")
        print("   例如：score/2025-06-21/10/80/00000010-2025-06-21-10-41-09-066")
        print("-" * 60)
        
        # 创建进度跟踪器
        progress = ProgressTracker(len(image_files), "处理图片文件夹")
        
        # 处理每个图片
        success_count = 0
        structure_info = {}  # 记录目录结构信息
        
        for i, (img_path, folder_path) in enumerate(image_files, 1):
            folder_name = os.path.basename(folder_path)
            print(f"\n[{i}/{len(image_files)}] 处理: {folder_name}")
            
            try:
                # 检测置信度
                confidence = self.model_manager.detect_image(img_path)
                
                # 处理文件夹
                target_path = file_processor.process_image_folder(img_path, folder_path, confidence)
                
                # 复制文件夹
                if file_processor.copy_folder(folder_path, target_path):
                    success_count += 1
                    
                    # 记录目录结构信息
                    target_parts = target_path.split(os.sep)
                    if len(target_parts) >= 5:
                        date = target_parts[-4]
                        ear_number = target_parts[-3]
                        score = target_parts[-2]
                        
                        if date not in structure_info:
                            structure_info[date] = {}
                        if ear_number not in structure_info[date]:
                            structure_info[date][ear_number] = {}
                        if score not in structure_info[date][ear_number]:
                            structure_info[date][ear_number][score] = []
                        
                        structure_info[date][ear_number][score].append(folder_name)
                
                # 更新进度
                progress.update()
                
            except Exception as e:
                print(f"❌ 处理失败: {e}")
        
        # 完成进度跟踪
        progress.finish()
        
        # 显示目录结构统计
        self._display_structure_summary(structure_info)
        
        print(f"\n✅ 处理完成！成功处理 {success_count}/{len(image_files)} 个文件夹")
        
        # 重命名耳号文件夹，添加数量信息
        print("\n🔄 开始重命名耳号文件夹...")
        file_processor.rename_ear_folders_with_count()
        
        # 生成统计报告
        print("\n📊 开始生成统计报告...")
        count_stats = file_processor.generate_statistics_report()
        
        # 显示统计结果
        self._display_count_statistics(count_stats)
        
        print("\n🎉 所有操作完成！")
    
    def _display_structure_summary(self, structure_info: dict):
        """显示目录结构统计信息"""
        if not structure_info:
            return
        
        print("\n📊 目录结构统计:")
        print("=" * 50)
        
        total_folders = 0
        for date in sorted(structure_info.keys()):
            print(f"\n📅 日期: {date}")
            date_total = 0
            
            for ear_number in sorted(structure_info[date].keys()):
                print(f"  🏷️  耳号: {ear_number}")
                ear_total = 0
                
                for score in sorted(structure_info[date][ear_number].keys()):
                    folder_count = len(structure_info[date][ear_number][score])
                    print(f"    📁 分数 {score}: {folder_count} 个文件夹")
                    ear_total += folder_count
                
                print(f"    📊 耳号 {ear_number} 总计: {ear_total} 个文件夹")
                date_total += ear_total
            
            print(f"  📊 日期 {date} 总计: {date_total} 个文件夹")
            total_folders += date_total
        
        print(f"\n🎯 总体统计: {total_folders} 个文件夹")
    
    def _display_count_statistics(self, count_stats: dict):
        """显示数量区间统计信息"""
        if not count_stats:
            return
        
        print("\n📈 数量区间统计:")
        print("=" * 40)
        print(f"大于2个文件夹的耳号数量: {count_stats['>2']}")
        print(f"大于3个文件夹的耳号数量: {count_stats['>3']}")
        print(f"大于4个文件夹的耳号数量: {count_stats['>4']}")
        print(f"大于5个文件夹的耳号数量: {count_stats['>5']}")
        print("=" * 40)
    
    def is_ready(self):
        """检查分类器是否准备就绪"""
        return self.model_manager.is_ready()
