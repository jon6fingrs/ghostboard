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

# Preprogrammed text for the demo
DEMO_TEXT = """This is a preprogrammed Ghostboard demonstration.
No user input is allowed, but you can watch it sync across devices in real time!
"""

# Keep track of typing tasks so we can cancel them if needed (e.g., Clear).
demo_tasks = {}

# Function to clear the shared text for a path
def clear_shared_text(path):
    global text_store, clear_text_timers
    text_store[path] = ""
    print(f"Shared text cleared for path: {path}")
    clear_text_timers.pop(path, None)

async def type_demo_message(path):
    """
    Gradually "type" out DEMO_TEXT for this path,
    sending partial updates to all WebSocket clients.
    """
    global text_store, connected_clients, DEMO_TEXT, demo_tasks

    # Start from blank
    text_store[path] = ""

    try:
        for i in range(len(DEMO_TEXT) + 1):
            # Check if this task was canceled
            await asyncio.sleep(0.05)  # "Typing" delay
            text_store[path] = DEMO_TEXT[:i]

            # Broadcast the updated text
            disconnected_clients = []
            for client in connected_clients[path]:
                try:
                    await client.send(text_store[path])
                except websockets.ConnectionClosed:
                    disconnected_clients.append(client)

            for dc in disconnected_clients:
                connected_clients[path].remove(dc)
    except asyncio.CancelledError:
        print(f"Typing task for path '{path}' was canceled.")
    finally:
        # Remove reference from dict if still present
        if path in demo_tasks:
            if demo_tasks[path] is asyncio.current_task():
                demo_tasks.pop(path, None)

async def clear_demo(path):
    """
    Clear the text_store for the path and cancel the typing task (if any).
    Broadcast the empty text to clients.
    """
    global text_store, connected_clients, demo_tasks

    # Cancel typing task if it exists
    if path in demo_tasks:
        task = demo_tasks[path]
        if not task.done():
            task.cancel()
        demo_tasks.pop(path, None)

    # Clear text
    text_store[path] = ""

    # Broadcast empty text
    disconnected_clients = []
    for client in connected_clients[path]:
        try:
            await client.send("")
        except websockets.ConnectionClosed:
            disconnected_clients.append(client)

    for dc in disconnected_clients:
        connected_clients[path].remove(dc)

    print(f"Cleared demo text for path '{path}'")

# WebSocket handler (demo version: ignore all inbound messages => read-only)
async def websocket_handler(websocket, path):
    global text_store, clear_text_timers

    # Normalize the path
    if path.lower().startswith('/ws'):
        path = path.lower()[3:]
    else:
        path = path.lower()
    if path == '':
        path = '/'

    connected_clients[path].add(websocket)

    # Cancel clear timer if present
    if path in clear_text_timers:
        clear_text_timers[path].cancel()
        clear_text_timers.pop(path, None)

    try:
        # Send current text upon connection
        await websocket.send(text_store[path])

        # Ignore all inbound messages (demo is read-only)
        async for message in websocket:
            print(f"Ignoring inbound message on path {path}: {message}")

    except websockets.ConnectionClosed:
        print(f"Client disconnected from path: {path}")

    finally:
        connected_clients[path].discard(websocket)
        print(f"{len(connected_clients[path])} client(s) remaining on path: {path}")

        # If no clients remain, set up the clearing timer
        if not connected_clients[path]:
            clear_text_timers[path] = threading.Timer(300, clear_shared_text, args=[path])
            clear_text_timers[path].start()

async def handle_request(request):
    raw_path = "/" + request.match_info['path'].strip("/").lower()

    # Adjust path to match WebSocket path logic
    if raw_path.startswith("/ws"):
        raw_path = raw_path[3:]
        if not raw_path.startswith("/"):
            raw_path = "/" + raw_path

    print(f"REST request for path: '{raw_path}'")

    # Check if we should start the demo
    if request.query.get('start_demo', 'false').lower() == 'true':
        print(f"Starting demo on path: {raw_path}")
        # If there's an existing typing task, cancel it first
        if raw_path in demo_tasks:
            old_task = demo_tasks[raw_path]
            if not old_task.done():
                old_task.cancel()
            demo_tasks.pop(raw_path, None)

        # Create & store new typing task
        new_task = asyncio.create_task(type_demo_message(raw_path))
        demo_tasks[raw_path] = new_task
        return web.Response(text=f"Demo started on {raw_path}.")

    # Check if we should clear the text (and cancel the demo)
    if request.query.get('clear', 'false').lower() == 'true':
        print(f"Clearing demo on path: {raw_path}")
        asyncio.create_task(clear_demo(raw_path))
        return web.Response(text=f"Demo cleared on {raw_path}.")

    # For POST requests, do nothing (read-only)
    if request.method == "POST":
        return web.Response(text="This demo is read-only.", status=403)

    # Handle text retrieval via GET param ?get_text=true
    get_text = request.query.get('get_text') == 'true'
    if get_text:
        if raw_path not in text_store:
            text_store[raw_path] = ""
        return web.Response(text=text_store[raw_path])

    # Serve static files if you have them
    if raw_path.startswith("/static/"):
        file_path = os.path.join("static", raw_path[len("/static/"):])
        if os.path.exists(file_path) and os.path.isfile(file_path):
            return web.FileResponse(file_path)
        else:
            raise web.HTTPNotFound(text=f"Static file not found: {raw_path}")

    # Serve index.html (the read-only demo version)
    return web.FileResponse("index.html")

async def main():
    # Create an aiohttp app
    app = web.Application()
    app.router.add_get("/{path:.*}", handle_request)
    app.router.add_post("/{path:.*}", handle_request)

    # Start HTTP server on port 8080
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", 8080)
    await site.start()
    print("HTTP server running on http://0.0.0.0:8080")

    # Start the WebSocket server on port 8765
    ws_server = await websockets.serve(websocket_handler, "0.0.0.0", 8765)
    print("WebSocket server running on ws://0.0.0.0:8765")

    try:
        await asyncio.Future()  # run forever
    except asyncio.CancelledError:
        print("Server shutting down...")

if __name__ == "__main__":
    asyncio.run(main())
