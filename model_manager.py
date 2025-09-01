import os
import cv2
import numpy as np
import onnxruntime as ort
import logging
from datetime import datetime

class ModelManager:
    """ONNX模型管理器，负责模型加载和推理"""
    
    def __init__(self, gpu_model_path="gpu.onnx", cpu_model_path="cpu.onnx"):
        self.gpu_model_path = gpu_model_path
        self.cpu_model_path = cpu_model_path
        self.session = None
        self.input_name = None
        self.output_name = None
        self.provider_info = "Unknown"
        self.current_model_path = None
        
        # 设置日志
        self._setup_logging()
        
        self.load_model()
    
    def _setup_logging(self):
        """设置日志记录"""
        # 创建logs目录
        log_dir = "logs"
        os.makedirs(log_dir, exist_ok=True)
        
        # 生成日志文件名（包含时间戳）
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_filename = f"model_detection_{timestamp}.log"
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
    
    def load_model(self):
        """加载ONNX模型"""
        try:
            # 检查可用的执行提供程序
            available_providers = ort.get_available_providers()
            self.logger.info(f"可用的执行提供程序: {available_providers}")
            print(f"🔍 可用的执行提供程序: {available_providers}")
            
            # 尝试使用GPU (CUDA)
            if 'CUDAExecutionProvider' in available_providers:
                if os.path.exists(self.gpu_model_path):
                    try:
                        self.logger.info("尝试使用CUDA GPU加速...")
                        print("🚀 尝试使用CUDA GPU加速...")
                        self.logger.info(f"加载GPU模型: {self.gpu_model_path}")
                        print(f"📁 加载GPU模型: {self.gpu_model_path}")
                        
                        # 设置CUDA选项
                        cuda_options = {
                            'device_id': 0,
                            'arena_extend_strategy': 'kNextPowerOfTwo',
                            'gpu_mem_limit': 2 * 1024 * 1024 * 1024,  # 2GB
                            'cudnn_conv_use_max_workspace': '1',
                            'do_copy_in_default_stream': '1',
                        }
                        
                        self.session = ort.InferenceSession(
                            self.gpu_model_path, 
                            providers=[('CUDAExecutionProvider', cuda_options), 'CPUExecutionProvider']
                        )
                        self.provider_info = "CUDA GPU"
                        self.current_model_path = self.gpu_model_path
                        self.logger.info("成功使用CUDA GPU加速")
                        print("✅ 成功使用CUDA GPU加速")
                        
                    except Exception as e:
                        self.logger.warning(f"CUDA初始化失败，回退到CPU: {e}")
                        print(f"⚠️  CUDA初始化失败，回退到CPU: {e}")
                        self._fallback_to_cpu()
                else:
                    self.logger.warning(f"GPU模型文件不存在: {self.gpu_model_path}")
                    print(f"⚠️  GPU模型文件不存在: {self.gpu_model_path}")
                    self.logger.info("直接使用CPU模式")
                    print("🔄 直接使用CPU模式")
                    self._fallback_to_cpu()
            else:
                self.logger.info("CUDA不可用，使用CPU")
                print("ℹ️  CUDA不可用，使用CPU")
                self._fallback_to_cpu()
            
            if self.session is not None:
                # 获取输入输出信息
                self.input_name = self.session.get_inputs()[0].name
                self.output_name = self.session.get_outputs()[0].name
                
                input_shape = self.session.get_inputs()[0].shape
                self.logger.info(f"模型输入形状: {input_shape}")
                print(f"📊 模型输入形状: {input_shape}")
                self.logger.info(f"使用执行提供程序: {self.provider_info}")
                print(f"🎯 使用执行提供程序: {self.provider_info}")
                self.logger.info(f"当前模型文件: {self.current_model_path}")
                print(f"📁 当前模型文件: {self.current_model_path}")
            
        except Exception as e:
            self.logger.error(f"模型加载失败: {e}")
            print(f"❌ 模型加载失败: {e}")
            self.session = None
    
    def _fallback_to_cpu(self):
        """回退到CPU执行"""
        try:
            self.logger.info("回退到CPU执行...")
            print("🔄 回退到CPU执行...")
            
            # 优先使用cpu.onnx，如果不存在则使用gpu.onnx
            if os.path.exists(self.cpu_model_path):
                self.logger.info(f"加载CPU模型: {self.cpu_model_path}")
                print(f"📁 加载CPU模型: {self.cpu_model_path}")
                model_path = self.cpu_model_path
            elif os.path.exists(self.gpu_model_path):
                self.logger.info(f"使用GPU模型作为CPU模型: {self.gpu_model_path}")
                print(f"📁 使用GPU模型作为CPU模型: {self.gpu_model_path}")
                model_path = self.gpu_model_path
            else:
                self.logger.error("未找到任何模型文件")
                print("❌ 未找到任何模型文件")
                return
            
            self.session = ort.InferenceSession(
                model_path, 
                providers=['CPUExecutionProvider']
            )
            self.provider_info = "CPU"
            self.current_model_path = model_path
            self.logger.info("成功使用CPU执行")
            print("✅ 成功使用CPU执行")
            
        except Exception as e:
            self.logger.error(f"CPU回退也失败: {e}")
            print(f"❌ CPU回退也失败: {e}")
            self.session = None
    
    def detect_image(self, image_path: str) -> float:
        """
        检测图片中的目标
        
        Args:
            image_path: 图片文件路径
            
        Returns:
            检测置信度 (0.0-1.0)
        """
        if not self.is_ready():
            self.logger.error("模型未准备就绪")
            print("❌ 模型未准备就绪")
            return 0.0
        
        try:
            self.logger.info(f"开始检测图片: {image_path}")
            
            # 读取图片
            image = cv2.imread(image_path)
            if image is None:
                self.logger.error(f"无法读取图片: {image_path}")
                print(f"❌ 无法读取图片: {image_path}")
                return 0.0
            
            self.logger.info(f"图片读取成功，尺寸: {image.shape}")
            
            # 预处理图片
            input_data = self._preprocess_image(image)
            self.logger.info(f"图片预处理完成，输入数据形状: {input_data.shape}")
            
            # 执行推理
            self.logger.info("开始执行模型推理...")
            outputs = self.session.run([self.output_name], {self.input_name: input_data})
            self.logger.info(f"推理完成，输出数量: {len(outputs)}")
            
            # 解析输出
            confidence = self._parse_output(outputs[0])
            self.logger.info(f"最终置信度: {confidence}")
            
            return confidence
            
        except Exception as e:
            self.logger.error(f"检测失败: {e}")
            print(f"❌ 检测失败: {e}")
            return 0.0
    
    def _preprocess_image(self, image):
        """预处理图片"""
        try:
            # 调整图片大小到模型输入尺寸
            input_size = (640, 640)  # YOLOv5标准输入尺寸
            resized = cv2.resize(image, input_size)
            
            # 转换为RGB格式
            rgb = cv2.cvtColor(resized, cv2.COLOR_BGR2RGB)
            
            # 归一化到0-1范围
            normalized = rgb.astype(np.float32) / 255.0
            
            # 添加batch维度并转换为NCHW格式
            input_data = np.transpose(normalized, (2, 0, 1))
            input_data = np.expand_dims(input_data, axis=0)
            
            return input_data
            
        except Exception as e:
            print(f"❌ 图片预处理失败: {e}")
            raise
    
    def _parse_output(self, output):
        """解析模型输出"""
        try:
            self.logger.info(f"开始解析模型输出...")
            self.logger.info(f"模型输出形状: {output.shape}")
            self.logger.info(f"模型输出数据类型: {output.dtype}")
            self.logger.info(f"模型输出内容: {output}")
            
            print(f"🔍 模型输出形状: {output.shape}")
            print(f"🔍 模型输出内容: {output}")
            
            # 获取最高置信度
            if len(output.shape) == 3:  # 标准YOLOv5输出格式
                # 输出形状: [1, num_detections, 6] (x1, y1, x2, y2, confidence, class)
                self.logger.info("检测到3D输出格式，按标准YOLOv5格式解析")
                confidences = output[0, :, 4]  # 提取置信度列
                if len(confidences) > 0:
                    max_confidence = np.max(confidences)
                    min_confidence = np.min(confidences)
                    self.logger.info(f"3D输出 - 置信度数组: {confidences}")
                    self.logger.info(f"3D输出 - 最大置信度: {max_confidence}")
                    self.logger.info(f"3D输出 - 最小置信度: {min_confidence}")
                    self.logger.info(f"3D输出 - 置信度范围: [{min_confidence}, {max_confidence}]")
                    print(f"🔍 3D输出 - 置信度数组: {confidences}")
                    print(f"🔍 3D输出 - 最大置信度: {max_confidence}")
                    return float(max_confidence)
                else:
                    self.logger.warning("3D输出格式但置信度数组为空")
            elif len(output.shape) == 2:  # 简化输出格式
                # 输出形状: [num_detections, 5] (x1, y1, x2, y2, confidence)
                self.logger.info("检测到2D输出格式，按简化格式解析")
                confidences = output[:, 4]
                if len(confidences) > 0:
                    max_confidence = np.max(confidences)
                    min_confidence = np.min(confidences)
                    self.logger.info(f"2D输出 - 置信度数组: {confidences}")
                    self.logger.info(f"2D输出 - 最大置信度: {max_confidence}")
                    self.logger.info(f"2D输出 - 最小置信度: {min_confidence}")
                    self.logger.info(f"2D输出 - 置信度范围: [{min_confidence}, {max_confidence}]")
                    print(f"🔍 2D输出 - 置信度数组: {confidences}")
                    print(f"🔍 2D输出 - 最大置信度: {max_confidence}")
                    return float(max_confidence)
                else:
                    self.logger.warning("2D输出格式但置信度数组为空")
            else:
                self.logger.warning(f"未知输出格式，形状: {output.shape}")
            
            self.logger.warning("未找到有效置信度，返回0.0")
            print("🔍 未找到有效置信度，返回0.0")
            return 0.0
            
        except Exception as e:
            self.logger.error(f"输出解析失败: {e}")
            print(f"❌ 输出解析失败: {e}")
            return 0.0
    
    def is_ready(self) -> bool:
        """检查模型是否准备就绪"""
        return self.session is not None and self.input_name is not None and self.output_name is not None
    
    def get_provider_info(self) -> str:
        """获取当前使用的执行提供程序信息"""
        return self.provider_info
    
    def get_model_info(self) -> dict:
        """获取模型信息"""
        if not self.is_ready():
            return {}
        
        try:
            input_info = self.session.get_inputs()[0]
            output_info = self.session.get_outputs()[0]
            
            return {
                'model_path': self.current_model_path,
                'provider': self.provider_info,
                'input_shape': input_info.shape,
                'input_type': input_info.type,
                'output_shape': output_info.shape,
                'output_type': output_info.type
            }
        except Exception as e:
            print(f"❌ 获取模型信息失败: {e}")
            return {}
