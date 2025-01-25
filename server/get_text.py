import asyncio
import websockets
from aiohttp import web
import threading

# Shared text state
shared_text = ""

# Track connected clients
connected_clients = set()

# Timer to clear text after all clients disconnect
clear_text_timer = None


# Function to clear the shared text
def clear_shared_text():
    global shared_text, clear_text_timer
    shared_text = ""
    print("Shared text cleared after all clients disconnected.")
    clear_text_timer = None  # Reset the timer


# WebSocket handler
async def sync_text(websocket, path):
    global shared_text, clear_text_timer
    connected_clients.add(websocket)

    # Cancel the text clear timer if a new client connects
    if clear_text_timer:
        clear_text_timer.cancel()
        clear_text_timer = None

    try:
        # Send the current text to the newly connected client
        await websocket.send(shared_text)

        # Listen for changes from the client
        async for message in websocket:
            shared_text = message  # Update the shared text
            print(f"Updated shared text: {shared_text}")

            # Broadcast the updated text to all connected clients
            disconnected_clients = []
            for client in connected_clients:
                try:
                    if client != websocket:  # Avoid echoing back to sender
                        await client.send(shared_text)
                except websockets.ConnectionClosed:
                    disconnected_clients.append(client)

            # Remove disconnected clients
            for client in disconnected_clients:
                connected_clients.remove(client)

    except websockets.ConnectionClosed:
        print("Client disconnected.")
    finally:
        connected_clients.discard(websocket)  # Ensure the client is removed from the set
        print(f"{len(connected_clients)} client(s) remaining.")
        # If no clients are left, start the timer to clear text
        if not connected_clients:
            clear_text_timer = threading.Timer(300, clear_shared_text)  # Clear after 5 minutes
            clear_text_timer.start()


# Serve the static HTML file
async def handle_index(request):
    return web.FileResponse("index.html")


# Main function to start the servers
async def main():
    # Create an aiohttp app for serving static files
    app = web.Application()
    app.router.add_get("/", handle_index)

    # Start the HTTP server for static files
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", 8080)
    await site.start()

    print("HTTP server running on http://0.0.0.0:8080")

    # Start the WebSocket server
    ws_server = await websockets.serve(sync_text, "0.0.0.0", 8765)
    print("WebSocket server running on ws://0.0.0.0:8765")

    # Keep the servers running
    try:
        await asyncio.Future()  # Keep running forever
    except asyncio.CancelledError:
        print("Server shutting down...")


if __name__ == "__main__":
    asyncio.run(main())
