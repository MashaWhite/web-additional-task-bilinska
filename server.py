import socket

def run_server():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(("localhost", 8080))
    server.listen()
    while True:
        client_socket, client_address = server.accept()
        handle_requset(client_socket)

def handle_requset(client_socket):
    try:
        request = get_request(client_socket)
        if request["method"] == "POST":
            post(request)
        response = create_response(request)
    except Exception as e:
        response = create_error_response(e)
    finally:
        client_socket.sendall(response)
        client_socket.close()

def post(request):
    with open("posted_data.txt", "a") as f:
        f.write(request["body"] + "\n")

def create_response(request):
    response = ""
    body = ""
    method = request["method"]
    if method == "GET":
        response += "HTTP/1.1 200 OK\r\n"
        response += f"Content-Type: text/html; charset=utf-8\r\n"
        body = response_body()
    elif method == "POST":
        response += "HTTP/1.1 201 Created\r\n"
        response += f"Content-Type: text/plain\r\n"
        body = "Content posted successfully\r\n"
    response += f"Content-Length: {len(body.encode())}\r\n"
    response += "Connection: close\r\n\r\n"
    response += body
    return response.encode()

def response_body():
    with open("static/index.html", "r") as f:
        return f.read()

def create_error_response(e):
    response = ""
    code = str(e).split(",")[0]
    msg = str(e).split(",")[1]
    response += f"HTTP/1.1 {code} {msg}\r\n"
    response += "Connection: close\r\n\r\n"
    return response.encode()

def get_request(client_socket, ):
    #splited_request - separates line and headers from body
    request = {"method": "", "url": "", "query_params": {},"http_version": "", "headers": {}, "body": ""}
    request_bytes = b""
    body = b""
    while b"\r\n\r\n" not in request_bytes:
        chunk = client_socket.recv(1024)
        if not chunk:
            break
        request_bytes += chunk
    if b"\r\n\r\n" not in request_bytes:
        status_code(400)

    splited_request_bytes = request_bytes.split(b"\r\n\r\n", 1)
    if len(splited_request_bytes) > 1:
        #request_text contains no body
        request_text = splited_request_bytes[0].decode()
        body = splited_request_bytes[1]
    else:
        request_text = request_bytes.decode()
    lines = request_text.split("\r\n")

    request_params = lines[0].split(" ")
    if(len(request_params) < 3):
        status_code(400)

    request["method"] = request_params[0]
    request["url"] = request_params[1].split("?")[0]
    request["query_params"] = parse_query(request_params[1])
    request["http_version"] = request_params[2]
    request["headers"] = parse_headers(lines[1:])

    if "content-length" in request["headers"]:
        actual_len = int(request["headers"]["content-length"])
        while len(body) < actual_len:
            chunk = client_socket.recv(1024)
            if not chunk:
                break
            body += chunk
        if len(body) < actual_len :
            status_code(400)
        request["body"] = body.decode()

    handle_errors(request)
    return request

def parse_query(url_and_query):
    query_params_parsed = {}
    url_and_query_splited = url_and_query.split("?")
    if len(url_and_query_splited) == 1 or url_and_query_splited[-1] == "":
        return query_params_parsed

    query_params = url_and_query_splited[1].split("&")
    for query_param in query_params:
        if "=" in query_param:
            query_params_parsed[query_param.split("=", 1)[0]] = query_param.split("=", 1)[1]
        else:
            query_params_parsed[query_param] = True
    return query_params_parsed

def parse_headers(lines):
    headers = {}
    for header_line in lines:
        if not header_line:
            continue
        if ":" not in header_line:
            status_code(400)
        headers[header_line.split(":", 1)[0].lower()] = header_line.split(":", 1)[1].strip()
    return headers

def handle_errors(request):
    methods = ["GET", "POST"]
    resources = ["static/index.html"]
    if request["method"] not in methods:
        status_code(405)
    if request["url"] not in resources:
        status_code(404)

def status_code(code):
    message = ""
    if code == 200:
        message = "OK"
    elif code == 400:
        message = "Bad Request"
    elif code == 404:
        message = "Not Found"
    elif code == 405:
        message = "Method Not Allowed"
    raise Exception(f"{code},{message}")

run_server()
