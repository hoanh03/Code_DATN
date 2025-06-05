# string_utils.py

def concat(a: str, b: str) -> str:
    """Nối hai chuỗi và trả về kết quả.

    Tham số:
        a: Chuỗi thứ nhất
        b: Chuỗi thứ hai

    Trả về:
        Chuỗi đã được nối
    """

    return a + b

def substring(text: str, start: int, length: int) -> str:
    """Trích xuất một đoạn chuỗi từ chuỗi cho trước.

    Tham số:
        text: Chuỗi nguồn
        start: Vị trí bắt đầu (bắt đầu từ 0)
        length: Độ dài của đoạn chuỗi cần trích xuất

    Trả về:
        Đoạn chuỗi đã được trích xuất

    Gây lỗi:
        IndexError: Nếu `start` nhỏ hơn 0 hoặc vượt quá độ dài chuỗi
        ValueError: Nếu `length` là số âm
    """
    if start < 0 or start >= len(text):
        raise IndexError("Start index out of range")
    if length < 0:
        raise ValueError("Length cannot be negative")
    
    end = min(start + length, len(text))
    return text[start:end]

def get_char_at(text: str, index: int) -> str:
    """Lấy ký tự tại vị trí xác định.

    Tham số:
        text: Chuỗi nguồn
        index: Vị trí của ký tự cần lấy (bắt đầu từ 0)

    Trả về:
        Ký tự tại vị trí được chỉ định

    Gây lỗi:
        IndexError: Nếu `index` nằm ngoài phạm vi chuỗi
    """
    if index < 0 or index >= len(text):
        raise IndexError("Index out of range")
    
    return text[index]

def to_uppercase(text: str) -> str:
    """Chuyển chuỗi thành chữ hoa.

    Tham số:
        text: Chuỗi nguồn

    Trả về:
        Chuỗi đã chuyển thành chữ hoa
    """
    return text.upper()

def to_lowercase(text: str) -> str:
    """Chuyển chuỗi thành chữ thường.

    Tham số:
        text: Chuỗi nguồn

    Trả về:
        Chuỗi đã chuyển thành chữ thường
    """
    return text.lower()

def replace(text: str, old: str, new: str) -> str:
    """Thay thế tất cả các phần chuỗi con bằng một chuỗi con khác.

    Tham số:
        text: Chuỗi nguồn
        old: Chuỗi con cần thay thế
        new: Chuỗi con thay thế

    Trả về:
        Chuỗi sau khi đã thay thế
    """
    return text.replace(old, new)

def starts_with(text: str, prefix: str) -> bool:
    """Kiểm tra xem chuỗi có bắt đầu bằng tiền tố cho trước hay không.

    Tham số:
        text: Chuỗi nguồn
        prefix: Tiền tố cần kiểm tra

    Trả về:
        True nếu chuỗi bắt đầu bằng tiền tố, ngược lại False
    """
    return text.startswith(prefix)

def ends_with(text: str, suffix: str) -> bool:
    """Kiểm tra xem chuỗi có kết thúc bằng hậu tố cho trước hay không.

    Tham số:
        text: Chuỗi nguồn
        suffix: Hậu tố cần kiểm tra

    Trả về:
        True nếu chuỗi kết thúc bằng hậu tố, ngược lại False
    """
    return text.endswith(suffix)

def contains(text: str, substring: str) -> bool:
    """Kiểm tra xem chuỗi có chứa đoạn chuỗi con cho trước hay không.

    Tham số:
        text: Chuỗi nguồn
        substring: Đoạn chuỗi cần kiểm tra

    Trả về:
        True nếu chuỗi chứa đoạn chuỗi con, ngược lại False
    """
    return substring in text

def length(text: str) -> int:
    """Lấy độ dài của chuỗi.

    Tham số:
        text: Chuỗi nguồn

    Trả về:
        Độ dài của chuỗi
    """
    return len(text)

def trim(text: str) -> str:
    """Xóa khoảng trắng ở đầu và cuối chuỗi.

    Tham số:
        text: Chuỗi nguồn

    Trả về:
        Chuỗi sau khi đã xóa khoảng trắng thừa
    """
    return text.strip()