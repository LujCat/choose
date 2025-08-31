#!/usr/bin/env python3
"""
YOLOv5 自动分类系统 - 主程序入口
"""

import os
from image_classifier import ImageClassifier

def get_root_directory():
    """获取用户输入的根目录"""
    root_dir = input("请输入根目录路径（包含EPCData文件夹）: ").strip()
    if not root_dir:
        root_dir = os.getcwd()
    return os.path.normpath(root_dir)

def check_model_file():
    """检查模型文件是否存在"""
    if not os.path.exists("gpu.onnx"):
        print("⚠️ 未找到 gpu.onnx 模型文件")
        return input("是否继续？(y/n): ").strip().lower() == 'y'
    return True

def main():
    """主程序入口"""
    print("=" * 50)
    print("🐷 YOLOv5 自动分类系统")
    print("=" * 50)
    
    # 获取根目录
    root_dir = get_root_directory()
    
    # 检查模型文件
    if not check_model_file():
        print("程序退出")
        return
    
    # 创建分类器并处理
    classifier = ImageClassifier()
    
    if classifier.is_ready():
        print(f"📂 开始处理目录: {root_dir}")
        classifier.process_directory(root_dir)
    else:
        print("❌ 模型加载失败，程序退出")

if __name__ == "__main__":
    main()
