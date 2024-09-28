import re
import socket
import ssl
import sys

# Define URI and cookie patterns using regex
uri_pattern = re.compile(
    r'^(?:(?P<protocol>https?)://)?(?P<host>[^:/]+)(?::(?P<port>\d+))?((?P<path>.*?))?$',
    re.IGNORECASE
)
cookie_pattern = re.compile(
    r'Set-Cookie:\s(?P<name>[^=]+)=(?P<value>[^;\n]*)(?=.*?\sdomain=(?P<domain>[^;\n]+))?(?=.*?\sexpires=(?P<expires>[^;\n]+))?(?=.*?\spath=(?P<path>[^;\n]+))?.*',
    re.IGNORECASE
)

# Function to parse URLs using regex
def parse_url(url):
    uri_match = uri_pattern.match(url)
    if not uri_match:
        raise ValueError(f"Invalid URL: {url}")
    
    protocol = uri_match.group("protocol") or "http"
    host = uri_match.group("host")
    port = int(uri_match.group("port")) if uri_match.group("port") else (443 if protocol == "https" else 80)
    path = uri_match.group("path") or "/"
    
    return protocol, host, port, path

# Function to parse cookies using regex
def cookie_check(headers):
    cookies = {}
    cookie_matches = cookie_pattern.finditer(headers)
    for match in cookie_matches:
        cookies[match.group("name")] = (
            match.group("value"), 
            match.group("domain"), 
            match.group("expires"), 
            match.group("path")
        )
    return cookies

# Context manager for socket connections, including SSL for HTTPS
class Socket:
    def __init__(self, host, port, protocol, alpn_proto=None, timeout=10):
        self.host = host
        self.port = port
        self.protocol = protocol
        self.alpn_proto = alpn_proto or ["http/1.1"]
        self.timeout = timeout

    def __enter__(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.settimeout(self.timeout)
        
        if self.protocol == "https":
            context = ssl.create_default_context()
            context.set_alpn_protocols(self.alpn_proto)
            self.sock = context.wrap_socket(self.sock, server_hostname=self.host)
        
        self.sock.connect((self.host, self.port))
        return self.sock

    def __exit__(self, exc_type, exc_value, traceback):
        self.sock.close()

# Function to check if the server supports HTTP/2
def check_http2(host, protocol):
    if protocol == "https":
        try:
            with Socket(host, 443, protocol, alpn_proto=["h2", "http/1.1"]) as sock:
                return sock.selected_alpn_protocol() == "h2"
        except ssl.SSLError:
            return False
    else:
        return check_http2_http(host)  # HTTP Upgrade method

# Function to check HTTP/2 over HTTP using the Upgrade header
def check_http2_http(host):
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((host, 80))
        
        # Sending HTTP/1.1 request with Upgrade header to try upgrading to HTTP/2
        request = (
            "GET / HTTP/1.1\r\n"
            f"Host: {host}\r\n"
            "Connection: Upgrade, close\r\n"
            "Upgrade: h2c\r\n"
            "HTTP2-Settings: \r\n"
            "\r\n"
        )
        sock.sendall(request.encode())
        
        # Read the response in chunks 
        response = ""
        while True:
            chunk = sock.recv(4096).decode('utf-8', errors='ignore')
            if not chunk:
                break
            response += chunk
        sock.close()
        
        # Check if the server responds with 101 Switching Protocols or other upgrade success
        if "101 Switching Protocols" in response or "Upgrade: h2c" in response:
            return True
    except Exception:
        return False

# Function to handle redirects 
def handle_redirects(headers, host, port, protocol, path):
    redirect_match = re.search(r"Location:\s(?P<url>[^\r\n]+)", headers)
    if redirect_match:
        new_url = redirect_match.group("url")
        protocol, host, port, path = parse_url(new_url)
        return protocol, host, port, path
    return None

# Function to print the final results 
def print_final_results(host, http2_support, cookies, password_protected):
    print(f"\nwebsite: {host}")
    print(f"1. Supports http2: {'yes' if http2_support else 'no'}")
    print("2. List of Cookies:")
    
    if cookies:
        for name, (value, domain, expires, path) in cookies.items():
            # Start with the cookie name
            print(f"cookie name: {name}", end="")

            # If expiration time exists, print it
            if expires:
                print(f", expires time: {expires}", end="")

            # If domain exists, print it
            if domain:
                print(f"; domain name: {domain}")
            else:
                print()  # Just move to the next line if no domain
    else:
        print("No cookies found.")

    print(f"3. Password-protected: {'yes' if password_protected else 'no'}")
    print()

# Main function to send HTTP requests and process the responses
def main(url):
    protocol, host, port, path = parse_url(url)
    
    with Socket(host, port, protocol) as sock:
        request = f"GET {path} HTTP/1.1\r\nHost: {host}\r\nConnection: close\r\n\r\n"
        sock.sendall(request.encode())

        response = ""
        while True:
            chunk = sock.recv(4096).decode('utf-8', errors='ignore')
            if not chunk:
                break
            response += chunk

    headers, body = response.split("\r\n\r\n", 1) if "\r\n\r\n" in response else (response, "")

    # Handle 301/302 redirection
    redirect_info = handle_redirects(headers, host, port, protocol, path)
    if redirect_info:
        protocol, host, port, path = redirect_info
        return main(f"{protocol}://{host}:{port}{path}")

    # Check if HTTP/2 is supported
    http2_support = check_http2(host, protocol)

    # Check for cookies
    cookies = cookie_check(headers)

    # Check for password protection by looking for "401 Unauthorized"
    password_protected = "401 Unauthorized" in headers

    # Print final results
    print_final_results(host, http2_support, cookies, password_protected)

# Entry point
if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Invalid Parameters. Usage: python3 WebTester.py <URL>")
        sys.exit(1)
    
    url = sys.argv[1]
    main(url)
