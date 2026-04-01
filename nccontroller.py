#!/usr/bin/env python3
# Adam Shaw UCID:30204315

import sys
import socket
import time
import hashlib
import select

def compute_mac(nonce, secret):
    data = nonce + secret
    return hashlib.sha256(data.encode()).hexdigest()[:8]

def send_command(sock, command_parts, secret):
    nonce = str(int(time.time() * 1000))
    mac = compute_mac(nonce, secret)
    full_command = f"{nonce} {mac} " + " ".join(command_parts) + "\n" # authenticated payload.
    sock.sendall(full_command.encode())

def gather_replies(sock):
    replies = []
    buffer = ""
    end_time = time.time() + 5.0 # 5 sec max
    
    sock.setblocking(0)
    print("Waiting 5s to gather replies.")
    while time.time() < end_time:
        ready = select.select([sock], [], [], 0.1) # so it doesn't need to keep looping
        if ready[0]:
            try:
                data = sock.recv(4096)
                if not data:
                    break
                buffer += data.decode()
                while '\n' in buffer:
                    line, buffer = buffer.split('\n', 1)
                    replies.append(line.strip())
            except Exception:
                pass
    sock.setblocking(1)
    return replies

def main():
    if len(sys.argv) != 3:
        sys.exit(1)
        
    target = sys.argv[1]
    secret = sys.argv[2]
    host, port = target.split(':')
    port = int(port)
    
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s.connect((host, port))
    except Exception:
        print("Failed to connect.")
        sys.exit(1)
        
    while True:
        try:
            cmd_input = input("cmd> ").strip() # prompt
        except EOFError:
            break
            
        if not cmd_input:
            continue
            
        parts = cmd_input.split()
        cmd = parts[0]
        
        if cmd == "quit":
            print("Disconnected.")
            break
            
        if cmd not in ["status", "shutdown", "attack", "move"]:
            print("Unknown command.")
            continue
            
        send_command(s, parts, secret) # sends command and collects string replies
        replies = gather_replies(s)
        
        if cmd == "status":
            bots = []
            for r in replies:
                if r.startswith("-status"):
                    tokens = r.split()
                    if len(tokens) >= 3:
                        bots.append(f"{tokens[1]} ({tokens[2]})")
            print(f"Result: {len(bots)} bots replied.")
            if bots:
                print(", ".join(bots))
                
        elif cmd == "shutdown":
            bots = []
            for r in replies:
                if r.startswith("-shutdown"):
                    tokens = r.split()
                    if len(tokens) >= 2:
                        bots.append(tokens[1])
            print(f"Result: {len(bots)} bots shut down.")
            if bots:
                print(", ".join(bots))
                
        elif cmd == "attack":
            successes = []
            failures = []
            for r in replies:
                if r.startswith("-attack"):
                    tokens = r.split(maxsplit=3)
                    if len(tokens) >= 3:
                        nick = tokens[1]
                        status = tokens[2]
                        if status == "OK":
                            successes.append(nick)
                        elif status == "FAIL" and len(tokens) >= 4:
                            failures.append(f"{nick}: {tokens[3]}")
            
            print(f"Result: {len(successes)} bots attacked successfully:")
            if successes:
                print(", ".join(successes))
            print(f"{len(failures)} bots failed to attack:")
            for f in failures:
                print(f)
                
        elif cmd == "move":
            bots = []
            for r in replies:
                if r.startswith("-move"):
                    tokens = r.split()
                    if len(tokens) >= 2:
                        bots.append(tokens[1])
            print(f"Result: {len(bots)} bots moved.")
            if bots:
                print(", ".join(bots))

if __name__ == "__main__":
    main()