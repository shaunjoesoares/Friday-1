"""
Multi-Agent Google Workspace Assistant
Coordinates Gmail, Google Drive, and Google Calendar operations using Google Gemini AI
Uses REST API for Gemini (compatible with Python 3.14+)
"""

import os
import sys
import io
import requests
import json

# Force UTF-8 encoding for stdout to handle emojis
# sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from config import GEMINI_API_KEY
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload, MediaIoBaseUpload
import pickle
from datetime import datetime, timedelta
from typing import List, Dict, Any
import base64
from email.mime.text import MIMEText
import time

# Scopes for Google APIs
SCOPES = [
    'https://www.googleapis.com/auth/gmail.modify',
    'https://www.googleapis.com/auth/drive',
    'https://www.googleapis.com/auth/calendar'
]

class GeminiRESTClient:
    """REST API client for Gemini (fixes Python 3.14 gRPC issues)"""
    def __init__(self, api_key: str, model_name: str = "gemini-flash-latest"):
        self.api_key = api_key
        self.model_name = model_name
        self.base_url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent"
    
    def generate_content(self, prompt: str):
        """Generate content using REST API instead of gRPC"""
        max_retries = 3
        print(f"[DEBUG] Generating content via REST API...", flush=True)
        
        for attempt in range(max_retries):
            try:
                print(f"[DEBUG] Attempt {attempt+1}", flush=True)
                
                headers = {"Content-Type": "application/json"}
                payload = {
                    "contents": [{
                        "parts": [{"text": prompt}]
                    }]
                }
                
                response = requests.post(
                    f"{self.base_url}?key={self.api_key}",
                    headers=headers,
                    json=payload,
                    timeout=30
                )
                
                if response.status_code == 200:
                    result = response.json()
                    # Extract text from response
                    text = result['candidates'][0]['content']['parts'][0]['text']
                    print("[DEBUG] Generation successful", flush=True)
                    
                    # Create response object that mimics genai response
                    class Response:
                        def __init__(self, txt):
                            self.text = txt
                    
                    return Response(text)
                elif response.status_code == 429:
                    if attempt < max_retries - 1:
                        print(f"[WARN] Rate limit hit. Retrying in 10 seconds... (Attempt {attempt+1}/{max_retries})", flush=True)
                        time.sleep(10)
                        continue
                    raise Exception(f"Rate limit exceeded: {response.text}")
                else:
                    raise Exception(f"API Error {response.status_code}: {response.text}")
                    
            except requests.exceptions.RequestException as e:
                print(f"[DEBUG] Network error: {e}", flush=True)
                if attempt < max_retries - 1:
                    print(f"[WARN] Retrying in 5 seconds... (Attempt {attempt+1}/{max_retries})", flush=True)
                    time.sleep(5)
                    continue
                raise Exception(f"Network error: {str(e)}")
        
        raise Exception("Max retries exceeded")

