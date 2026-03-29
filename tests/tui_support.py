from pathlib import Path


TEST_CONFIG = Path(__file__).resolve().parent / "config_example"


class DummyTUI:
    def __init__(self):
        self.notifications = []

    def notify(self, message, title=None, severity=None):
        self.notifications.append({"message": message, "title": title, "severity": severity})
