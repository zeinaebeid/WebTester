# WebTester


## Overview

This project implements a simple Python-based web client that performs the following tasks:
- Collects information about a specified web server.
- Checks whether the server supports HTTP/2.
- Retrieves and displays cookies from the server response.
- Determines whether the requested web page is password-protected.

The program establishes a connection to the server, sends an HTTP request, and processes the response to display the information.

---

## Requirements

- Python 3.x
- Internet connection for accessing web servers

---

## How to Run the Program

### Usage:


python3 WebTester.py <URL>


### Example:


python3 WebTester.py www.google.com


This will output the following information:
1. Whether the server supports HTTP/2.
2. A list of cookies (if any), along with their expiration time and domain (if provided).
3. Whether the page is password-protected.

---

## Output Format

The output is formatted as follows:

```
website: <hostname>
1. Supports http2: yes/no
2. List of Cookies:
cookie name: <cookie_name>, expires time: <expiration_date>; domain name: <domain>
cookie name: <cookie_name>
...
3. Password-protected: yes/no
```

### Example Output:

```
website: www.google.com
1. Supports http2: no
2. List of Cookies:
cookie name: AEC, expires time: Thu, 27-Mar-2025 00:24:30 GMT; domain name: .google.com
cookie name: NID, expires time: Sun, 30-Mar-2025 00:24:30 GMT; domain name: .google.com
3. Password-protected: no
```

---

## Features

- **HTTP/2 Support Check**: The client checks if the server supports HTTP/2 by using Application-Layer Protocol Negotiation (ALPN) for HTTPS and the `Upgrade` header for HTTP.
  
- **Cookie Extraction**: The client extracts cookies from the server response using the `Set-Cookie` headers. It prints the cookie name, expiration date (if available), and domain (if available).

- **Password Protection Detection**: The client checks if the page is password-protected by looking for a `401 Unauthorized` status code in the server response.

- **Redirection Handling**: The client handles 301/302 redirects and makes another request to the new URL provided in the `Location` header.

---

## Error Handling

The program will display an error if:
1. The URL is invalid.
2. The server cannot be reached.
3. An invalid or unexpected response is received from the server.

---

## Limitations

- The program does not follow more than one redirection at a time.
- Cookies set via JavaScript (client-side) are not detected by this program, as it only checks `Set-Cookie` headers from the server response.
- The program does not check for other types of authentication mechanisms beyond the `401 Unauthorized` status.

---

## Notes

- The program must be executed in an environment with Python 3.x installed.
  
---

## Installation

No installation required. Simply download the script and run it using Python 3.


