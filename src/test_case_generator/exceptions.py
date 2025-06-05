# exceptions.py
# Chứa các lớp ngoại lệ và trình xử lý cho gói test_case_generator


import signal

class TimeoutException(Exception):
    """Ngoại lệ được kích hoạt khi một hàm thực thi vượt quá thời gian cho phép."""

    pass

def timeout_handler(signum, frame):
    """Trình xử lý tín hiệu cho các trường hợp vượt quá thời gian."""
    raise TimeoutException("Function execution timed out")