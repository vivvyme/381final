import asyncio, sys
import streamlit as st
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from anthropic import Anthropic
from netmiko import ConnectHandler

MODEL = "claude-haiku-4-5"   # low-cost model

DEVICES = {
    "R1":  {"host": "192.168.100.1"},
    "R2":  {"host": "192.168.100.2"},
    "SW1": {"host": "192.168.100.3"},
}
CREDS = {"device_type": "cisco_ios", "username": "cisco",
         "password": "cisco", "secret": "cisco"}

SYSTEM = (
    "You inspect and configure a small Cisco lab (routers R1 and R2, switch "
    "SW1) from plain-English requests. The devices run classic IOS on CML; "
    "interfaces are named like Ethernet0/0. To change a device, call "
    "configure(device, config) with the exact IOS commands (no 'configure "
    "terminal'). To read state, use run_show_command with a 'show' command. "
    "After a change, verify it with a show command. Be precise with interface "
    "names and subnet masks."
)

# ---------------- Page 1: the agent ----------------
async def run_agent(question):
    """Run the agent once; return (steps, answer). steps = (tool, args, output)."""
    steps = []
    params = StdioServerParameters(command=sys.executable,
                                   args=["net_mcp_server.py"])
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            mcp_tools = (await session.list_tools()).tools
            tools = [{"name": t.name, "description": t.description or "",
                      "input_schema": t.inputSchema} for t in mcp_tools]
            client = Anthropic()
            messages = [{"role": "user", "content": question}]
            answer = ""
            while True:
                resp = client.messages.create(model=MODEL, max_tokens=1024,
                                               system=SYSTEM, messages=messages,
                                               tools=tools)
                if resp.stop_reason != "tool_use":
                    answer = "".join(b.text for b in resp.content
                                     if b.type == "text")
                    break
                messages.append({"role": "assistant", "content": resp.content})
                results = []
                for b in resp.content:
                    if b.type == "tool_use":
                        r = await session.call_tool(b.name, b.input)
                        out = r.content[0].text if r.content else ""
                        steps.append((b.name, b.input, out))
                        results.append({"type": "tool_result",
                                        "tool_use_id": b.id, "content": out})
                messages.append({"role": "user", "content": results})
    return steps, answer

def show_agent():
    st.title("Network Agent")
    st.write("Ask the agent to inspect or configure the lab (R1, R2, SW1) in plain English.")
    question = st.text_input("What do you want to do?",
                             placeholder="Give R2 a loopback 22 with IP 10.0.0.22/32")
    if st.button("Run") and question:
        with st.spinner("The agent is working..."):
            try:
                steps, answer = asyncio.run(run_agent(question))
            except Exception as e:
                st.error(f"Error: {e}")
                st.stop()
        if steps:
            st.subheader("What the agent did")
            for name, args, output in steps:
                st.write(f"Called `{name}` with `{args}`")
                # TODO (your turn): show the device output in an expander here
                with st.expander("Show output"):
                    st.code(output)
        st.subheader("Answer")
        st.write(answer)

# ---------------- Page 2: live dashboard ----------------
def pull_interfaces(device):
    conn = ConnectHandler(host=DEVICES[device]["host"], **CREDS)
    conn.enable()
    data = conn.send_command("show ip interface brief", use_textfsm=True)
    conn.disconnect()
    return data

def show_dashboard():
    st.title("Live Network Dashboard")
    st.write("Live interface status pulled from the real devices. Click Refresh to update.")
    st.button("Refresh")
    for device in DEVICES:
        st.subheader(device)
        try:
            data = pull_interfaces(device)
        except Exception as e:
            st.error(f"{device}: cannot reach device ({e})")
            continue
        if isinstance(data, list) and data:
            up = sum(1 for r in data if str(r.get("proto", "")).lower() == "up")
            st.metric("Interfaces up", f"{up} of {len(data)}")
            st.dataframe(data, use_container_width=True)
        else:
            st.code(data)

# ---------------- navigation ----------------
st.set_page_config(page_title="Network Tools", layout="wide")
page = st.sidebar.radio("Page", ["Network Agent", "Live Dashboard"])
if page == "Network Agent":
    show_agent()
else:
    show_dashboard()
