"use client";

import { useEffect, useState, useRef } from "react";

interface PermissionRequest {
  request_id: string;
  tool_name: string;
  tool_input: any;
  session_id?: string;
}

export default function Home() {
  const [wsConnected, setWsConnected] = useState(false);
  const [agentConnected, setAgentConnected] = useState(false);
  const [pendingRequests, setPendingRequests] = useState<PermissionRequest[]>([]);
  const [showSettings, setShowSettings] = useState(false);
  const [wsUrlInput, setWsUrlInput] = useState("");
  const [activeWsUrl, setActiveWsUrl] = useState("");
  const socketRef = useRef<WebSocket | null>(null);

  // Load saved WebSocket URL on mount
  useEffect(() => {
    const savedUrl = localStorage.getItem("claude_remote_ws_url") || "";
    setWsUrlInput(savedUrl);
    
    const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
    const defaultUrl = `${protocol}//${window.location.hostname}:8000/ws/frontend`;
    setActiveWsUrl(savedUrl || defaultUrl);
  }, []);

  useEffect(() => {
    if (!activeWsUrl) return;

    let active = true;
    let reconnectTimeout: NodeJS.Timeout;

    function connect() {
      if (!active) return;
      
      console.log(`Connecting to backend WS: ${activeWsUrl}`);
      const socket = new WebSocket(activeWsUrl);
      socketRef.current = socket;

      socket.onopen = () => {
        if (!active) return;
        setWsConnected(true);
        console.log("Connected to backend WS");
      };

      socket.onmessage = (event) => {
        if (!active) return;
        try {
          const data = JSON.parse(event.data);
          console.log("Received WS message:", data);
          if (data.type === "state_update") {
            setAgentConnected(data.agent_connected);
            setPendingRequests(data.pending_requests || []);
          } else if (data.type === "new_request") {
            setPendingRequests((prev) => {
              if (prev.some((r) => r.request_id === data.request.request_id)) {
                return prev;
              }
              return [...prev, data.request];
            });
          } else if (data.type === "request_resolved") {
            setPendingRequests((prev) =>
              prev.filter((r) => r.request_id !== data.request_id)
            );
          }
        } catch (e) {
          console.error("Error parsing WS message:", e);
        }
      };

      socket.onclose = () => {
        if (!active) return;
        setWsConnected(false);
        setAgentConnected(false);
        console.log("WS connection closed. Reconnecting in 3s...");
        reconnectTimeout = setTimeout(connect, 3000);
      };

      socket.onerror = (err) => {
        console.error("WS error:", err);
        socket.close();
      };
    }

    connect();

    return () => {
      active = false;
      clearTimeout(reconnectTimeout);
      if (socketRef.current) {
        socketRef.current.close();
      }
    };
  }, [activeWsUrl]);

  const saveWsUrl = (url: string) => {
    localStorage.setItem("claude_remote_ws_url", url);
    setWsUrlInput(url);
    
    const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
    const defaultUrl = `${protocol}//${window.location.hostname}:8000/ws/frontend`;
    setActiveWsUrl(url || defaultUrl);
    setShowSettings(false);
  };

  const handleAction = (requestId: string, approved: boolean) => {
    if (socketRef.current && socketRef.current.readyState === WebSocket.OPEN) {
      socketRef.current.send(
        JSON.stringify({
          type: "action",
          request_id: requestId,
          approved: approved,
        })
      );
    } else {
      alert("Error: Web Socket connection is not open.");
    }
  };

  const getToolContent = (request: PermissionRequest) => {
    const input = request.tool_input;
    if (typeof input === "string") {
      return input;
    }
    if (input && typeof input === "object") {
      if ("command" in input) {
        return input.command;
      }
      if ("path" in input && "content" in input) {
        return `Write to ${input.path}:\n\n${input.content}`;
      }
      return JSON.stringify(input, null, 2);
    }
    return String(input);
  };

  const getToolBadgeClass = (toolName: string) => {
    const name = toolName.toLowerCase();
    if (name.includes("bash") || name.includes("command") || name.includes("run")) {
      return "tool-badge bash";
    }
    if (name.includes("write") || name.includes("create")) {
      return "tool-badge write";
    }
    if (name.includes("edit") || name.includes("replace") || name.includes("modify")) {
      return "tool-badge edit";
    }
    return "tool-badge";
  };

  return (
    <div className="container">
      <header>
        <h1>Claude Remote</h1>
        <button 
          className="settings-toggle" 
          onClick={() => setShowSettings(!showSettings)}
          aria-label="Toggle settings"
        >
          ⚙️
        </button>
        <div className="status-bar">
          <span className={`status-badge ${wsConnected ? "connected" : ""}`}>
            Server: {wsConnected ? "Online" : "Offline"}
          </span>
          <span className={`status-badge ${agentConnected ? "connected" : ""}`}>
            Agent: {agentConnected ? "Connected" : "Disconnected"}
          </span>
        </div>
      </header>

      <main>
        {showSettings && (
          <div className="settings-panel">
            <div className="settings-title">Configure Backend URL</div>
            <input
              type="text"
              className="input-text"
              placeholder="ws://192.168.x.x:8000/ws/frontend"
              value={wsUrlInput}
              onChange={(e) => setWsUrlInput(e.target.value)}
            />
            <div className="settings-actions">
              <button 
                className="btn-small btn-secondary" 
                onClick={() => saveWsUrl("")}
              >
                Reset Default
              </button>
              <button 
                className="btn-small btn-primary" 
                onClick={() => saveWsUrl(wsUrlInput)}
              >
                Save
              </button>
            </div>
          </div>
        )}

        {pendingRequests.length === 0 ? (
          <div className="empty-state">
            <div className="empty-state-icon">🔔</div>
            <div className="empty-state-text">
              {agentConnected
                ? "Ready! Listening for Claude Code permission prompts..."
                : "Waiting for Desktop Agent to connect..."}
            </div>
          </div>
        ) : (
          pendingRequests.map((request) => (
            <div key={request.request_id} className="request-card">
              <div className="card-header">
                <span className={getToolBadgeClass(request.tool_name)}>
                  {request.tool_name}
                </span>
                {request.session_id && (
                  <span className="session-id" title="Claude Session ID">
                    Session: {request.session_id.slice(0, 8)}...
                  </span>
                )}
              </div>
              <div className="code-block">
                {getToolContent(request)}
              </div>
              <div className="action-buttons">
                <button
                  className="btn btn-deny"
                  onClick={() => handleAction(request.request_id, false)}
                >
                  Deny (N)
                </button>
                <button
                  className="btn btn-approve"
                  onClick={() => handleAction(request.request_id, true)}
                >
                  Approve (Y)
                </button>
              </div>
            </div>
          ))
        )}
      </main>
    </div>
  );
}
