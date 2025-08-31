import os
from typing import List, Tuple

class FileScanner:
    """文件扫描器，负责查找符合条件的图片文件"""
    
    def __init__(self, supported_extensions=None):
        if supported_extensions is None:
            supported_extensions = ['.jpg', '.jpeg', '.png']
        self.supported_extensions = supported_extensions
    
    def scan_for_images(self, root_dir: str) -> List[Tuple[str, str]]:
        """
        扫描目录中的图片文件
        
        Args:
            root_dir: 根目录路径，包含多个子目录，每个子目录下有EPCData
            
        Returns:
            List of (image_path, folder_path) tuples
        """
        if not os.path.exists(root_dir):
            print("❌ 路径不存在")
            return []
        
        image_files = []
        
        # 首先获取根目录下的所有子目录
        sub_dirs = []
        for item in os.listdir(root_dir):
            item_path = os.path.join(root_dir, item)
            if os.path.isdir(item_path) and not item.startswith('.'):
                sub_dirs.append(item_path)
        
        print(f"📂 在根目录下找到 {len(sub_dirs)} 个子目录")
        
        # 在每个子目录中查找EPCData
        for sub_dir in sub_dirs:
            sub_dir_name = os.path.basename(sub_dir)
            print(f"🔍 扫描子目录: {sub_dir_name}")
            
            # 在子目录中查找EPCData文件夹
            epcdata_path = os.path.join(sub_dir, 'EPCData')
            if os.path.isdir(epcdata_path):
                print(f"  ✅ 找到EPCData文件夹")
                
                # 在EPCData中查找图片文件夹
                for item in os.listdir(epcdata_path):
                    item_path = os.path.join(epcdata_path, item)
                    if os.path.isdir(item_path):
                        img_path = self._find_basic_point_image(item_path)
                        if img_path:
                            # 记录完整的文件夹路径（从根目录开始）
                            image_files.append((img_path, item_path))
                            print(f"    📁 找到图片文件夹: {item}")
            else:
                print(f"  ⚠️  未找到EPCData文件夹")
        
        return image_files
    
    def _find_basic_point_image(self, folder_path: str) -> str:
        """
        在指定文件夹中查找basicPoint图片
        
        Args:
            folder_path: 文件夹路径
            
        Returns:
            图片文件路径，如果未找到则返回空字符串
        """
        for ext in self.supported_extensions:
            img_path = os.path.join(folder_path, f"basicPoint{ext}")
            if os.path.isfile(img_path):
                return img_path
        return ""
    
    def get_folder_count(self, root_dir: str) -> int:
        """获取符合条件的文件夹数量"""
        return len(self.scan_for_images(root_dir))
    
    def get_directory_structure(self, root_dir: str) -> dict:
        """
        获取目录结构信息
        
        Args:
            root_dir: 根目录路径
            
        Returns:
            目录结构字典
        """
        structure = {}
        
        if not os.path.exists(root_dir):
            return structure
        
        for item in os.listdir(root_dir):
            item_path = os.path.join(root_dir, item)
            if os.path.isdir(item_path) and not item.startswith('.'):
                epcdata_path = os.path.join(item_path, 'EPCData')
                if os.path.isdir(epcdata_path):
                    structure[item] = {
                        'path': item_path,
                        'epcdata_path': epcdata_path,
                        'sub_folders': []
                    }
                    
                    # 获取EPCData下的子文件夹
                    for sub_item in os.listdir(epcdata_path):
                        sub_item_path = os.path.join(epcdata_path, sub_item)
                        if os.path.isdir(sub_item_path):
                            structure[item]['sub_folders'].append(sub_item)
        
        return structure
