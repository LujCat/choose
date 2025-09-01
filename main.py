#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
YOLOv5 自动分类系统 - 主程序入口
"""

import os
import sys
from image_classifier import ImageClassifier


def check_environment():
    """检查运行环境"""
    print("🔍 检查运行环境...")
    
    # 检查Python版本
    python_version = sys.version_info
    print(f"🐍 Python版本: {python_version.major}.{python_version.minor}.{python_version.micro}")
    
    # 检查必要的包
    try:
        import onnxruntime as ort
        print(f"✅ ONNX Runtime版本: {ort.__version__}")
        
        # 检查可用的执行提供程序
        available_providers = ort.get_available_providers()
        print(f"🔍 可用的执行提供程序: {available_providers}")
        
        if 'CUDAExecutionProvider' in available_providers:
            print("🚀 CUDA支持: 可用")
        else:
            print("⚠️  CUDA支持: 不可用")
            
    except ImportError as e:
        print(f"❌ ONNX Runtime未安装: {e}")
        return False
    
    try:
        import cv2
        print(f"✅ OpenCV版本: {cv2.__version__}")
    except ImportError as e:
        print(f"❌ OpenCV未安装: {e}")
        return False
    
    try:
        import numpy as np
        print(f"✅ NumPy版本: {np.__version__}")
    except ImportError as e:
        print(f"❌ NumPy未安装: {e}")
        return False
    
    print("✅ 环境检查完成")
    return True


def check_model_files():
    """检查模型文件"""
    print("\n🔍 检查模型文件...")
    
    gpu_model = "gpu.onnx"
    cpu_model = "cpu.onnx"
    
    gpu_exists = os.path.exists(gpu_model)
    cpu_exists = os.path.exists(cpu_model)
    
    if gpu_exists:
        gpu_size = os.path.getsize(gpu_model) / (1024 * 1024)  # MB
        print(f"✅ GPU模型文件: {gpu_model} ({gpu_size:.1f} MB)")
    else:
        print(f"⚠️  GPU模型文件: {gpu_model} (不存在)")
    
    if cpu_exists:
        cpu_size = os.path.getsize(cpu_model) / (1024 * 1024)  # MB
        print(f"✅ CPU模型文件: {cpu_model} ({cpu_size:.1f} MB)")
    else:
        print(f"⚠️  CPU模型文件: {cpu_model} (不存在)")
    
    if not gpu_exists and not cpu_exists:
        print("❌ 未找到任何模型文件")
        print("请确保以下文件之一存在于项目根目录:")
        print(f"  - {gpu_model} (GPU加速)")
        print(f"  - {cpu_model} (CPU执行)")
        return False
    
    print("✅ 模型文件检查完成")
    return True


def main():
    """主函数"""
    print("=" * 60)
    print("🐷 YOLOv5 自动分类系统")
    print("=" * 60)
    print("功能：自动分类和整理图片文件")
    print()
    
    # 检查运行环境
    if not check_environment():
        print("\n❌ 环境检查失败，请安装必要的依赖包")
        print("运行: pip install -r requirements.txt")
        input("\n按回车键退出...")
        return
    
    # 检查模型文件
    if not check_model_files():
        input("\n按回车键退出...")
        return
    
    print("\n🚀 启动图像分类器...")
    
    try:
        # 创建图像分类器（会自动选择GPU或CPU模型）
        classifier = ImageClassifier()
        
        # 检查模型是否准备就绪
        if not classifier.is_ready():
            print("❌ 模型初始化失败")
            input("\n按回车键退出...")
            return
        
        # 显示模型信息
        model_info = classifier.model_manager.get_model_info()
        if model_info:
            print(f"\n📊 模型信息:")
            print(f"  模型文件: {model_info.get('model_path', 'Unknown')}")
            print(f"  执行提供程序: {model_info.get('provider', 'Unknown')}")
            print(f"  输入形状: {model_info.get('input_shape', 'Unknown')}")
            print(f"  输出形状: {model_info.get('output_shape', 'Unknown')}")
        
        # 获取用户输入的目录路径
        while True:
            print(f"\n📁 请输入要处理的根目录路径:")
            print("   注意：根目录应包含多个子目录，每个子目录下有EPCData文件夹")
            print("   例如：C:\\Data\\Images 或 /home/user/images")
            
            root_dir = input("\n路径: ").strip()
            
            # 去除引号
            if root_dir.startswith('"') and root_dir.endswith('"'):
                root_dir = root_dir[1:-1]
            elif root_dir.startswith("'") and root_dir.endswith("'"):
                root_dir = root_dir[1:-1]
            
            if not root_dir:
                print("❌ 路径不能为空")
                continue
            
            if not os.path.exists(root_dir):
                print(f"❌ 路径不存在: {root_dir}")
                continue
            
            if not os.path.isdir(root_dir):
                print(f"❌ 不是目录: {root_dir}")
                continue
            
            print(f"✅ 找到目录: {root_dir}")
            break
        
        # 开始处理
        print(f"\n🚀 开始处理目录: {root_dir}")
        print("=" * 60)
        
        classifier.process_directory(root_dir)
        
        print("\n🎉 所有操作完成！")
        
        # 询问是否打开结果文件夹
        score_dir = os.path.join(root_dir, 'score')
        if os.path.exists(score_dir):
            open_folder = input(f"\n是否打开结果文件夹 {score_dir}? (y/n): ").strip().lower()
            if open_folder in ['y', 'yes', '是']:
                try:
                    os.startfile(score_dir)  # Windows
                except AttributeError:
                    try:
                        import subprocess
                        subprocess.run(['open', score_dir])  # macOS
                    except FileNotFoundError:
                        subprocess.run(['xdg-open', score_dir])  # Linux
                    print(f"📂 已尝试打开文件夹: {score_dir}")
        
    except KeyboardInterrupt:
        print("\n\n⚠️  用户中断操作")
    except Exception as e:
        print(f"\n❌ 程序执行过程中发生错误: {e}")
        import traceback
        traceback.print_exc()
    
    input("\n按回车键退出...")


if __name__ == "__main__":
    main()
