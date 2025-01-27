import asyncio
import websockets
from aiohttp import web
from collections import defaultdict
import threading

# Store text for each path dynamically
text_store = defaultdict(str)

# Track connected clients for each path
connected_clients = defaultdict(set)

# Timer to clear text after all clients disconnect
clear_text_timers = {}

# Function to clear the shared text for a path
def clear_shared_text(path):
    global text_store, clear_text_timers
    text_store[path] = ""
    print(f"Shared text cleared for path: {path}")
    clear_text_timers.pop(path, None)

# WebSocket handler
async def websocket_handler(websocket, path):
    global text_store, clear_text_timers

    # Add this client to the set for the path
    connected_clients[path].add(websocket)

    # Cancel the text clear timer if a new client connects
    if path in clear_text_timers:
        clear_text_timers[path].cancel()
        clear_text_timers.pop(path, None)

    try:
        # Send the current text for this path to the newly connected client
        await websocket.send(text_store[path])

        # Listen for changes from the client
        async for message in websocket:
            text_store[path] = message  # Update the shared text for the path
            print(f"Updated shared text for {path}: {text_store[path]}")

            # Broadcast the updated text to all connected clients for this path
            disconnected_clients = []
            for client in connected_clients[path]:
                try:
                    if client != websocket:  # Avoid echoing back to sender
                        await client.send(text_store[path])
                except websockets.ConnectionClosed:
                    disconnected_clients.append(client)

            # Remove disconnected clients
            for client in disconnected_clients:
                connected_clients[path].remove(client)

    except websockets.ConnectionClosed:
        print(f"Client disconnected from path: {path}")
    finally:
        connected_clients[path].discard(websocket)
        print(f"{len(connected_clients[path])} client(s) remaining on path: {path}")

        # If no clients are left, start the timer to clear text for this path
        if not connected_clients[path]:
            clear_text_timers[path] = threading.Timer(300, clear_shared_text, args=[path])
            clear_text_timers[path].start()

# Serve the static HTML file
async def handle_index(request):
    return web.FileResponse("index.html")

# Main function to start the servers
async def main():
    # Create an aiohttp app for serving static files
    app = web.Application()
    app.router.add_get("/{path:.*}", handle_index)  # Serve index.html for all paths

    # Start the HTTP server for static files
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", 8080)
    await site.start()

    print("HTTP server running on http://0.0.0.0:8080")

    # Start the WebSocket server with dynamic paths
    ws_server = await websockets.serve(websocket_handler, "0.0.0.0", 8765)
    print("WebSocket server running on ws://0.0.0.0:8765")

    # Keep the servers running
    try:
        await asyncio.Future()  # Keep running forever
    except asyncio.CancelledError:
        print("Server shutting down...")

if __name__ == "__main__":
    asyncio.run(main())