class GoogleWorkspaceAgent:
    """Main coordinator agent for Google Workspace operations"""
    
    def __init__(self):
        self.creds = self._get_credentials()
        self.gmail_service = build('gmail', 'v1', credentials=self.creds)
        self.drive_service = build('drive', 'v3', credentials=self.creds)
        self.calendar_service = build('calendar', 'v3', credentials=self.creds)
        
        # Initialize Gemini REST API client (Python 3.14 compatible)
        self.model = GeminiRESTClient(GEMINI_API_KEY, "gemini-flash-latest")
        self.chat_history = []
        
        # Initialize specialized agents
        self.email_agent = EmailAgent(self.gmail_service, self.model)
        self.drive_agent = DriveAgent(self.drive_service, self.model)
        self.calendar_agent = CalendarAgent(self.calendar_service, self.model)
    
    def _get_credentials(self):
        """Authenticate and get credentials for Google APIs"""
        creds = None
        
        # Check if we have saved credentials
        if os.path.exists('token.pickle'):
            with open('token.pickle', 'rb') as token:
                creds = pickle.load(token)
        
        # If no valid credentials, authenticate
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                print("Refreshing expired credentials...", flush=True)
                creds.refresh(Request())
            else:
                print("Starting OAuth authentication...", flush=True)
                print("A browser window will open for authentication.", flush=True)
                flow = InstalledAppFlow.from_client_secrets_file(
                    'credentials.json', SCOPES)
                creds = flow.run_local_server(port=0)
                print("[OK] Authentication successful!", flush=True)
            
            # Save credentials for future use
            with open('token.pickle', 'wb') as token:
                pickle.dump(creds, token)
        
        return creds
    
    def process_request(self, user_input: str) -> str:
        """Main coordinator that routes requests to specialized agents"""
        
        # Prepare history context for the router
        history_context = ""
        for turn in self.chat_history[-3:]:
            history_context += f"User: {turn['user']}\nAssistant: {turn['assistant']}\n"

        system_prompt = f"""You are a helpful AI assistant named Friday.
        You coordinate specialized agents for Gmail, Google Drive, and Google Calendar, but you can also chat normally.
        
        Recent Conversation:
        {history_context}

        Analyze this request: "{user_input}"
        
        Determine the best way to handle it:
        - EMAIL: If the user wants to send, read, or manage emails.
        - DRIVE: If the user wants to create, search, or manage files.
        - CALENDAR: If the user wants to schedule or check events.
        - CHAT: If the user is asking a general question, saying hello, or asking about your capabilities.
        
        Respond with ONLY ONE WORD: EMAIL, DRIVE, CALENDAR, or CHAT"""
        
        try:
            # Determine which agent to use
            print(f"[DEBUG] Routing request: {user_input}", flush=True)
            response = self.model.generate_content(system_prompt)
            agent_type = response.text.strip().upper()
            
            print(f"[TARGET] Routing to: {agent_type} agent", flush=True)
            
            # Route to appropriate agent
            if 'EMAIL' in agent_type:
                result = self.email_agent.process(user_input, self.chat_history)
            elif 'DRIVE' in agent_type:
                result = self.drive_agent.process(user_input, self.chat_history)
            elif 'CALENDAR' in agent_type:
                result = self.calendar_agent.process(user_input, self.chat_history)
            else:
                # General Chat Mode
                chat_prompt = f"""You are Friday, a helpful AI assistant.
                
                Recent Conversation:
                {history_context}
                
                The user said: "{user_input}"
                
                Respond naturally and helpfully. If they asked how to do something (like "how do I format files"), explain it to them.
                Do not try to execute commands, just chat."""
                
                chat_response = self.model.generate_content(chat_prompt)
                result = chat_response.text
            
            self.chat_history.append({'user': user_input, 'assistant': result})
            return result
        
        except Exception as e:
            return f"[ERROR] Error processing request: {str(e)}"


