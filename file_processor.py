import os
import shutil
from typing import Tuple, Dict
import re
import logging
from datetime import datetime

class FileProcessor:
    """文件处理器，负责文件复制和分类"""
    
    def __init__(self, root_dir: str):
        self.root_dir = root_dir
        self.ear_folder_counts = {}  # 记录每个耳号的文件夹数量
        
        # 设置日志
        self._setup_logging()
    
    def _setup_logging(self):
        """设置日志记录"""
        # 创建logs目录
        log_dir = "logs"
        os.makedirs(log_dir, exist_ok=True)
        
        # 生成日志文件名（包含时间戳）
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_filename = f"file_processing_{timestamp}.log"
        log_path = os.path.join(log_dir, log_filename)
        
        # 配置日志
        logging.basicConfig(
            level=logging.DEBUG,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_path, encoding='utf-8'),
                logging.StreamHandler()  # 同时输出到控制台
            ]
        )
        
        self.logger = logging.getLogger(__name__)
        self.logger.info(f"日志文件创建: {log_path}")
    
    def extract_folder_info(self, folder_name: str) -> Tuple[str, str]:
        """
        从文件夹名称提取耳号和日期信息
        
        Args:
            folder_name: 文件夹名称，如 "00000101-2025-06-22-13-57-51-584"
            
        Returns:
            (ear_number, date_str) 元组
        """
        # 解析文件夹名称格式：00000101-2025-06-22-13-57-51-584
        # 其中 101 是耳号，2025-06-22 是日期
        # 支持不同位数的耳号：00000010, 00000101, 000000123 等
        pattern = r'^0*(\d+)-(\d{4}-\d{2}-\d{2})-\d{2}-\d{2}-\d{2}-\d+$'
        match = re.match(pattern, folder_name)
        
        if match:
            ear_number = match.group(1)  # 耳号（去掉前导零）
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
        self.logger.info(f"处理图片文件夹: {folder_name}")
        self.logger.info(f"提取的耳号: {ear_number}")
        self.logger.info(f"提取的日期: {date_str}")
        self.logger.info(f"原始置信度: {confidence:.6f}")
        
        print(f"🔍 原始置信度: {confidence:.6f}")
        if confidence > 0.3:  # 阈值：0.3，过滤低质量检测
            score = int(confidence * 100)
            score_folder = str((score // 10) * 10)
            self.logger.info(f"置信度大于0.3，计算分数: {confidence:.2f} -> {score} -> {score_folder}")
            print(f"✅ 置信度: {confidence:.2f} -> {date_str}/{ear_number}/{score_folder}")
        else:
            score_folder = "undetected"
            self.logger.info(f"置信度小于等于0.3，标记为undetected: {confidence}")
            print("⏭️ 置信度过低，标记为undetected")
        
        # 构建目标路径：日期\耳号\分数\具体文件夹
        # 注意：undetected 也按照相同结构，只是不计入统计
        target = os.path.join(
            self.root_dir, 
            'score', 
            date_str,           # 日期
            ear_number,         # 耳号
            score_folder,       # 分数（包括undetected）
            folder_name         # 具体文件夹
        )
        
        self.logger.info(f"构建目标路径: {target}")
        self.logger.info(f"路径组件: 根目录={self.root_dir}, 日期={date_str}, 耳号={ear_number}, 分数={score_folder}, 文件夹={folder_name}")
        
        # 记录耳号文件夹数量（用于后续重命名）
        # 注意：只有非undetected的才计入统计
        if score_folder != "undetected":
            key = f"{date_str}_{ear_number}"
            if key not in self.ear_folder_counts:
                self.ear_folder_counts[key] = 0
            self.ear_folder_counts[key] += 1
            self.logger.info(f"计入统计: {key} -> {self.ear_folder_counts[key]}")
        else:
            self.logger.info(f"undetected文件夹不计入统计: {date_str}_{ear_number}")
        
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
        """复制cuboid文件夹到耳号目录"""
        try:
            # 从目标路径提取日期和耳号信息
            # 目标结构：root_dir/score/date/ear_number/score_folder/folder_name
            target_parts = target_path.split(os.sep)
            
            if len(target_parts) >= 5:  # 确保有足够的层级
                date_str = target_parts[-4]  # 日期
                ear_number = target_parts[-3]  # 耳号
                
                # 构建日期级别的cuboid源路径
                date_cuboid_src = os.path.join(
                    self.root_dir,
                    'score',
                    date_str,
                    'cuboid'
                )
                
                # 构建耳号级别的cuboid目标路径
                ear_cuboid_dst = os.path.join(
                    self.root_dir,
                    'score',
                    date_str,
                    ear_number,
                    'cuboid'
                )
                
                # 检查源cuboid文件夹是否存在
                if os.path.isdir(date_cuboid_src):
                    # 检查目标cuboid文件夹是否已存在
                    if not os.path.exists(ear_cuboid_dst):
                        shutil.copytree(date_cuboid_src, ear_cuboid_dst, dirs_exist_ok=True)
                        self.logger.info(f"已复制cuboid文件夹: {date_cuboid_src} -> {ear_cuboid_dst}")
                        print(f"📁 已复制cuboid文件夹到: {ear_cuboid_dst}")
                    else:
                        self.logger.info(f"cuboid文件夹已存在: {ear_cuboid_dst}")
                else:
                    self.logger.warning(f"源cuboid文件夹不存在: {date_cuboid_src}")
                    
        except Exception as e:
            self.logger.error(f"复制cuboid文件夹失败: {e}")
            print(f"⚠️ 复制cuboid文件夹失败: {e}")
    
    def create_score_structure(self):
        """创建新的score目录结构"""
        score_dir = os.path.join(self.root_dir, 'score')
        os.makedirs(score_dir, exist_ok=True)
        
        # 注意：具体的日期和耳号目录会在处理过程中动态创建
        # 这里只创建基础的score目录
        print("📁 创建score目录结构")
    
    def rename_ear_folders_with_count(self):
        """
        重命名耳号文件夹，添加数量信息
        将 耳号 重命名为 耳号-数量
        注意：只重命名包含有效检测结果的耳号文件夹
        """
        score_dir = os.path.join(self.root_dir, 'score')
        if not os.path.exists(score_dir):
            return
        
        print("\n🔄 开始重命名耳号文件夹，添加数量信息...")
        print("⚠️  注意：undetected文件夹中的耳号不会被重命名")
        
        for date_folder in os.listdir(score_dir):
            date_path = os.path.join(score_dir, date_folder)
            if not os.path.isdir(date_path) or date_folder == 'undetected':
                continue
            
            print(f"📅 处理日期: {date_folder}")
            
            for ear_folder in os.listdir(date_path):
                ear_path = os.path.join(date_path, ear_folder)
                if not os.path.isdir(ear_path):
                    continue
                
                # 检查是否是耳号文件夹（纯数字）
                if not ear_folder.isdigit():
                    continue
                
                # 计算该耳号下的有效点云文件夹数量（排除undetected和cuboid）
                folder_count = 0
                for score_item in os.listdir(ear_path):
                    score_item_path = os.path.join(ear_path, score_item)
                    if os.path.isdir(score_item_path) and score_item != 'cuboid' and score_item != 'undetected':
                        # 统计每个分数目录下的点云文件夹数量
                        for cloud_folder in os.listdir(score_item_path):
                            cloud_folder_path = os.path.join(score_item_path, cloud_folder)
                            if os.path.isdir(cloud_folder_path):
                                folder_count += 1
                
                # 重命名耳号文件夹
                if folder_count > 0:
                    new_name = f"{ear_folder}-{folder_count}"
                    new_path = os.path.join(date_path, new_name)
                    
                    try:
                        os.rename(ear_path, new_path)
                        print(f"  🏷️  {ear_folder} -> {new_name} ({folder_count} 个有效文件夹)")
                    except Exception as e:
                        print(f"  ❌ 重命名失败 {ear_folder}: {e}")
                else:
                    print(f"  ⚠️  {ear_folder}: 未找到有效文件夹")
        
        print("✅ 耳号文件夹重命名完成")
    
    def generate_statistics_report(self):
        """
        生成统计报告，统计不同数量区间的耳号文件夹数量
        并保存为txt文件
        注意：排除undetected文件夹，只统计有效检测的耳号
        """
        score_dir = os.path.join(self.root_dir, 'score')
        if not os.path.exists(score_dir):
            return
        
        print("\n📊 开始生成统计报告...")
        print("⚠️  注意：undetected文件夹中的耳号不计入统计")
        
        # 统计不同数量区间的耳号文件夹
        count_stats = {
            '>=2': 0,   # 大于等于2个文件夹的耳号数量（包括2、3、4、5...）
            '>=3': 0,   # 大于等于3个文件夹的耳号数量（包括3、4、5...）
            '>=4': 0,   # 大于等于4个文件夹的耳号数量（包括4、5...）
            '>=5': 0    # 大于等于5个文件夹的耳号数量（包括5...）
        }
        
        # 记录详细信息
        detailed_stats = {}
        
        for date_folder in os.listdir(score_dir):
            date_path = os.path.join(score_dir, date_folder)
            if not os.path.isdir(date_path) or date_folder == 'undetected':
                continue
            
            detailed_stats[date_folder] = {}
            
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
                    
                    # 统计不同区间（累加统计）
                    if folder_count >= 2:
                        count_stats['>=2'] += 1
                    if folder_count >= 3:
                        count_stats['>=3'] += 1
                    if folder_count >= 4:
                        count_stats['>=4'] += 1
                    if folder_count >= 5:
                        count_stats['>=5'] += 1
                    
                    # 记录详细信息
                    if ear_number not in detailed_stats[date_folder]:
                        detailed_stats[date_folder][ear_number] = folder_count
                    
                except ValueError:
                    continue
        
        # 生成报告内容
        report_content = self._format_statistics_report(count_stats, detailed_stats)
        
        # 保存为txt文件
        report_path = os.path.join(self.root_dir, 'statistics_report.txt')
        try:
            with open(report_path, 'w', encoding='utf-8') as f:
                f.write(report_content)
            print(f"📄 统计报告已保存到: {report_path}")
        except Exception as e:
            print(f"❌ 保存统计报告失败: {e}")
        
        return count_stats
    
    def _format_statistics_report(self, count_stats: Dict[str, int], detailed_stats: Dict) -> str:
        """格式化统计报告内容"""
        report_lines = []
        report_lines.append("=" * 60)
        report_lines.append("YOLOv5 自动分类系统 - 统计报告")
        report_lines.append("=" * 60)
        report_lines.append("")
        report_lines.append("📋 说明：本报告仅统计有效检测的耳号，undetected文件夹不计入统计")
        report_lines.append("")
        
        # 总体统计
        report_lines.append("📊 总体统计")
        report_lines.append("-" * 30)
        report_lines.append(f"大于等于2个文件夹的耳号数量: {count_stats['>=2']}")
        report_lines.append(f"大于等于3个文件夹的耳号数量: {count_stats['>=3']}")
        report_lines.append(f"大于等于4个文件夹的耳号数量: {count_stats['>=4']}")
        report_lines.append(f"大于等于5个文件夹的耳号数量: {count_stats['>=5']}")
        report_lines.append("")
        
        # 详细统计
        report_lines.append("📋 详细统计（按日期）")
        report_lines.append("-" * 30)
        
        for date in sorted(detailed_stats.keys()):
            report_lines.append(f"📅 日期: {date}")
            
            # 按文件夹数量排序
            sorted_ears = sorted(detailed_stats[date].items(), 
                               key=lambda x: x[1], reverse=True)
            
            for ear_number, folder_count in sorted_ears:
                report_lines.append(f"  🏷️  耳号 {ear_number}: {folder_count} 个有效文件夹")
            
            report_lines.append("")
        
        # 总结
        report_lines.append("🎯 总结")
        report_lines.append("-" * 30)
        total_ears = sum(len(ears) for ears in detailed_stats.values())
        report_lines.append(f"有效耳号数量: {total_ears}")
        report_lines.append(f"总日期数量: {len(detailed_stats)}")
        report_lines.append("")
        report_lines.append("=" * 60)
        
        return "\n".join(report_lines)
    
    def get_ear_folder_counts(self) -> Dict[str, int]:
        """获取耳号文件夹数量统计"""
        return self.ear_folder_counts.copy()
    
    def ensure_all_ears_have_cuboid(self):
        """确保所有耳号文件夹都有对应的cuboid文件夹"""
        score_dir = os.path.join(self.root_dir, 'score')
        if not os.path.exists(score_dir):
            return
        
        print("\n🔍 检查并确保所有耳号都有cuboid文件夹...")
        
        total_ears = 0
        missing_cuboid = 0
        copied_cuboid = 0
        existing_cuboid = 0
        
        # 遍历所有日期文件夹
        for date_folder in os.listdir(score_dir):
            date_path = os.path.join(score_dir, date_folder)
            
            # 跳过非目录或特殊目录
            if not os.path.isdir(date_path) or date_folder in ['cuboid', 'unknown']:
                continue
                
            print(f"📅 检查日期: {date_folder}")
            
            # 检查该日期下是否有cuboid文件夹
            date_cuboid_path = os.path.join(date_path, 'cuboid')
            if not os.path.exists(date_cuboid_path):
                print(f"  ⚠️  日期 {date_folder} 下没有cuboid文件夹，跳过")
                continue
                
            # 遍历日期下的耳号文件夹
            for ear_folder in os.listdir(date_path):
                ear_path = os.path.join(date_path, ear_folder)
                
                if not os.path.isdir(ear_path) or ear_folder == 'cuboid':
                    continue
                    
                total_ears += 1
                
                # 检查耳号文件夹下是否已有cuboid
                ear_cuboid_path = os.path.join(ear_path, 'cuboid')
                
                if os.path.exists(ear_cuboid_path):
                    existing_cuboid += 1
                    print(f"  ✅ {ear_folder}: 已有cuboid文件夹")
                else:
                    missing_cuboid += 1
                    print(f"  ❌ {ear_folder}: 缺少cuboid文件夹")
                    
                    # 复制cuboid文件夹
                    try:
                        shutil.copytree(date_cuboid_path, ear_cuboid_path)
                        copied_cuboid += 1
                        print(f"  ✅ {ear_folder}: 已复制cuboid文件夹")
                    except Exception as e:
                        print(f"  ❌ {ear_folder}: 复制失败 - {e}")
        
        # 输出统计结果
        print(f"\n📊 Cuboid文件夹统计:")
        print(f"  总耳号数量: {total_ears}")
        print(f"  已有cuboid的耳号: {existing_cuboid}")
        print(f"  缺少cuboid的耳号: {missing_cuboid}")
        print(f"  成功复制的cuboid: {copied_cuboid}")
        
        if copied_cuboid > 0:
            print(f"\n✅ 成功为 {copied_cuboid} 个耳号复制了cuboid文件夹")
