import asyncio
import websockets
from aiohttp import web
from collections import defaultdict
import threading
import os

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

# Serve static files and index.html as a fallback
async def handle_request(request):
    raw_path = request.match_info['path']
    print(f"Requested path: {raw_path}")

    # Handle static files
    if raw_path.startswith("static/"):
        file_path = os.path.join("static", raw_path[len("static/"):])
        print(f"Resolved static file path: {file_path}")

        if os.path.exists(file_path) and os.path.isfile(file_path):
            return web.FileResponse(file_path)
        else:
            # Static file not found, return 404
            raise web.HTTPNotFound(text=f"Static file not found: {raw_path}")

    # Serve index.html for all "virtual board" paths or root
    if raw_path == "" or not raw_path.startswith("static/"):
        print("Serving index.html for board")
        return web.FileResponse("index.html")

    # Fallback for any other unhandled case
    raise web.HTTPNotFound(text=f"Path not found: {raw_path}")



# Main function to start the servers
async def main():
    # Create an aiohttp app
    app = web.Application()

    # Use our custom handler for ALL GET requests
    app.router.add_get("/{path:.*}", handle_request)
    
    # Start the HTTP server for static files + boards
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", 8080)
    await site.start()

    print("HTTP server running on http://0.0.0.0:8080")

    # Start the WebSocket server
    ws_server = await websockets.serve(websocket_handler, "0.0.0.0", 8765)
    print("WebSocket server running on ws://0.0.0.0:8765")

    # Keep the servers running
    try:
        await asyncio.Future()  # run forever
    except asyncio.CancelledError:
        print("Server shutting down...")


if __name__ == "__main__":
    asyncio.run(main())