class EmailAgent:
    """Specialized agent for Gmail operations"""
    
    def __init__(self, gmail_service, model):
        self.service = gmail_service
        self.model = model
    
    def process(self, request: str, history: List[Dict]) -> str:
        """Process email-related requests"""
        
        history_context = ""
        for turn in history[-3:]:
            history_context += f"User: {turn['user']}\nAssistant: {turn['assistant']}\n"
        
        system_prompt = f"""You are an Email Agent specialized in Gmail operations.
        
        Recent Conversation (Use this to resolve references like "those emails" or "the last one"):
        {history_context}
        
        Analyze this request: "{request}"
        
        Determine the action and extract parameters:
        - Actions: SEND, READ, DELETE, MARK_READ, MARK_UNREAD, REPLY, LIST
        - For SEND: extract 'to' (email), 'subject', 'message'
        - For READ/DELETE/MARK: extract 'message_id'. If multiple, separate with commas. If referring to previously listed emails, extract their IDs from history.
        - For REPLY: extract 'message_id' and 'message'
        - For LIST: no parameters needed
        
        Respond in this exact format:
        ACTION: <action>
        to: <email>
        subject: <subject>
        message: <message>
        message_id: <id or comma-separated ids>
        
        Only include relevant parameters."""
        
        try:
            response = self.model.generate_content(system_prompt)
            parsed = self._parse_response(response.text)
            
            action = parsed.get('ACTION', '').upper()
            
            if action == 'SEND':
                return self.send_email(
                    parsed.get('to', ''),
                    parsed.get('subject', 'No Subject'),
                    parsed.get('message', '')
                )
            elif action == 'LIST':
                return self.list_emails()
            elif action == 'READ':
                if 'NEED_ID' in parsed.get('message_id', ''):
                    return "Please provide the message ID or use 'list emails' first."
                return self.get_email(parsed.get('message_id'))
            elif action == 'DELETE':
                if 'NEED_ID' in parsed.get('message_id', ''):
                    return "Please provide the message ID or use 'list emails' first."
                return self.delete_email(parsed.get('message_id'))
            elif action == 'MARK_READ':
                if 'NEED_ID' in parsed.get('message_id', ''):
                    return "Please provide the message ID or use 'list emails' first."
                return self.mark_as_read(parsed.get('message_id'))
            elif action == 'MARK_UNREAD':
                if 'NEED_ID' in parsed.get('message_id', ''):
                    return "Please provide the message ID or use 'list emails' first."
                return self.mark_as_unread(parsed.get('message_id'))
            elif action == 'REPLY':
                if 'NEED_ID' in parsed.get('message_id', ''):
                    return "Please provide the message ID or use 'list emails' first."
                return self.reply_to_email(parsed.get('message_id'), parsed.get('message', ''))
            
            return "I couldn't understand that email request. Try: 'send email', 'list emails', etc."
        
        except Exception as e:
            return f"[ERROR] Error processing email request: {str(e)}"
    
    def _parse_response(self, text: str) -> Dict[str, str]:
        """Parse AI response into parameters"""
        params = {}
        for line in text.strip().split('\n'):
            if ':' in line:
                key, val = line.split(':', 1)
                params[key.strip()] = val.strip()
        return params
    
    def list_emails(self, max_results: int = 10) -> str:
        """List recent emails"""
        try:
            results = self.service.users().messages().list(
                userId='me',
                maxResults=max_results
            ).execute()
            
            messages = results.get('messages', [])
            
            if not messages:
                return "[EMPTY] No emails found."
            
            response = f"[EMAIL] Found {len(messages)} recent emails:\n\n"
            
            for msg in messages:
                msg_data = self.service.users().messages().get(
                    userId='me',
                    id=msg['id'],
                    format='metadata',
                    metadataHeaders=['From', 'Subject', 'Date']
                ).execute()
                
                headers = {h['name']: h['value'] for h in msg_data['payload']['headers']}
                
                response += f"ID: {msg['id']}\n"
                response += f"From: {headers.get('From', 'Unknown')}\n"
                response += f"Subject: {headers.get('Subject', 'No Subject')}\n"
                response += f"Date: {headers.get('Date', 'Unknown')}\n"
                response += "-" * 50 + "\n"
            
            return response
        
        except Exception as e:
            return f"[ERROR] Error listing emails: {str(e)}"
    
    def send_email(self, to: str, subject: str, body: str) -> str:
        """Send an email"""
        max_retries = 3
        for attempt in range(max_retries):
            try:
                message = MIMEText(body)
                message['to'] = to
                message['subject'] = subject
                raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
                
                self.service.users().messages().send(
                    userId='me',
                    body={'raw': raw}
                ).execute()
                
                return f"[OK] Email sent successfully to {to}\nSubject: {subject}"
            except Exception as e:
                # If it's a connection error and we have retries left, wait and retry
                if ("10053" in str(e) or "10054" in str(e)) and attempt < max_retries - 1:
                    print(f"[WARN] Connection error sending email (attempt {attempt+1}/{max_retries}). Retrying...", flush=True)
                    time.sleep(2)
                    continue
                return f"[ERROR] Error sending email: {str(e)}"
    
    def get_email(self, message_id: str) -> str:
        """Get email details"""
        try:
            msg = self.service.users().messages().get(
                userId='me',
                id=message_id,
                format='full'
            ).execute()
            
            headers = {h['name']: h['value'] for h in msg['payload']['headers']}
            
            # Get email body
            parts = msg['payload'].get('parts', [])
            body = msg['payload'].get('body', {}).get('data', '')
            
            if parts:
                for part in parts:
                    if part['mimeType'] == 'text/plain':
                        body = part['body'].get('data', '')
                        break
            
            if body:
                body = base64.urlsafe_b64decode(body).decode('utf-8')
            
            response = f"[EMAIL] Email Details:\n\n"
            response += f"From: {headers.get('From', 'Unknown')}\n"
            response += f"To: {headers.get('To', 'Unknown')}\n"
            response += f"Subject: {headers.get('Subject', 'No Subject')}\n"
            response += f"Date: {headers.get('Date', 'Unknown')}\n"
            response += f"\nBody:\n{body[:500]}..."  # First 500 chars
            
            return response
        except Exception as e:
            return f"[ERROR] Error getting email: {str(e)}"
    
    def delete_email(self, message_ids: str) -> str:
        """Delete one or more emails"""
        ids = [id.strip() for id in message_ids.split(',')]
        results = []
        
        for msg_id in ids:
            try:
                self.service.users().messages().delete(
                    userId='me',
                    id=msg_id
                ).execute()
                results.append(f"[OK] Email {msg_id} deleted")
            except Exception as e:
                results.append(f"[ERROR] Failed to delete {msg_id}: {str(e)}")
        
        return "\n".join(results)
    
    def mark_as_read(self, message_ids: str) -> str:
        """Mark one or more emails as read"""
        ids = [id.strip() for id in message_ids.split(',')]
        results = []
        
        for msg_id in ids:
            try:
                self.service.users().messages().modify(
                    userId='me',
                    id=msg_id,
                    body={'removeLabelIds': ['UNREAD']}
                ).execute()
                results.append(f"[OK] Email {msg_id} marked as read")
            except Exception as e:
                results.append(f"[ERROR] Failed to mark {msg_id}: {str(e)}")
        
        return "\n".join(results)
    
    def mark_as_unread(self, message_ids: str) -> str:
        """Mark one or more emails as unread"""
        ids = [id.strip() for id in message_ids.split(',')]
        results = []
        
        for msg_id in ids:
            try:
                self.service.users().messages().modify(
                    userId='me',
                    id=msg_id,
                    body={'addLabelIds': ['UNREAD']}
                ).execute()
                results.append(f"[OK] Email {msg_id} marked as unread")
            except Exception as e:
                results.append(f"[ERROR] Failed to mark {msg_id}: {str(e)}")
        
        return "\n".join(results)
    
    def reply_to_email(self, message_id: str, reply_text: str) -> str:
        """Reply to an email"""
        try:
            original = self.service.users().messages().get(
                userId='me',
                id=message_id
            ).execute()
            
            headers = {h['name']: h['value'] for h in original['payload']['headers']}
            
            message = MIMEText(reply_text)
            message['to'] = headers.get('From', '')
            message['subject'] = 'Re: ' + headers.get('Subject', '')
            raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
            
            self.service.users().messages().send(
                userId='me',
                body={'raw': raw, 'threadId': original['threadId']}
            ).execute()
            
            return f"[OK] Reply sent successfully to {headers.get('From', 'recipient')}"
        except Exception as e:
            return f"[ERROR] Error replying: {str(e)}"


