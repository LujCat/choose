"""
配置文件 - 集中管理所有配置参数
"""

# 模型配置
MODEL_CONFIG = {
    'model_path': 'gpu.onnx',
    'confidence_threshold': 0.25,
    'input_size': (640, 640),
    'providers': ['CUDAExecutionProvider', 'CPUExecutionProvider']
}

# 文件配置
FILE_CONFIG = {
    'supported_extensions': ['.jpg', '.jpeg', '.png'],
    'target_folder_name': 'basicPoint',
    'score_folder_name': 'score',
    'undetected_folder_name': 'undetected',
    'cuboid_folder_name': 'cuboid'
}

# 目录配置
DIRECTORY_CONFIG = {
    'epcdata_folder_name': 'epcdata',
    'score_bin_size': 10,  # 分数区间大小
    'new_structure': True,  # 使用新的目录结构
    'folder_pattern': r'^000000(\d+)-(\d{4}-\d{2}-\d{2})-\d{2}-\d{2}-\d{2}-\d+$'
}

# 新的目录结构配置
STRUCTURE_CONFIG = {
    'root': 'score',
    'levels': ['date', 'ear_number', 'score', 'folder_name'],
    'date_format': 'YYYY-MM-DD',
    'ear_number_prefix': '000000'
}

# 日志配置
LOG_CONFIG = {
    'show_progress': True,
    'show_confidence': True,
    'show_file_operations': True,
    'show_structure_info': True
}
