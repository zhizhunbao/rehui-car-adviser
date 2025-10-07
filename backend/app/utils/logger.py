import logging
import os
import inspect
import threading

class KeyPointLogger:
    """关键部位日志器 - 只在关键部位记录日志"""
    
    def __init__(self):
        self.sequence_counter = 0
        self.lock = threading.Lock()
        self.logger = self._setup_logger()
    
    def _setup_logger(self):
        """设置日志器"""
        # 获取当前文件所在目录的父目录（backend目录）
        current_dir = os.path.dirname(os.path.abspath(__file__))
        backend_dir = os.path.dirname(current_dir)
        logs_dir = os.path.join(backend_dir, 'logs')
        os.makedirs(logs_dir, exist_ok=True)
        
        logger = logging.getLogger('key_points')
        logger.setLevel(logging.INFO)
        
        # 清除现有处理器，避免重复
        logger.handlers.clear()
        
        # 文件处理器
        log_file_path = os.path.join(logs_dir, 'app.log')
        file_handler = logging.FileHandler(log_file_path, encoding='utf-8')
        formatter = logging.Formatter('%(asctime)s | %(sequence)s | %(call_stack)s | %(message)s')
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        
        # 控制台处理器
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
        
        return logger
    
    def _get_next_sequence(self):
        """获取下一个执行序号"""
        with self.lock:
            self.sequence_counter += 1
            return str(self.sequence_counter)
    
    def _get_call_stack(self):
        """获取调用栈信息"""
        frame = inspect.currentframe().f_back.f_back
        module_name = frame.f_globals.get('__name__', 'unknown')
        function_name = frame.f_code.co_name
        line_number = frame.f_lineno
        
        # 处理模块路径
        if module_name.startswith('app.'):
            package_path = module_name
        else:
            package_path = f"app.{module_name}"
        
        return f"{package_path}.{function_name}:{line_number}"

    def log_result(self, conclusion: str, reason: str = ""):
        """只在关键部位记录日志"""
        sequence = self._get_next_sequence()
        call_stack = self._get_call_stack()

        if reason:
            message = f"{conclusion} - {reason}"
        else:
            message = conclusion

        self.logger.info(message, extra={
            'sequence': sequence,
            'call_stack': call_stack
        })


# 全局实例
logger = KeyPointLogger()


# 兼容性函数
def get_logger(name: str = "key_points"):
    """获取日志器实例（保持向后兼容）"""
    return logger