class DriveAgent:
    """Specialized agent for Google Drive operations"""
    
    def __init__(self, drive_service, model):
        self.service = drive_service
        self.model = model
    
    def process(self, request: str, history: List[Dict]) -> str:
        """Process drive-related requests"""
        
        history_context = ""
        for turn in history[-3:]:
            history_context += f"User: {turn['user']}\nAssistant: {turn['assistant']}\n"
        
        system_prompt = f"""You are a Google Drive Agent specialized in file management.
        
        Recent Conversation:
        {history_context}
        
        Analyze this request: "{request}"
        
        Determine the action and extract parameters:
        - Actions: CREATE, UPLOAD, UPDATE, SHARE, MOVE, SEARCH, DELETE, LIST
        - For CREATE: extract 'filename' and 'content'
        - For SEARCH: extract 'query'
        - For DELETE/SHARE: extract 'file_id'
        - For LIST: no parameters needed
        
        Respond in this exact format:
        ACTION: <action>
        filename: <name>
        content: <text content>
        query: <search term>
        file_id: <id>
        
        Only include relevant parameters."""
        
        try:
            response = self.model.generate_content(system_prompt)
            parsed = self._parse_response(response.text)
            
            action = parsed.get('ACTION', '').upper()
            
            if action == 'CREATE':
                return self.create_file(
                    parsed.get('filename', 'untitled.txt'),
                    parsed.get('content', '')
                )
            elif action == 'SEARCH':
                return self.search_files(parsed.get('query', ''))
            elif action == 'DELETE':
                return self.delete_file(parsed.get('file_id', ''))
            elif action == 'SHARE':
                return self.share_file(parsed.get('file_id', ''))
            elif action == 'LIST':
                return self.list_files()
            
            return "I couldn't understand that drive request. Try: 'create file', 'search files', etc."
        
        except Exception as e:
            return f"[ERROR] Error processing drive request: {str(e)}"
    
    def _parse_response(self, text: str) -> Dict[str, str]:
        """Parse AI response into parameters"""
        params = {}
        for line in text.strip().split('\n'):
            if ':' in line:
                key, val = line.split(':', 1)
                params[key.strip()] = val.strip()
        return params
    
    def list_files(self, max_results: int = 10) -> str:
        """List recent files"""
        try:
            results = self.service.files().list(
                pageSize=max_results,
                fields="files(id, name, mimeType, webViewLink, createdTime)"
            ).execute()
            
            files = results.get('files', [])
            
            if not files:
                return "[EMPTY] No files found."
            
            response = f"[FILE] Found {len(files)} files:\n\n"
            
            for f in files:
                response += f"ID: {f['id']}\n"
                response += f"Name: {f['name']}\n"
                response += f"Type: {f.get('mimeType', 'Unknown')}\n"
                response += f"Link: {f.get('webViewLink', 'No link')}\n"
                response += f"Created: {f.get('createdTime', 'Unknown')}\n"
                response += "-" * 50 + "\n"
            
            return response
        
        except Exception as e:
            return f"[ERROR] Error listing files: {str(e)}"
    
    def create_file(self, filename: str, content: str) -> str:
        """Create a new text file in Google Drive"""
        try:
            file_metadata = {'name': filename}
            
            # Create file with content
            media = MediaIoBaseUpload(
                io.BytesIO(content.encode('utf-8')),
                mimetype='text/plain'
            )
            
            file = self.service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id, name, webViewLink'
            ).execute()
            
            return f"[OK] File '{filename}' created successfully!\n[LINK] Link: {file.get('webViewLink')}\n[ID] File ID: {file.get('id')}"
        except Exception as e:
            return f"[ERROR] Error creating file: {str(e)}"
    
    def search_files(self, query: str) -> str:
        """Search for files in Drive"""
        try:
            results = self.service.files().list(
                q=f"name contains '{query}'",
                pageSize=10,
                fields="files(id, name, mimeType, webViewLink)"
            ).execute()
            
            files = results.get('files', [])
            if not files:
                return f"[EMPTY] No files found matching '{query}'."
            
            response = f"[SEARCH] Found {len(files)} file(s) matching '{query}':\n\n"
            for f in files:
                response += f"[FILE] {f['name']}\n"
                response += f"   ID: {f['id']}\n"
                response += f"   Type: {f.get('mimeType', 'Unknown')}\n"
                response += f"   Link: {f.get('webViewLink', 'No link')}\n\n"
            
            return response
        except Exception as e:
            return f"[ERROR] Error searching: {str(e)}"
    
    def delete_file(self, file_id: str) -> str:
        """Delete a file"""
        try:
            self.service.files().delete(fileId=file_id).execute()
            return f"[OK] File {file_id} deleted successfully"
        except Exception as e:
            return f"[ERROR] Error deleting file: {str(e)}"
    
    def share_file(self, file_id: str) -> str:
        """Share a file with anyone"""
        try:
            permission = {
                'type': 'anyone',
                'role': 'reader'
            }
            self.service.permissions().create(
                fileId=file_id,
                body=permission
            ).execute()
            
            # Get file link
            file = self.service.files().get(
                fileId=file_id,
                fields='webViewLink'
            ).execute()
            
            return f"[OK] File shared successfully!\n[LINK] Link: {file.get('webViewLink')}"
        except Exception as e:
            return f"[ERROR] Error sharing file: {str(e)}"

    def get_files_data(self, max_results: int = 5) -> List[Dict[str, Any]]:
        """Get raw file data for dashboard"""
        try:
            results = self.service.files().list(
                pageSize=max_results,
                fields="files(id, name, mimeType, webViewLink, createdTime, iconLink)",
                orderBy="createdTime desc"
            ).execute()
            return results.get('files', [])
        except Exception as e:
            print(f"[ERROR] fetching files: {e}", flush=True)
            return []


