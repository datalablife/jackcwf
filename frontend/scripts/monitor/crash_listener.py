#!/usr/bin/env python3
"""
Supervisor Event Listener for Crash Notifications

Listens for PROCESS_STATE_FATAL and PROCESS_STATE_EXITED events
and sends notifications when services crash.
"""

import os
import sys
import json
import urllib.request
from datetime import datetime


def write_stdout(s):
    sys.stdout.write(s)
    sys.stdout.flush()


def write_stderr(s):
    sys.stderr.write(s)
    sys.stderr.flush()


def send_webhook_alert(event_data: dict):
    """Send alert to webhook if configured."""
    webhook_url = os.getenv('ALERT_WEBHOOK_URL')
    if not webhook_url:
        return

    try:
        data = json.dumps({
            "title": f"Process Crashed: {event_data.get('processname', 'unknown')}",
            "message": f"Process {event_data.get('processname')} has {event_data.get('event_type', 'crashed')}. "
                       f"Exit code: {event_data.get('expected', 'unknown')}",
            "severity": "critical",
            "timestamp": datetime.now().isoformat(),
            "source": "supervisor_crash_listener",
            "details": event_data
        }).encode('utf-8')

        req = urllib.request.Request(
            webhook_url,
            data=data,
            headers={'Content-Type': 'application/json'}
        )
        urllib.request.urlopen(req, timeout=10)
    except Exception as e:
        write_stderr(f"Failed to send webhook: {e}\n")


def main():
    while True:
        # Signal ready to receive events
        write_stdout('READY\n')

        # Read event header
        line = sys.stdin.readline()
        headers = dict([x.split(':') for x in line.split() if ':' in x])

        # Read event payload
        data_len = int(headers.get('len', 0))
        payload = sys.stdin.read(data_len) if data_len > 0 else ''

        # Parse payload
        event_data = dict([x.split(':') for x in payload.split() if ':' in x])
        event_data['event_type'] = headers.get('eventname', 'UNKNOWN')

        # Log the event
        process_name = event_data.get('processname', 'unknown')
        event_type = event_data['event_type']

        write_stderr(f"[CRASH_LISTENER] Event: {event_type} for process: {process_name}\n")

        # Send notification for critical events
        if event_type in ('PROCESS_STATE_FATAL', 'PROCESS_STATE_EXITED'):
            send_webhook_alert(event_data)

        # Signal event handled
        write_stdout('RESULT 2\nOK')


if __name__ == '__main__':
    main()
