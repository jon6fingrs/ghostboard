import asyncio
import websockets
import sys
import re


def format_server_url(server_input):
    """
    Format the input server address to ensure it is a valid WebSocket URL.
    """
    # Check if the input is already a full WebSocket URL
    if server_input.startswith("ws://") or server_input.startswith("wss://"):
        return server_input

    # Check if a port is included in the address
    if ":" in server_input and not server_input.startswith("["):
        # IPv4 with port or domain with port
        if re.match(r"^\d{1,3}(\.\d{1,3}){3}:\d+$", server_input) or ":" in server_input.split(":")[-1]:
            return f"ws://{server_input}"  # Keep the existing port

    # Match an IP address (e.g., 192.168.1.1)
    ip_pattern = r"^\d{1,3}(\.\d{1,3}){3}$"
    if re.match(ip_pattern, server_input):
        return f"ws://{server_input}:8765"  # Default to ws:// with port 8765 for IPs

    # Assume it is a domain name
    return f"wss://{server_input}:443/ws"  # Default to wss:// with port 443 for domains



async def get_shared_text(server_url):
    """
    Retrieve the current shared text from the server.
    """
    try:
        async with websockets.connect(server_url) as websocket:
            # Wait for the server to send the shared text
            shared_text = await websocket.recv()
            print(shared_text)  # Print the text to stdout
    except Exception as e:
        print(f"Error connecting to the server: {e}", file=sys.stderr)


async def update_shared_text(server_url, new_text):
    """
    Update the shared text on the server.
    """
    try:
        async with websockets.connect(server_url) as websocket:
            # Send the new text to the server
            await websocket.send(new_text)
            print("Text updated successfully.")  # Confirm update to the user
    except Exception as e:
        print(f"Error connecting to the server: {e}", file=sys.stderr)


if __name__ == "__main__":
    if len(sys.argv) < 2 or len(sys.argv) > 3:
        print("Usage:", file=sys.stderr)
        print("  python3 text_client.py <server-address> [<new-text>|-]", file=sys.stderr)
        print("Examples:", file=sys.stderr)
        print("  Retrieve current text: python3 text_client.py 192.168.1.1", file=sys.stderr)
        print("  Update text: python3 text_client.py example.com \"New shared text\"", file=sys.stderr)
        print("  Update with file: cat text.txt | python3 text_client.py 192.168.1.1 -", file=sys.stderr)
        sys.exit(1)

    server_input = sys.argv[1]
    server_url = format_server_url(server_input)

    if len(sys.argv) == 2:
        # Retrieve the current text
        print(f"Connecting to: {server_url}", file=sys.stderr)
        asyncio.run(get_shared_text(server_url))
    elif len(sys.argv) == 3:
        # Update the shared text
        new_text = sys.argv[2]
        if new_text == "-":
            # Read from stdin if "-" is passed
            new_text = sys.stdin.read().strip()
        print(f"Connecting to: {server_url}", file=sys.stderr)
        asyncio.run(update_shared_text(server_url, new_text))