class CalendarAgent:
    """Specialized agent for Google Calendar operations"""
    
    def __init__(self, calendar_service, model):
        self.service = calendar_service
        self.model = model
    
    def process(self, request: str, history: List[Dict]) -> str:
        """Process calendar-related requests"""
        
        current_time = datetime.utcnow().isoformat()
        
        history_context = ""
        for turn in history[-3:]:
            history_context += f"User: {turn['user']}\nAssistant: {turn['assistant']}\n"
        
        system_prompt = f"""You are a Google Calendar Agent specialized in calendar management.
        The current time (UTC) is: {current_time}
        
        Recent Conversation:
        {history_context}
        
        Analyze this request: "{request}"
        
        Determine the action and extract parameters:
        - Actions: CREATE, DELETE, UPDATE, GET, LIST
        - For CREATE: extract 'summary', 'start' (ISO format), 'end' (ISO format)
        - For UPDATE: extract 'event_id', and optional 'summary', 'start', 'end'
        - For DELETE: extract 'event_id'
        - For LIST/GET: no parameters or time range
        
        Respond in this exact format:
        ACTION: <action>
        summary: <event name>
        start: <ISO datetime>
        end: <ISO datetime>
        event_id: <id>
        
        For dates, use ISO format like: 2024-12-08T10:00:00
        Only include relevant parameters."""
        
        try:
            response = self.model.generate_content(system_prompt)
            parsed = self._parse_response(response.text)
            
            action = parsed.get('ACTION', '').upper()
            
            if action == 'CREATE':
                return self.create_event(
                    parsed.get('summary', 'New Event'),
                    parsed.get('start', ''),
                    parsed.get('end', '')
                )
            elif action == 'UPDATE':
                return self.update_event(
                    parsed.get('event_id', ''),
                    parsed.get('summary', ''),
                    parsed.get('start', ''),
                    parsed.get('end', '')
                )
            elif action == 'DELETE':
                return self.delete_event(parsed.get('event_id', ''))
            elif action in ['GET', 'LIST']:
                return self.get_events()
            
            return "I couldn't understand that calendar request. Try: 'create event', 'list events', etc."
        
        except Exception as e:
            return f"[ERROR] Error processing calendar request: {str(e)}"
    
    def _parse_response(self, text: str) -> Dict[str, str]:
        """Parse AI response into parameters"""
        params = {}
        for line in text.strip().split('\n'):
            if ':' in line:
                key, val = line.split(':', 1)
                params[key.strip()] = val.strip()
        return params
    
    def create_event(self, summary: str, start: str, end: str) -> str:
        """Create a calendar event"""
        try:
            # If start/end not provided, create a 1-hour event starting now
            if not start or not end:
                now = datetime.utcnow()
                start = now.isoformat() + 'Z'
                end = (now + timedelta(hours=1)).isoformat() + 'Z'
            else:
                # Ensure ISO format with Z
                if not start.endswith('Z'):
                    start += 'Z'
                if not end.endswith('Z'):
                    end += 'Z'
            
            event = {
                'summary': summary,
                'start': {'dateTime': start, 'timeZone': 'UTC'},
                'end': {'dateTime': end, 'timeZone': 'UTC'}
            }
            
            created = self.service.events().insert(
                calendarId='primary',
                body=event
            ).execute()
            
            return f"[OK] Event '{summary}' created successfully!\n[LINK] Link: {created.get('htmlLink')}\n[ID] Event ID: {created.get('id')}"
        except Exception as e:
            return f"[ERROR] Error creating event: {str(e)}"
    
    def update_event(self, event_id: str, summary: str = "", start: str = "", end: str = "") -> str:
        """Update an existing calendar event"""
        try:
            # First, get the existing event
            event = self.service.events().get(calendarId='primary', eventId=event_id).execute()
            
            # Update fields if provided
            if summary:
                event['summary'] = summary
            
            if start:
                if not start.endswith('Z'): start += 'Z'
                event['start'] = {'dateTime': start, 'timeZone': 'UTC'}
            
            if end:
                if not end.endswith('Z'): end += 'Z'
                event['end'] = {'dateTime': end, 'timeZone': 'UTC'}
            
            updated_event = self.service.events().update(
                calendarId='primary',
                eventId=event_id,
                body=event
            ).execute()
            
            return f"[OK] Event updated successfully!\n[LINK] Link: {updated_event.get('htmlLink')}"
        except Exception as e:
            return f"[ERROR] Error updating event: {str(e)}"

    def delete_event(self, event_id: str) -> str:
        """Delete a calendar event"""
        try:
            self.service.events().delete(
                calendarId='primary',
                eventId=event_id
            ).execute()
            return f"[OK] Event {event_id} deleted successfully"
        except Exception as e:
            return f"[ERROR] Error deleting event: {str(e)}"
    
    def get_events(self, max_results: int = 10) -> str:
        """Get upcoming events"""
        try:
            now = datetime.utcnow().isoformat() + 'Z'
            events_result = self.service.events().list(
                calendarId='primary',
                timeMin=now,
                maxResults=max_results,
                singleEvents=True,
                orderBy='startTime'
            ).execute()
            
            events = events_result.get('items', [])
            if not events:
                return "[EMPTY] No upcoming events found."
            
            response = f"[CALENDAR] Found {len(events)} upcoming event(s):\n\n"
            for event in events:
                start = event['start'].get('dateTime', event['start'].get('date'))
                response += f"[EVENT] {event['summary']}\n"
                response += f"   Time: {start}\n"
                response += f"   ID: {event['id']}\n"
                response += f"   Link: {event.get('htmlLink', 'No link')}\n\n"
            
            return response
        except Exception as e:
            return f"[ERROR] Error getting events: {str(e)}"

    def get_events_data(self, max_results: int = 5) -> List[Dict[str, Any]]:
        """Get raw event data for dashboard"""
        try:
            now = datetime.utcnow().isoformat() + 'Z'
            events_result = self.service.events().list(
                calendarId='primary',
                timeMin=now,
                maxResults=max_results,
                singleEvents=True,
                orderBy='startTime'
            ).execute()
            return events_result.get('items', [])
        except Exception as e:
            print(f"[ERROR] fetching events: {e}", flush=True)
            return []


