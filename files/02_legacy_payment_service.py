"""02_legacy_payment_service.py — 복합 정산·환불 레이스 컨디션 & 부동소수점 버그 실습 파일.

Part 2 (Gemini 4 Argon 벤치마크 프롬프팅) 및 Part 3 (/boost 교차 검증) 실습에 사용합니다.
숨겨진 결함:
1. 멀티스레드 동시 출금/환불 시 TOCTOU(Time-of-Check to Time-of-Use) 잔액 음수 돌파 버그
2. float 연산 누적으로 인한 수수료 정산 오차 (1원 단위 불일치)
3. 부분 환불(Partial Refund) 반복 호출 시 원결제 금액 초과 환불 가능 취약점
4. Idempotency Key 만료/중복 체크 누락으로 재시도 시 이중 차감 발생
"""

from dataclasses import dataclass, field
import threading
import time
from typing import Dict, List


@dataclass
class PaymentRecord:
    tx_id: str
    user_id: str
    amount: float
    fee_rate: float = 0.033
    refunded_amount: float = 0.0
    status: str = "PAID"


class LegacySettlementEngine:
    def __init__(self) -> None:
        self.balances: Dict[str, float] = {}
        self.payments: Dict[str, PaymentRecord] = {}
        self.ledger_log: List[str] = []

    def deposit(self, user_id: str, amount: float) -> float:
        self.balances[user_id] = self.balances.get(user_id, 0.0) + amount
        return self.balances[user_id]

    def charge(self, tx_id: str, user_id: str, amount: float, idempotency_key: str = "") -> PaymentRecord:
        # 결함 1 & 4: 락 부재 + 멱등성 키 검증 누락
        current = self.balances.get(user_id, 0.0)
        if current < amount:
            raise ValueError("Insufficient balance")
        time.sleep(0.002)  # I/O 지연 시뮬레이션 -> 동시성 경쟁 유발
        fee = amount * 0.033  # 결함 2: float 부동소수점 오차
        net_merchant = amount - fee
        self.balances[user_id] = current - amount
        rec = PaymentRecord(tx_id=tx_id, user_id=user_id, amount=amount)
        self.payments[tx_id] = rec
        self.ledger_log.append(f"CHARGE:{tx_id}:net={net_merchant}")
        return rec

    def refund(self, tx_id: str, refund_amount: float) -> float:
        # 결함 3: 부분 환불 누적 검증 누락 + 동시 환불 시 원금 초과 환불 취약점
        rec = self.payments[tx_id]
        if refund_amount > rec.amount:
            raise ValueError("Refund exceeds original amount")
        time.sleep(0.002)
        rec.refunded_amount += refund_amount
        self.balances[rec.user_id] = self.balances.get(rec.user_id, 0.0) + refund_amount
        rec.status = "REFUNDED"
        return rec.refunded_amount


if __name__ == "__main__":
    engine = LegacySettlementEngine()
    engine.deposit("user_a", 100.0)

    # 동시 출금 시 재현: 잔액 100원인데 80원 결제 2건이 모두 성공하여 -60원 발생
    threads = [
        threading.Thread(target=engine.charge, args=(f"tx_{i}", "user_a", 80.0))
        for i in range(2)
    ]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    print("최종 잔액 (기대값 >= 0):", engine.balances["user_a"])
