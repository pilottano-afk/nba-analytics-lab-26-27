from dataclasses import dataclass

@dataclass
class CircuitBreaker:
    threshold: int = 3
    consecutive_failures: int = 0
    open: bool = False

    def record_success(self) -> None:
        self.consecutive_failures = 0
        self.open = False

    def record_failure(self) -> None:
        self.consecutive_failures += 1
        if self.consecutive_failures >= self.threshold:
            self.open = True

    def allow(self) -> bool:
        return not self.open
