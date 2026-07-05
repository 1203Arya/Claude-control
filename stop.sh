#!/bin/bash
kill $(lsof -ti:8000,9000) 2>/dev/null
pkill -f ngrok 2>/dev/null
echo "✅ Sab band ho gaya"