# Main interface
if __name__ == "__main__":
    print("[BOT] Google Workspace Assistant Starting...")
    print("=" * 50)
    
    try:
        assistant = GoogleWorkspaceAgent()
        
        print("\n[OK] Ready! You can ask me to help with Gmail, Google Drive, or Google Calendar.")
        print("\nExamples:")
        print("  - 'Send an email to john@example.com about the meeting'")
        print("  - 'Create a file called notes.txt with some content'")
        print("  - 'Show me my upcoming calendar events'")
        print("  - 'List my recent emails'")
        print("\nType 'quit' to exit.\n")
        
        while True:
            user_input = input("You: ").strip()
            
            if user_input.lower() in ['quit', 'exit', 'q']:
                print("\n[BYE] Goodbye!")
                break
            
            if not user_input:
                continue
            
            print("\n[...] Processing...\n")
            response = assistant.process_request(user_input)
            print(f"Assistant: {response}\n")
            print("-" * 50 + "\n")
    
    except KeyboardInterrupt:
        print("\n\n[BYE] Goodbye!")
    except Exception as e:
        print(f"\n[ERROR] Error initializing assistant: {str(e)}")
        print("\nMake sure:")
        print("1. credentials.json is in the same directory")
        print("2. You have enabled Gmail, Drive, and Calendar APIs")
        print("3. pip install requests google-auth-oauthlib google-api-python-client")