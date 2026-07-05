import sys
import json
import urllib.request
import urllib.error

def main():
    try:
        input_data = sys.stdin.read()
        if not input_data:
            sys.stderr.write("[Claude Remote] Error: No input received on stdin\n")
            sys.exit(2)
            
        try:
            payload = json.loads(input_data)
        except Exception as e:
            sys.stderr.write(f"[Claude Remote] Error: Failed to parse JSON from stdin: {e}\n")
            sys.exit(2)

        tool_name = payload.get("tool_name", "unknown")
        tool_input = payload.get("tool_input", {})
        sys.stderr.write(f"\n[Claude Remote] Requesting remote approval for tool: {tool_name} ({json.dumps(tool_input)})\n")
        
        url = "http://localhost:9000/request"
        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode('utf-8'),
            headers={'Content-Type': 'application/json'},
            method='POST'
        )
        
        try:
            # Set timeout slightly higher than the agent timeout
            with urllib.request.urlopen(req, timeout=310) as response:
                res_body = response.read().decode('utf-8')
                res_data = json.loads(res_body)
                approved = res_data.get("approved", False)
                
                if approved:
                    sys.stderr.write("[Claude Remote] Action APPROVED\n")
                    sys.exit(0)
                else:
                    sys.stderr.write("[Claude Remote] Action DENIED\n")
                    sys.exit(2)
        except urllib.error.URLError as e:
            sys.stderr.write(f"[Claude Remote] Error: Could not connect to desktop agent at {url}. Make sure agent/desktop_agent.py is running.\n")
            sys.exit(2)
            
    except Exception as e:
        sys.stderr.write(f"[Claude Remote] Unexpected error: {e}\n")
        sys.exit(2)

if __name__ == "__main__":
    main()
