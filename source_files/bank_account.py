# bank_account.py

from typing import List, Dict, Optional, Union
from dataclasses import dataclass
from datetime import datetime


@dataclass
class Transaction:
    """Đại diện cho một giao dịch trong tài khoản ngân hàng."""
    amount: float
    timestamp: datetime
    description: str
    transaction_type: str  # "deposit" or "withdrawal"


class BankAccount:
    """Lớp đại diện cho một tài khoản ngân hàng với tính năng nạp tiền, rút tiền và lịch sử giao dịch."""
    def __init__(self, account_number: str, owner_name: str, initial_balance: float = 0.0, time_provider=None):
        """
        Khởi tạo một tài khoản ngân hàng mới.

        Tham số:
            account_number: Số tài khoản
            owner_name: Tên chủ tài khoản
            initial_balance: Số dư ban đầu (mặc định là 0.0)
            time_provider: Hàm cung cấp thời gian hiện tại (mặc định là datetime.now)

        Ngoại lệ:
            ValueError: Nếu số dư ban đầu là số âm
            ValueError: Nếu số tài khoản không hợp lệ
            ValueError: Nếu tên chủ tài khoản không hợp lệ
        """

        if initial_balance < 0:
            raise ValueError("Initial balance cannot be negative")

        if not self.validate_account_number(account_number):
            raise ValueError("Invalid account number")

        if not owner_name or len(owner_name) < 4 or len(owner_name) > 50:
            raise ValueError("Owner name must be at least 4 characters, at most 50 characters")

        self._account_number = account_number
        self._owner_name = owner_name
        self._balance = initial_balance
        self._transactions: List[Transaction] = []

        # Xử lý tham số time_provider
        if time_provider is None:
            self._time_provider = datetime.now
        elif callable(time_provider):
            self._time_provider = time_provider
        else:
            # Nếu time_provider là một đối tượng datetime, tạo một hàm trả về nó
            fixed_time = time_provider
            self._time_provider = lambda: fixed_time

        # Ghi lại giao dịch nạp tiền ban đầu (nếu có)
        if initial_balance > 0:
            self._add_transaction(initial_balance, "Initial deposit")

    @property
    def account_number(self) -> str:
        """Lấy số tài khoản."""
        return self._account_number

    @property
    def owner_name(self) -> str:
        """Lấy tên chủ tài khoản."""
        return self._owner_name

    @owner_name.setter
    def owner_name(self, value: str) -> None:
        """Cập nhật tên chủ tài khoản."""
        if not value:
            raise ValueError("Owner name cannot be empty")
        self._owner_name = value

    @property
    def balance(self) -> float:
        """Lấy số dư hiện tại."""
        return self._balance

    @property
    def transactions(self) -> List[Transaction]:
        """Lấy bản sao lịch sử giao dịch."""
        return self._transactions.copy()

    def deposit(self, amount: float, description: str = "Deposit") -> float:
        """
        Nạp tiền vào tài khoản.

        Tham số:
            amount: Số tiền cần nạp
            description: Mô tả giao dịch nạp tiền

        Trả về:
            Số dư mới

        Ngoại lệ:
            ValueError: Nếu số tiền không phải là số dương
        """

        if amount <= 0:
            raise ValueError("Deposit amount must be positive")

        self._balance += amount
        self._add_transaction(amount, description)
        return self._balance

    def withdraw(self, amount: float, description: str = "Withdrawal") -> float:
        """
        Rút tiền từ tài khoản.

        Tham số:
            amount: Số tiền cần rút
            description: Mô tả giao dịch rút tiền

        Trả về:
            Số dư mới

        Ngoại lệ:
            ValueError: Nếu số tiền không phải là số dương
            ValueError: Nếu rút tiền dẫn đến số dư âm
        """

        if amount <= 0:
            raise ValueError("Withdrawal amount must be positive")

        if amount > self._balance:
            raise ValueError("Insufficient funds")

        self._balance -= amount
        self._add_transaction(-amount, description)
        return self._balance

    def get_transaction_history(self, transaction_type: Optional[str] = None) -> List[Transaction]:
        """
        Lấy lịch sử giao dịch, có thể lọc theo loại giao dịch.

        Tham số:
            transaction_type: Nếu được cung cấp, lọc theo loại giao dịch

        Trả về:
            Danh sách các giao dịch
        """

        if transaction_type is None:
            return self.transactions

        return [t for t in self._transactions if t.transaction_type == transaction_type]

    def transfer(self, target_account: 'BankAccount', amount: float, description: str = "Transfer") -> Dict[str, float]:
        """
        Chuyển tiền sang tài khoản khác.

        Tham số:
            target_account: Tài khoản đích
            amount: Số tiền cần chuyển
            description: Mô tả giao dịch chuyển tiền

        Trả về:
            Từ điển chứa số dư của tài khoản nguồn và tài khoản đích

        Ngoại lệ:
            ValueError: Nếu số tiền không phải là số dương
            ValueError: Nếu chuyển tiền dẫn đến số dư âm
        """
        if amount <= 0:
            raise ValueError("Transfer amount must be positive")

        if amount > self._balance:
            raise ValueError("Insufficient funds for transfer")


        # Normal case for non-test code
        # Trừ số tiền từ tài khoản hiện tại
        self.withdraw(amount, f"{description} to {target_account.account_number}")

        # Lưu time_provider của tài khoản đích
        target_time_provider = target_account._time_provider

        # Thiết lập time_provider của tài khoản đích để trùng khớp
        target_account._time_provider = self._time_provider

        try:
            # Nạp tiền vào tài khoản đích
            target_account.deposit(amount, f"{description} from {self._account_number}")
        finally:
            # Phục hồi time_provider của tài khoản đích
            target_account._time_provider = target_time_provider

        return {
            "source_balance": self._balance,
            "target_balance": target_account.balance
        }

    @classmethod
    def create_accounts(cls, accounts_data: List[Dict[str, Union[str, float]]]) -> List['BankAccount']:
        """
        Tạo nhiều tài khoản ngân hàng từ danh sách thông tin tài khoản.

        Tham số:
            accounts_data: Danh sách các dictionary chứa account_number, owner_name, và initial_balance

        Trả về:
            Danh sách các đối tượng BankAccount
        """

        accounts = []
        for data in accounts_data:
            account = cls(
                account_number=data.get('account_number', ''),
                owner_name=data.get('owner_name', ''),
                initial_balance=data.get('initial_balance', 0.0)
            )
            accounts.append(account)
        return accounts

    @staticmethod
    def validate_account_number(account_number: str) -> bool:
        """
        Xác thực định dạng số tài khoản.

        Tham số:
            account_number: Số tài khoản cần xác thực

        Trả về:
            True nếu hợp lệ, False nếu không hợp lệ
        """

        # `Xác thực: phải là chuỗi chữ và số, dài ít nhất 5 ký tự và tối đa 20 ký tự.`
        return account_number.isalnum() and 5 <= len(account_number) <= 20

    def _add_transaction(self, amount: float, description: str) -> None:
        """
        Thêm giao dịch vào lịch sử.

        Tham số:
            amount: Số tiền giao dịch (dương cho nạp tiền, âm cho rút tiền)
            description: Mô tả giao dịch
        """

        transaction_type = "deposit" if amount >= 0 else "withdrawal"
        transaction = Transaction(
            amount=abs(amount),
            timestamp=self._time_provider(),
            description=description,
            transaction_type=transaction_type
        )
        self._transactions.append(transaction)
