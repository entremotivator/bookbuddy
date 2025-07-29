import streamlit as st
import json
import requests
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import os
import tempfile
from datetime import datetime
import pandas as pd

# Page configuration
st.set_page_config(
    page_title="📄 Google Docs Live Viewer",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        text-align: center;
        padding: 2rem 0;
        background: linear-gradient(90deg, #4285f4 0%, #34a853 100%);
        color: white;
        border-radius: 10px;
        margin-bottom: 2rem;
    }
    
    .auth-section {
        background: #f8f9fa;
        padding: 2rem;
        border-radius: 15px;
        border: 2px solid #e9ecef;
        margin: 1rem 0;
    }
    
    .doc-content {
        background: white;
        padding: 2rem;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        margin: 1rem 0;
        max-height: 600px;
        overflow-y: auto;
    }
    
    .success-message {
        background: #d4edda;
        color: #155724;
        padding: 1rem;
        border-radius: 8px;
        border: 1px solid #c3e6cb;
        margin: 1rem 0;
    }
    
    .error-message {
        background: #f8d7da;
        color: #721c24;
        padding: 1rem;
        border-radius: 8px;
        border: 1px solid #f5c6cb;
        margin: 1rem 0;
    }
    
    .info-card {
        background: #e3f2fd;
        padding: 1.5rem;
        border-radius: 10px;
        border-left: 4px solid #2196f3;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'google_credentials' not in st.session_state:
    st.session_state.google_credentials = None
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
if 'doc_content' not in st.session_state:
    st.session_state.doc_content = None
if 'doc_metadata' not in st.session_state:
    st.session_state.doc_metadata = None

# Google API configuration
SCOPES = [
    'https://www.googleapis.com/auth/documents.readonly',
    'https://www.googleapis.com/auth/drive.readonly'
]

# Main header
st.markdown("""
<div class="main-header">
    <h1>📄 Google Docs Live Viewer</h1>
    <p>View and monitor Google Documents in real-time</p>
</div>
""", unsafe_allow_html=True)

# Sidebar for authentication
with st.sidebar:
    st.title("🔐 Google Authentication")
    
    # Authentication file upload
    st.subheader("Upload Credentials")
    uploaded_file = st.file_uploader(
        "Upload Google OAuth2 JSON file",
        type=['json'],
        help="Upload your Google OAuth2 credentials JSON file from Google Cloud Console"
    )
    
    if uploaded_file is not None:
        try:
            credentials_data = json.load(uploaded_file)
            st.session_state.credentials_data = credentials_data
            st.success("✅ Credentials file loaded successfully!")
            
            # Display some info about the credentials
            if 'web' in credentials_data:
                client_info = credentials_data['web']
                st.info(f"**Client ID:** {client_info.get('client_id', 'N/A')[:20]}...")
                st.info(f"**Project ID:** {client_info.get('project_id', 'N/A')}")
            
        except Exception as e:
            st.error(f"❌ Error loading credentials: {str(e)}")
    
    # Manual credentials input
    st.subheader("Manual Configuration")
    with st.expander("Enter credentials manually"):
        client_id = st.text_input("Client ID", type="password")
        client_secret = st.text_input("Client Secret", type="password")
        redirect_uri = st.text_input("Redirect URI", value="http://localhost:8501")
        
        if st.button("Save Manual Credentials"):
            if client_id and client_secret:
                manual_creds = {
                    "web": {
                        "client_id": client_id,
                        "client_secret": client_secret,
                        "redirect_uris": [redirect_uri],
                        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                        "token_uri": "https://oauth2.googleapis.com/token"
                    }
                }
                st.session_state.credentials_data = manual_creds
                st.success("Manual credentials saved!")
    
    # Authentication status
    st.subheader("Authentication Status")
    if st.session_state.authenticated:
        st.success("✅ Authenticated")
        if st.button("🔓 Logout"):
            st.session_state.authenticated = False
            st.session_state.google_credentials = None
            st.rerun()
    else:
        st.warning("❌ Not authenticated")
    
    # Document settings
    st.subheader("📄 Document Settings")
    doc_id = st.text_input(
        "Google Doc ID",
        help="Enter the Google Document ID from the URL"
    )
    
    auto_refresh = st.checkbox("Auto-refresh (30s)", value=False)
    
    if auto_refresh:
        st.info("🔄 Auto-refresh enabled")

# Main content area
def authenticate_google():
    """Handle Google OAuth2 authentication"""
    if 'credentials_data' not in st.session_state:
        st.error("Please upload credentials file first!")
        return False
    
    try:
        # Create a temporary file for credentials
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(st.session_state.credentials_data, f)
            temp_creds_path = f.name
        
        # Create OAuth2 flow
        flow = Flow.from_client_secrets_file(
            temp_creds_path,
            scopes=SCOPES,
            redirect_uri='http://localhost:8501'
        )
        
        # Generate authorization URL
        auth_url, _ = flow.authorization_url(prompt='consent')
        
        st.markdown(f"""
        <div class="info-card">
            <h4>🔗 Authentication Required</h4>
            <p>Click the link below to authenticate with Google:</p>
            <a href="{auth_url}" target="_blank" style="color: #1976d2; font-weight: bold;">
                🔐 Authenticate with Google
            </a>
        </div>
        """, unsafe_allow_html=True)
        
        # Input for authorization code
        auth_code = st.text_input(
            "Enter authorization code:",
            help="Copy the authorization code from the redirect URL"
        )
        
        if auth_code:
            try:
                # Exchange code for credentials
                flow.fetch_token(code=auth_code)
                credentials = flow.credentials
                
                # Store credentials in session state
                st.session_state.google_credentials = {
                    'token': credentials.token,
                    'refresh_token': credentials.refresh_token,
                    'token_uri': credentials.token_uri,
                    'client_id': credentials.client_id,
                    'client_secret': credentials.client_secret,
                    'scopes': credentials.scopes
                }
                st.session_state.authenticated = True
                
                # Clean up temp file
                os.unlink(temp_creds_path)
                
                st.success("✅ Authentication successful!")
                st.rerun()
                
            except Exception as e:
                st.error(f"❌ Authentication failed: {str(e)}")
                os.unlink(temp_creds_path)
        
        return False
        
    except Exception as e:
        st.error(f"❌ Error setting up authentication: {str(e)}")
        return False

def get_google_doc_content(doc_id):
    """Fetch Google Doc content"""
    if not st.session_state.authenticated or not st.session_state.google_credentials:
        return None, None
    
    try:
        # Create credentials object
        creds = Credentials(
            token=st.session_state.google_credentials['token'],
            refresh_token=st.session_state.google_credentials['refresh_token'],
            token_uri=st.session_state.google_credentials['token_uri'],
            client_id=st.session_state.google_credentials['client_id'],
            client_secret=st.session_state.google_credentials['client_secret'],
            scopes=st.session_state.google_credentials['scopes']
        )
        
        # Build the service
        service = build('docs', 'v1', credentials=creds)
        
        # Retrieve the document
        document = service.documents().get(documentId=doc_id).execute()
        
        # Extract text content
        content = []
        for element in document.get('body', {}).get('content', []):
            if 'paragraph' in element:
                paragraph = element['paragraph']
                for text_run in paragraph.get('elements', []):
                    if 'textRun' in text_run:
                        content.append(text_run['textRun']['content'])
        
        # Document metadata
        metadata = {
            'title': document.get('title', 'Untitled'),
            'document_id': document.get('documentId'),
            'revision_id': document.get('revisionId'),
            'created_time': document.get('createdTime'),
            'modified_time': document.get('modifiedTime')
        }
        
        return ''.join(content), metadata
        
    except HttpError as e:
        st.error(f"❌ Google API Error: {str(e)}")
        return None, None
    except Exception as e:
        st.error(f"❌ Error fetching document: {str(e)}")
        return None, None

# Main interface
if not st.session_state.authenticated:
    st.markdown("""
    <div class="auth-section">
    """, unsafe_allow_html=True)
    
    st.markdown("### 🔐 Authentication Required")
    st.markdown("""
    To view Google Docs, you need to authenticate with Google. Please upload your 
    OAuth2 credentials file in the sidebar and follow the authentication process.
    """)
    
    if st.button("🚀 Start Authentication", use_container_width=True):
        authenticate_google()
    
    st.markdown("</div>", unsafe_allow_html=True)
    
    # Instructions for getting credentials
    with st.expander("📋 How to get Google OAuth2 credentials"):
        st.markdown("""
        1. Go to [Google Cloud Console](https://console.cloud.google.com/)
        2. Create a new project or select existing one
        3. Enable Google Docs API and Google Drive API
        4. Go to "Credentials" → "Create Credentials" → "OAuth 2.0 Client IDs"
        5. Set application type to "Web application"
        6. Add `http://localhost:8501` to authorized redirect URIs
        7. Download the JSON file and upload it here
        """)

else:
    # Document viewer interface
    col1, col2 = st.columns([3, 1])
    
    with col1:
        st.markdown("### 📄 Document Viewer")
        
        if doc_id:
            # Fetch document button
            col_a, col_b, col_c = st.columns(3)
            with col_a:
                if st.button("🔄 Refresh Document", use_container_width=True):
                    with st.spinner("Fetching document..."):
                        content, metadata = get_google_doc_content(doc_id)
                        if content is not None:
                            st.session_state.doc_content = content
                            st.session_state.doc_metadata = metadata
            
            with col_b:
                if st.button("📋 Copy Content", use_container_width=True):
                    if st.session_state.doc_content:
                        st.code(st.session_state.doc_content)
            
            with col_c:
                if st.button("💾 Download as Text", use_container_width=True):
                    if st.session_state.doc_content:
                        st.download_button(
                            "Download",
                            st.session_state.doc_content,
                            f"google_doc_{doc_id}.txt",
                            "text/plain"
                        )
            
            # Display document content
            if st.session_state.doc_content:
                # Document metadata
                if st.session_state.doc_metadata:
                    metadata = st.session_state.doc_metadata
                    st.markdown(f"**Title:** {metadata.get('title', 'N/A')}")
                    st.markdown(f"**Last Modified:** {metadata.get('modified_time', 'N/A')}")
                    st.markdown(f"**Document ID:** {metadata.get('document_id', 'N/A')}")
                
                # Document content
                st.markdown("""
                <div class="doc-content">
                """, unsafe_allow_html=True)
                
                st.markdown(st.session_state.doc_content)
                
                st.markdown("</div>", unsafe_allow_html=True)
            
            else:
                st.info("👆 Click 'Refresh Document' to load content")
        
        else:
            st.info("📝 Enter a Google Doc ID in the sidebar to get started")
    
    with col2:
        st.markdown("### 📊 Document Info")
        
        if st.session_state.doc_metadata:
            metadata = st.session_state.doc_metadata
            
            # Document statistics
            if st.session_state.doc_content:
                word_count = len(st.session_state.doc_content.split())
                char_count = len(st.session_state.doc_content)
                
                st.metric("Word Count", word_count)
                st.metric("Character Count", char_count)
                st.metric("Estimated Reading Time", f"{word_count // 200} min")
            
            # Document details
            st.markdown("**Document Details:**")
            st.text(f"Title: {metadata.get('title', 'N/A')}")
            st.text(f"Revision: {metadata.get('revision_id', 'N/A')}")
            
            # Last update
            if metadata.get('modified_time'):
                st.markdown(f"**Last Updated:**")
                st.text(metadata['modified_time'])
        
        # Quick actions
        st.markdown("### ⚡ Quick Actions")
        
        if st.button("🔗 Open in Google Docs", use_container_width=True):
            if doc_id:
                st.markdown(f"[Open Document](https://docs.google.com/document/d/{doc_id}/edit)")
        
        if st.button("📤 Share Document", use_container_width=True):
            if doc_id:
                share_url = f"https://docs.google.com/document/d/{doc_id}/edit"
                st.code(share_url)

# Auto-refresh functionality
if auto_refresh and st.session_state.authenticated and doc_id:
    import time
    time.sleep(30)
    st.rerun()

# Footer
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #666; padding: 1rem;">
    📄 Google Docs Live Viewer | Powered by Google Docs API | 
    <a href="https://developers.google.com/docs" style="color: #4285f4;">API Documentation</a>
</div>
""", unsafe_allow_html=True)

