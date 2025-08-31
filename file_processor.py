import os
import shutil
from typing import Tuple
import re

class FileProcessor:
    """文件处理器，负责文件复制和分类"""
    
    def __init__(self, root_dir: str):
        self.root_dir = root_dir
    
    def extract_folder_info(self, folder_name: str) -> Tuple[str, str]:
        """
        从文件夹名称提取耳号和日期信息
        
        Args:
            folder_name: 文件夹名称，如 "00000010-2025-06-21-10-41-09-066"
            
        Returns:
            (ear_number, date_str) 元组
        """
        # 解析文件夹名称格式：00000010-2025-06-21-10-41-09-066
        # 其中 10 是耳号，2025-06-21 是日期
        pattern = r'^000000(\d+)-(\d{4}-\d{2}-\d{2})-\d{2}-\d{2}-\d{2}-\d+$'
        match = re.match(pattern, folder_name)
        
        if match:
            ear_number = match.group(1)  # 耳号
            date_str = match.group(2)    # 日期
            return ear_number, date_str
        else:
            # 如果格式不匹配，使用默认值
            print(f"⚠️ 文件夹名称格式不匹配: {folder_name}")
            return "unknown", "unknown"
    
    def process_image_folder(self, img_path: str, folder_path: str, confidence: float) -> str:
        """
        处理单个图片文件夹，按照新结构：日期\耳号\分数\具体文件夹
        
        Args:
            img_path: 图片文件路径
            folder_path: 文件夹路径
            confidence: 检测置信度
            
        Returns:
            目标路径
        """
        # 获取文件夹名称
        folder_name = os.path.basename(folder_path)
        
        # 提取耳号和日期
        ear_number, date_str = self.extract_folder_info(folder_name)
        
        # 确定分数文件夹
        if confidence > 0:
            score = int(confidence * 100)
            score_folder = str((score // 10) * 10)
            print(f"✅ 置信度: {confidence:.2f} -> {date_str}/{ear_number}/{score_folder}")
        else:
            score_folder = "undetected"
            print("⏭️ 未检测到目标 -> undetected")
        
        # 构建目标路径：日期\耳号\分数\具体文件夹
        target = os.path.join(
            self.root_dir, 
            'score', 
            date_str,           # 日期
            ear_number,         # 耳号
            score_folder,       # 分数
            folder_name         # 具体文件夹
        )
        
        return target
    
    def copy_folder(self, source_path: str, target_path: str) -> bool:
        """
        复制文件夹到目标位置
        
        Args:
            source_path: 源文件夹路径
            target_path: 目标文件夹路径
            
        Returns:
            是否复制成功
        """
        try:
            if os.path.exists(target_path):
                print("⏭️ 目标已存在，跳过")
                return True
            
            # 创建目标目录
            os.makedirs(os.path.dirname(target_path), exist_ok=True)
            
            # 复制主文件夹
            shutil.copytree(source_path, target_path, dirs_exist_ok=True)
            
            # 复制cuboid文件夹
            self._copy_cuboid_folder(source_path, target_path)
            
            return True
            
        except Exception as e:
            print(f"❌ 复制失败: {e}")
            return False
    
    def _copy_cuboid_folder(self, source_path: str, target_path: str):
        """复制cuboid文件夹"""
        try:
            # 获取EPCData的父目录
            epcdata_parent = os.path.dirname(os.path.dirname(source_path))
            cuboid_src = os.path.join(epcdata_parent, 'cuboid')
            
            if os.path.isdir(cuboid_src):
                # 计算cuboid目标路径 - 需要调整到正确的层级
                # 目标结构：日期\耳号\分数\具体文件夹
                # cuboid应该在：日期\耳号\cuboid
                target_parts = target_path.split(os.sep)
                if len(target_parts) >= 4:  # 确保有足够的层级
                    cuboid_dst = os.path.join(
                        target_parts[0],  # 根目录
                        target_parts[1],  # score
                        target_parts[2],  # 日期
                        target_parts[3],  # 耳号
                        'cuboid'
                    )
                    
                    if not os.path.exists(cuboid_dst):
                        shutil.copytree(cuboid_src, cuboid_dst, dirs_exist_ok=True)
                        print(f"📁 已复制cuboid文件夹到: {cuboid_dst}")
                    
        except Exception as e:
            print(f"⚠️ 复制cuboid文件夹失败: {e}")
    
    def create_score_structure(self):
        """创建新的score目录结构"""
        score_dir = os.path.join(self.root_dir, 'score')
        os.makedirs(score_dir, exist_ok=True)
        
        # 注意：具体的日期和耳号目录会在处理过程中动态创建
        # 这里只创建基础的score目录
        print("📁 创建score目录结构")
