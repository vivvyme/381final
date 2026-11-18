from mcp.server.fastmcp import FastMCP
from netmiko import ConnectHandler

mcp = FastMCP("net-tools")

DEVICES = {
    "R1":  {"host": "192.168.100.1"},
    "R2":  {"host": "192.168.100.2"},
    "SW1": {"host": "192.168.100.3"},
}
CREDS = {"device_type": "cisco_ios", "username": "cisco",
         "password": "cisco", "secret": "cisco"}

def _connect(device):
    return ConnectHandler(host=DEVICES[device]["host"], **CREDS)

# ---------- read ----------
@mcp.tool()
def list_devices() -> str:
    """List the network devices this server can reach."""
    return ", ".join(DEVICES)

@mcp.tool()
def run_show_command(device: str, command: str) -> str:
    """Run a 'show' command on a device (R1, R2, SW1) and return its output."""
    if device not in DEVICES:
        return f"Unknown device '{device}'."
    if not command.strip().startswith("show"):
        return "run_show_command only runs 'show' commands."
    conn = _connect(device)
    conn.enable()
    out = conn.send_command(command)
    conn.disconnect()
    return out

# ---------- write ----------
@mcp.tool()
def configure(device: str, config: str) -> str:
    """Apply IOS configuration to a device. 'config' is one or more IOS config
    commands separated by newlines, exactly as typed in config mode (do not
    include 'configure terminal'). Example: 'interface Loopback22\\n ip address
    10.0.0.22 255.255.255.255\\n no shutdown'. Returns the device output."""
    if device not in DEVICES:
        return f"Unknown device '{device}'."
    conn = _connect(device)
    conn.enable()
    out = conn.send_config_set(config.splitlines())
    conn.disconnect()
    return out

@mcp.tool()
def save_config(device: str) -> str:
    """Save the running config to startup (write memory) on a device."""
    if device not in DEVICES:
        return f"Unknown device '{device}'."
    conn = _connect(device)
    conn.enable()
    out = conn.save_config()
    conn.disconnect()
    return out

if __name__ == "__main__":
    mcp.run(transport="stdio")
