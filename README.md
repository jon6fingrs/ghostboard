# Ghostboard

Ghostboard is a lightweight, self-hosted solution for real-time synchronized text sharing. This repository includes a WebSocket server for syncing text across multiple clients and a command-line client for retrieving or updating the shared text.

---

## Features

- **Server**:
  - Serves a webpage with a real-time synchronized text field.
  - Clients see live updates as text is typed.
  - Text remains synchronized across all connected clients.

- **Client**:
  - Command-line tool to retrieve or update the shared text.
  - Supports WebSocket servers with IPs or domain names.

- **Dockerized**:
  - Both server and client are packaged as Docker containers for ease of deployment.

---

## Repository Structure

```
ghostboard/
├── client/                  # Client-related files
│   ├── Dockerfile           # Dockerfile for the client
│   ├── requirements.txt     # Python dependencies for the client
│   ├── text_client.py       # Command-line client script
├── server/                  # Server-related files
│   ├── Dockerfile           # Dockerfile for the server
│   ├── requirements.txt     # Python dependencies for the server
│   ├── get_text.py          # WebSocket server script
│   ├── index.html           # Webpage for real-time synchronization
├── .gitignore               # Ignore unnecessary files
├── LICENSE                  # Project license
└── README.md                # This README file
```

---

## Setup

### Prerequisites

- Docker (for running containers)
- Python 3.8+ (if running the scripts locally)

---

## Usage

### Running the Server

#### Using Python

1. Navigate to the `server/` directory:
   ```bash
   cd server
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Run the server:
   ```bash
   python3 get_text.py
   ```

4. Access the server:
   - Open `http://<server-ip>:8080` in your browser.
   - Text changes will synchronize in real time.

#### Using Docker

1. Build the server image:
   ```bash
   docker build -t ghostboard-server ./server
   ```

2. Run the server container:
   ```bash
   docker run --rm -p 8080:8080 ghostboard-server
   ```

3. Access the server:
   - Open `http://<server-ip>:8080` in your browser.

---

### Running the Client

#### Using Python

1. Navigate to the `client/` directory:
   ```bash
   cd client
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Retrieve the current text:
   ```bash
   python3 text_client.py <server-ip>
   ```

4. Update the shared text:
   ```bash
   python3 text_client.py <server-ip> "New text to share"
   ```

#### Using Docker

1. Build the client image:
   ```bash
   docker build -t ghostboard-client ./client
   ```

2. Retrieve the current text:
   ```bash
   docker run --rm ghostboard-client <server-ip>
   ```

3. Update the shared text:
   ```bash
   docker run --rm ghostboard-client <server-ip> "New text to share"
   ```

---

## Examples

### Retrieve the Current Text
```bash
python3 client/text_client.py 192.168.1.1
```

Output:
```
Hello, World!
```

### Update the Shared Text
```bash
python3 client/text_client.py example.com "New shared text"
```

Output:
```
Text updated successfully.
```

#### **Docker**:
Retrieve text:
```bash
docker run --rm ghostboard-client example.com
```

Update text:
```bash
docker run --rm ghostboard-client example.com "Text updated via Docker!"
```

---

## Contributing

Contributions are welcome! Feel free to open an issue or submit a pull request.

---

## License

This project is licensed under the MIT License.
