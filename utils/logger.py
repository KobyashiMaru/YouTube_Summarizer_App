import streamlit as st
import datetime
from enum import Enum

class LogLevel(Enum):
    INFO = "INFO"
    WARNING = "WARNING"
    CRITICAL = "CRITICAL"

class UILogger:
    def __init__(self):
        if "logs" not in st.session_state:
            st.session_state.logs = []

    def log(self, message: str, level: LogLevel = LogLevel.INFO):
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] [{level.value}] {message}"
        st.session_state.logs.append(log_entry)
        # Force a rerun to update the UI only if running in a callback? 
        # No, Streamlit reruns on interaction. We might need a container to update dynamically if using st.empty()
        print(log_entry) # Also print to terminal

    def info(self, message: str):
        self.log(message, LogLevel.INFO)

    def warning(self, message: str):
        self.log(message, LogLevel.WARNING)

    def critical(self, message: str):
        self.log(message, LogLevel.CRITICAL)

    def get_logs(self):
        return "\n".join(st.session_state.logs)

    def clear(self):
        st.session_state.logs = []

# Global instance
logger = UILogger()
