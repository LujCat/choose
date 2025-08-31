import os
import cv2
import numpy as np
import onnxruntime as ort

class ModelManager:
    """ONNX模型管理器，负责模型加载和推理"""
    
    def __init__(self, model_path="gpu.onnx"):
        self.model_path = model_path
        self.session = None
        self.input_name = None
        self.output_name = None
        self.load_model()
    
    def load_model(self):
        """加载ONNX模型"""
        if not os.path.exists(self.model_path):
            print(f"❌ 模型文件不存在: {self.model_path}")
            return False
        
        try:
            # 优先使用GPU，失败则使用CPU
            providers = ['CUDAExecutionProvider', 'CPUExecutionProvider']
            for provider in providers:
                try:
                    self.session = ort.InferenceSession(self.model_path, providers=[provider])
                    print(f"✅ 使用{provider}执行")
                    break
                except:
                    continue
            
            if self.session:
                self.input_name = self.session.get_inputs()[0].name
                self.output_name = self.session.get_outputs()[0].name
                return True
        except Exception as e:
            print(f"❌ 加载模型失败: {e}")
        return False
    
    def detect_image(self, image_path):
        """检测单张图片的置信度"""
        if not self.session or not os.path.exists(image_path):
            return 0.0
        
        try:
            # 读取和预处理图片
            img = cv2.imread(image_path)
            if img is None:
                return 0.0
            
            # 调整图片尺寸和格式
            img_input = cv2.resize(img, (640, 640)).astype(np.float32) / 255.0
            img_input = img_input.transpose(2, 0, 1)[np.newaxis, ...]
            
            # 模型推理
            outputs = self.session.run([self.output_name], {self.input_name: img_input})
            detections = outputs[0][0]
            
            # 获取最高置信度
            valid_detections = [d[4] for d in detections if d[4] > 0.25]
            return max(valid_detections) if valid_detections else 0.0
            
        except Exception as e:
            print(f"检测失败 {image_path}: {e}")
            return 0.0
    
    def is_ready(self):
        """检查模型是否已准备就绪"""
        return self.session is not None
