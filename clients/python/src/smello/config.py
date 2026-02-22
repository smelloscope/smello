"""Configuration for Smello client."""

from dataclasses import dataclass, field


@dataclass
class SmelloConfig:
    server_url: str
    capture_hosts: list[str] = field(default_factory=list)
    capture_all: bool = True
    ignore_hosts: list[str] = field(default_factory=list)
    redact_headers: list[str] = field(
        default_factory=lambda: ["authorization", "x-api-key"]
    )

    def should_capture(self, host: str) -> bool:
        """Decide whether to capture a request to the given host."""
        if host in self.ignore_hosts:
            return False
        if self.capture_all:
            return True
        return host in self.capture_hosts
