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
    if path.lower().startswith('/ws'):
        path = path.lower()[3:]  # Remove the first 3 characters ("/ws")
    else:
        path = path.lower()

    # Ensure that the path is not empty
    if path == '':
        path = '/'
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

async def handle_request(request):
    # Normalize path and handle the '/ws' prefix
    raw_path = "/" + request.match_info['path'].strip("/").lower()

    # Adjust path to match how the WebSocket server handles paths
    if raw_path.startswith("/ws"):
        raw_path = raw_path[3:]  # Remove '/ws' prefix but keep leading slash
        if not raw_path.startswith("/"):
            raw_path = "/" + raw_path

    # Debug log to confirm the path
    print(f"REST request for normalized path: '{raw_path}'")

    query_text = request.query.get('text')
    get_text = request.query.get('get_text') == 'true'

    # Handle text retrieval
    if get_text:
        if raw_path not in text_store:
            text_store[raw_path] = ""  # Create the board dynamically if missing
        print(f"Returning text for path '{raw_path}': {text_store[raw_path]}")
        return web.Response(text=text_store[raw_path])

    # Handle text updates
    if query_text is not None:
        if raw_path not in text_store:
            text_store[raw_path] = ""
            print(f"Created new board for path: '{raw_path}'")

        text_store[raw_path] = query_text
        print(f"Text for path '{raw_path}' updated to: {text_store[raw_path]}")

        # Broadcast to WebSocket clients
        disconnected_clients = []
        for client in connected_clients[raw_path]:
            try:
                await client.send(text_store[raw_path])
            except websockets.ConnectionClosed:
                disconnected_clients.append(client)

        for client in disconnected_clients:
            connected_clients[raw_path].remove(client)

        return web.Response(text="Text updated successfully.")

    # Serve static files
    if raw_path.startswith("/static/"):
        file_path = os.path.join("static", raw_path[len("/static/"):])
        if os.path.exists(file_path) and os.path.isfile(file_path):
            return web.FileResponse(file_path)
        else:
            raise web.HTTPNotFound(text=f"Static file not found: {raw_path}")

    # Serve index.html for dynamic boards and root path
    print(f"Serving index.html for path: '{raw_path}'")
    return web.FileResponse("index.html")

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
