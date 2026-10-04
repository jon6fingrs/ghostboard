import asyncio
import os
from collections import defaultdict

from aiohttp import web
from websockets.asyncio.server import serve, broadcast
from websockets.exceptions import ConnectionClosed

# Largest message/POST body accepted (default 16 MiB). The library defaults of
# 1 MiB caused large pastes to drop the WebSocket connection.
MAX_TEXT_SIZE = int(os.environ.get("GHOSTBOARD_MAX_TEXT_SIZE", 16 * 1024 * 1024))

# Seconds to keep a board's text after its last client disconnects
CLEAR_DELAY = int(os.environ.get("GHOSTBOARD_CLEAR_DELAY", 300))

# Store text for each path dynamically
text_store = defaultdict(str)

# Track connected clients for each path
connected_clients = defaultdict(set)

# Timer to clear text after all clients disconnect
clear_text_timers = {}


def normalize_path(path):
    """Lowercase, strip the '/ws' prefix, and ensure a leading slash."""
    path = "/" + path.strip("/").lower()
    if path.startswith("/ws"):
        path = "/" + path[3:].lstrip("/")
    return path


def preview(text, limit=60):
    """Short, single-line summary of text for logging."""
    snippet = text[:limit].replace("\n", "\\n")
    return f"{len(text)} chars: {snippet!r}{'...' if len(text) > limit else ''}"


# Function to clear the shared text for a path
def clear_shared_text(path):
    clear_text_timers.pop(path, None)
    if connected_clients.get(path):
        return
    text_store.pop(path, None)
    connected_clients.pop(path, None)
    print(f"Shared text cleared for path: {path}")


def cancel_clear_timer(path):
    timer = clear_text_timers.pop(path, None)
    if timer:
        timer.cancel()


def schedule_clear(path):
    cancel_clear_timer(path)
    loop = asyncio.get_running_loop()
    clear_text_timers[path] = loop.call_later(CLEAR_DELAY, clear_shared_text, path)


# WebSocket handler
async def websocket_handler(websocket):
    path = normalize_path(websocket.request.path)

    # Add this client to the set for the path
    connected_clients[path].add(websocket)

    # Cancel the text clear timer if a new client connects
    cancel_clear_timer(path)
    print(f"Client connected to path: {path} ({len(connected_clients[path])} total)")

    try:
        # Send the current text for this path to the newly connected client
        await websocket.send(text_store[path])

        # Listen for changes from the client
        async for message in websocket:
            if isinstance(message, bytes):
                message = message.decode("utf-8", errors="replace")
            text_store[path] = message  # Update the shared text for the path
            print(f"Updated shared text for {path}: {preview(message)}")

            # Broadcast to all other clients without blocking on slow ones
            broadcast(connected_clients[path] - {websocket}, message)

    except ConnectionClosed:
        pass
    finally:
        connected_clients[path].discard(websocket)
        print(f"Client disconnected from path: {path} ({len(connected_clients[path])} remaining)")

        # If no clients are left, start the timer to clear text for this path
        if not connected_clients[path]:
            schedule_clear(path)


async def handle_request(request):
    raw_path = normalize_path(request.match_info['path'])

    # Handle POST requests for text updates
    if request.method == "POST":
        query_text = None
        if request.content_type in ("application/x-www-form-urlencoded", "multipart/form-data"):
            data = await request.post()
            if 'text' in data:
                query_text = data['text']
                if isinstance(query_text, web.FileField):  # curl -F "text=@file"
                    query_text = query_text.file.read().decode("utf-8", errors="replace")

        # Otherwise use the raw body as the text, e.g. curl --data-binary @file
        if query_text is None and request.content_type != "multipart/form-data":
            body = await request.read()
            if body:
                query_text = body.decode("utf-8", errors="replace")

        if query_text is not None:
            text_store[raw_path] = query_text
            print(f"REST update for path '{raw_path}': {preview(query_text)}")

            # Broadcast to WebSocket clients
            broadcast(connected_clients.get(raw_path, ()), query_text)

            return web.Response(text="Text updated successfully.")
        raise web.HTTPBadRequest(text="No text provided.")

    # Handle text retrieval via GET request
    if request.query.get('get_text') == 'true':
        text = text_store.get(raw_path, "")
        print(f"REST read for path '{raw_path}': {preview(text)}")
        return web.Response(text=text)

    # Serve static files
    if raw_path.startswith("/static/"):
        file_path = os.path.join("static", raw_path[len("/static/"):])
        if os.path.isfile(file_path):
            return web.FileResponse(file_path)
        raise web.HTTPNotFound(text=f"Static file not found: {raw_path}")

    # Serve index.html for dynamic boards and root path
    return web.FileResponse("index.html", headers={"Cache-Control": "no-cache"})


# Main function to start the servers
async def main():
    # Create an aiohttp app
    app = web.Application(client_max_size=MAX_TEXT_SIZE)

    # Use our custom handler for GET and POST requests
    app.router.add_get("/{path:.*}", handle_request)
    app.router.add_post("/{path:.*}", handle_request)

    # Start the HTTP server for static files + boards
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", 8080)
    await site.start()

    print("HTTP server running on http://0.0.0.0:8080")

    # Start the WebSocket server and run forever
    async with serve(websocket_handler, "0.0.0.0", 8765, max_size=MAX_TEXT_SIZE):
        print("WebSocket server running on ws://0.0.0.0:8765")
        try:
            await asyncio.Future()  # run forever
        except asyncio.CancelledError:
            print("Server shutting down...")
        finally:
            await runner.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
