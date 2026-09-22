"""Constants for the Rust RCON integration."""
from datetime import timedelta

DOMAIN = "rust_rcon"
DEFAULT_PORT = 28016
SCAN_INTERVAL = timedelta(seconds=30)

SERVICE_SEND_COMMAND = "send_command"
SERVICE_SAY = "say"
ATTR_COMMAND = "command"
ATTR_MESSAGE = "message"
ATTR_ENTRY_ID = "entry_id"

OPT_CUSTOM_COMMANDS = "custom_commands"
