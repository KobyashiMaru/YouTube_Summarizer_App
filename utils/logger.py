import streamlit as st
import datetime
from enum import Enum

class LogLevel(Enum):
    INFO = "INFO"
    WARNING = "WARNING"
    CRITICAL = "CRITICAL"

class CriticalError(Exception):
    pass

class UILogger:
    def __init__(self):
        if "logs" not in st.session_state:
            st.session_state.logs = []
        self.container = None

    def set_container(self, container):
        self.container = container

    def log(self, message: str, level: LogLevel = LogLevel.INFO):
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] [{level.value}] {message}"
        st.session_state.logs.append(log_entry)
        
        print(log_entry) # Also print to terminal
        
        if self.container:
            self.container.code("\n".join(st.session_state.logs), language="text")

    def info(self, message: str):
        self.log(message, LogLevel.INFO)

    def warning(self, message: str):
        self.log(message, LogLevel.WARNING)

    def critical(self, message: str):
        self.log(message, LogLevel.CRITICAL)
        raise CriticalError(message)

    def get_logs(self):
        return "\n".join(st.session_state.logs)

    def clear(self):
        st.session_state.logs = []
        if self.container:
             self.container.empty()

# Global instance
logger = UILogger()
