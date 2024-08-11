from pyngrok import ngrok
import threading

ngrok.set_auth_token('2kGrBZhxLDOSsT3UNs5tVpOJmfq_7Z8vLFaW6VvHEusYUHNme')
port_no = 8000

# Setup ngrok
def start_ngrok():
    public_url = ngrok.connect(port_no)
    print(f'ngrok tunnel "{public_url}" -> "http://127.0.0.1:{port_no}"')

# Start ngrok when app is run
ngrok_thread = threading.Thread(target=start_ngrok)
ngrok_thread.daemon = True  # Ensures thread exits when main program exits
ngrok_thread.start()

# Keep the main thread alive so the ngrok thread can run
try:
    while True:
        pass
except KeyboardInterrupt:
    print("Shutting down server...")
    ngrok.kill()  # Ensures ngrok process is killed
