#!/bin/bash
# Granian availability diagnostic script
# Run this in the Coolify container to diagnose PATH issues

echo "=========================================="
echo "Granian Diagnostic Report"
echo "=========================================="
echo ""

echo "1. Environment Information"
echo "--------------------------"
echo "Current user: $(whoami)"
echo "Current directory: $(pwd)"
echo "Shell: $SHELL"
echo ""

echo "2. PATH Variable"
echo "----------------"
echo "PATH=$PATH"
echo ""

echo "3. Python Information"
echo "---------------------"
echo "System Python: $(which python || echo 'Not found')"
echo "System Python3: $(which python3 || echo 'Not found')"
echo "Venv Python: $(ls -la .venv/bin/python 2>/dev/null || echo '.venv/bin/python not found')"
echo ""

echo "4. Granian Availability"
echo "-----------------------"
echo "System granian: $(which granian 2>/dev/null || echo 'Not found in PATH')"
echo "Venv granian: $(ls -la .venv/bin/granian 2>/dev/null || echo '.venv/bin/granian not found')"
echo ""

echo "5. Installed Packages"
echo "---------------------"
if [ -f .venv/bin/pip ]; then
    echo "Packages with 'granian' in name:"
    .venv/bin/pip list | grep -i granian || echo "No granian package found"
    echo ""
    echo "ASGI servers installed:"
    .venv/bin/pip list | grep -E "(granian|uvicorn|hypercorn|daphne)" || echo "No ASGI servers found"
else
    echo ".venv/bin/pip not found"
fi
echo ""

echo "6. Virtual Environment Structure"
echo "---------------------------------"
if [ -d .venv ]; then
    echo ".venv exists"
    echo "Contents of .venv/bin:"
    ls -la .venv/bin/ | head -20
else
    echo ".venv directory not found"
fi
echo ""

echo "7. Testing Granian Execution"
echo "----------------------------"
if [ -f .venv/bin/granian ]; then
    echo "Testing direct execution:"
    .venv/bin/granian --version 2>&1 || echo "Failed to execute"
    echo ""
    echo "File permissions:"
    ls -la .venv/bin/granian
else
    echo ".venv/bin/granian not found"
fi
echo ""

echo "8. Reflex Configuration"
echo "-----------------------"
if [ -f rxconfig.py ]; then
    echo "rxconfig.py exists"
    echo "Backend configuration:"
    grep -E "(backend_host|backend_port|backend_backend)" rxconfig.py || echo "No backend config found"
else
    echo "rxconfig.py not found"
fi
echo ""

echo "=========================================="
echo "Diagnostic Complete"
echo "=========================================="
