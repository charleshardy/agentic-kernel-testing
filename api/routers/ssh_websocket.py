"""
WebSocket-based SSH Terminal

Provides a real-time SSH terminal connection via WebSocket.
"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException
from typing import Dict, Any
import asyncio
import paramiko
import os

router = APIRouter()

# Store active SSH connections
_ssh_clients: Dict[str, paramiko.SSHClient] = {}


async def ssh_shell_handler(websocket: WebSocket, server_id: str, hostname: str, username: str, ssh_key_path: str = None):
    """
    Handle SSH shell session over WebSocket.
    """
    ssh_client = None
    channel = None
    
    try:
        print(f"[SSH Handler] Creating SSH client for {hostname}")
        # Create SSH client
        ssh_client = paramiko.SSHClient()
        ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        
        # Determine SSH key path
        if not ssh_key_path:
            # Try default keys
            home = os.path.expanduser("~")
            for key_file in ['.ssh/id_rsa', '.ssh/id_ed25519', '.ssh/id_ecdsa']:
                key_path = os.path.join(home, key_file)
                if os.path.exists(key_path):
                    ssh_key_path = key_path
                    print(f"[SSH Handler] Found SSH key: {ssh_key_path}")
                    break
        
        if not ssh_key_path:
            error_msg = '\r\n\x1b[1;31mNo SSH key found. Please configure SSH key.\x1b[0m\r\n'
            print(f"[SSH Handler] Error: No SSH key found")
            await websocket.send_text(error_msg)
            return
        
        # Connect to server
        connect_kwargs = {
            'hostname': hostname,
            'username': username,
            'timeout': 10,
            'banner_timeout': 10
        }
        
        if ssh_key_path and os.path.exists(ssh_key_path):
            connect_kwargs['key_filename'] = ssh_key_path
        
        print(f"[SSH Handler] Connecting to {hostname} as {username} with key {ssh_key_path}")
        ssh_client.connect(**connect_kwargs)
        print(f"[SSH Handler] SSH connection established")
        
        # Open interactive shell
        channel = ssh_client.invoke_shell(term='xterm-256color', width=120, height=30)
        channel.settimeout(0.0)
        print(f"[SSH Handler] Interactive shell opened")
        
        # Send welcome message
        await websocket.send_text('\r\n\x1b[1;32mConnected to ' + hostname + '\x1b[0m\r\n\r\n')
        
        # Create tasks for bidirectional communication
        read_task = None
        write_task = None
        
        async def read_from_ssh():
            """Read from SSH and send to WebSocket"""
            try:
                while True:
                    try:
                        if channel.recv_ready():
                            data = channel.recv(4096)
                            if data:
                                await websocket.send_bytes(data)
                        else:
                            await asyncio.sleep(0.01)
                    except asyncio.CancelledError:
                        print(f"[SSH Handler] Read task cancelled")
                        break
                    except Exception as e:
                        print(f"[SSH Handler] Read error: {e}")
                        break
            except Exception as e:
                print(f"[SSH Handler] Read task error: {e}")
        
        async def write_to_ssh():
            """Read from WebSocket and send to SSH"""
            try:
                while True:
                    try:
                        data = await websocket.receive()
                        if 'text' in data:
                            channel.send(data['text'])
                        elif 'bytes' in data:
                            channel.send(data['bytes'])
                    except WebSocketDisconnect:
                        print(f"[SSH Handler] WebSocket disconnected")
                        break
                    except asyncio.CancelledError:
                        print(f"[SSH Handler] Write task cancelled")
                        break
                    except RuntimeError as e:
                        # Handle "Cannot call receive once disconnect received" error
                        if "disconnect" in str(e).lower():
                            print(f"[SSH Handler] WebSocket already disconnected")
                            break
                        print(f"[SSH Handler] Write runtime error: {e}")
                        break
                    except Exception as e:
                        print(f"[SSH Handler] Write error: {e}")
                        break
            except Exception as e:
                print(f"[SSH Handler] Write task error: {e}")
        
        # Run both tasks concurrently
        print(f"[SSH Handler] Starting bidirectional communication")
        try:
            read_task = asyncio.create_task(read_from_ssh())
            write_task = asyncio.create_task(write_to_ssh())
            
            # Wait for either task to complete
            done, pending = await asyncio.wait(
                [read_task, write_task],
                return_when=asyncio.FIRST_COMPLETED
            )
            
            # Cancel remaining tasks
            for task in pending:
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass
                    
        except Exception as e:
            print(f"[SSH Handler] Communication error: {e}")
            if read_task and not read_task.done():
                read_task.cancel()
            if write_task and not write_task.done():
                write_task.cancel()
        
    except paramiko.AuthenticationException as e:
        error_msg = '\r\n\x1b[1;31mAuthentication failed. Please check SSH credentials.\x1b[0m\r\n'
        print(f"[SSH Handler] Authentication failed: {e}")
        await websocket.send_text(error_msg)
    except paramiko.SSHException as e:
        error_msg = f'\r\n\x1b[1;31mSSH error: {str(e)}\x1b[0m\r\n'
        print(f"[SSH Handler] SSH error: {e}")
        await websocket.send_text(error_msg)
    except Exception as e:
        error_msg = f'\r\n\x1b[1;31mConnection error: {str(e)}\x1b[0m\r\n'
        print(f"[SSH Handler] Connection error: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        await websocket.send_text(error_msg)
    finally:
        print(f"[SSH Handler] Cleaning up SSH connection")
        if channel:
            channel.close()
        if ssh_client:
            ssh_client.close()


@router.websocket("/ws/ssh/{server_id}")
async def websocket_ssh_endpoint(websocket: WebSocket, server_id: str):
    """
    WebSocket endpoint for SSH terminal connection.
    """
    print(f"[SSH WebSocket] Connection attempt for server: {server_id}")
    
    try:
        await websocket.accept()
        print(f"[SSH WebSocket] WebSocket accepted for server: {server_id}")
        
        # Get server info from query params
        hostname = websocket.query_params.get('hostname')
        username = websocket.query_params.get('username')
        ssh_key_path = websocket.query_params.get('ssh_key_path')
        
        print(f"[SSH WebSocket] Params - hostname: {hostname}, username: {username}, key: {ssh_key_path}")
        
        if not hostname or not username:
            error_msg = '\r\n\x1b[1;31mError: Missing hostname or username\x1b[0m\r\n'
            print(f"[SSH WebSocket] Error: Missing params")
            await websocket.send_text(error_msg)
            await websocket.close()
            return
        
        # Handle SSH session
        print(f"[SSH WebSocket] Starting SSH handler for {hostname}")
        await ssh_shell_handler(websocket, server_id, hostname, username, ssh_key_path)
        
    except WebSocketDisconnect as e:
        print(f"[SSH WebSocket] Client disconnected: {e}")
    except Exception as e:
        print(f"[SSH WebSocket] Error: {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()
        try:
            await websocket.send_text(f'\r\n\x1b[1;31mError: {str(e)}\x1b[0m\r\n')
        except:
            pass
    finally:
        try:
            await websocket.close()
            print(f"[SSH WebSocket] Connection closed for server: {server_id}")
        except:
            pass
