import subprocess
import json
import sys

def test():
    payload = {
        "hook_event_name": "PreToolUse",
        "session_id": "test-session-abc",
        "tool_name": "bash",
        "tool_input": {
            "command": "git commit -m 'Initial commit'"
        }
    }
    
    print("Starting hook.py with mock stdin payload...")
    proc = subprocess.Popen(
        ["python3", "hook.py"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    
    try:
        stdout, stderr = proc.communicate(input=json.dumps(payload), timeout=320)
        print(f"hook.py finished with returncode: {proc.returncode}")
        print(f"Stdout: {stdout}")
        print(f"Stderr: {stderr}")
    except subprocess.TimeoutExpired:
        print("Timeout! Killing process...")
        proc.kill()
        stdout, stderr = proc.communicate()
        print(f"Stderr: {stderr}")

if __name__ == "__main__":
    test()
