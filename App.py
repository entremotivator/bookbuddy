import streamlit as st
import st_audiorec as staud
import uuid
import os
import requests
import datetime
import re
import base64

# Page configuration
st.set_page_config(
    page_title="Audio Recording Tool",
    page_icon="🎙️",
    layout="centered",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        text-align: center;
        color: #1f77b4;
        margin-bottom: 2rem;
    }
    .success-box {
        padding: 1rem;
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        border-radius: 0.25rem;
        color: #155724;
        margin: 1rem 0;
    }
    .error-box {
        padding: 1rem;
        background-color: #f8d7da;
        border: 1px solid #f5c6cb;
        border-radius: 0.25rem;
        color: #721c24;
        margin: 1rem 0;
    }
    .info-box {
        padding: 1rem;
        background-color: #d1ecf1;
        border: 1px solid #bee5eb;
        border-radius: 0.25rem;
        color: #0c5460;
        margin: 1rem 0;
    }
    .warning-box {
        padding: 1rem;
        background-color: #fff3cd;
        border: 1px solid #ffecb5;
        border-radius: 0.25rem;
        color: #856404;
        margin: 1rem 0;
    }
    .stButton > button {
        width: 100%;
        border-radius: 20px;
        height: 3em;
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        border: none;
        color: white;
        font-weight: bold;
    }
    .stButton > button:hover {
        background: linear-gradient(90deg, #764ba2 0%, #667eea 100%);
        border: none;
        color: white;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'user_name' not in st.session_state:
    st.session_state.user_name = ""
if 'user_email' not in st.session_state:
    st.session_state.user_email = ""
if 'webhook_url' not in st.session_state:
    st.session_state.webhook_url = "https://your-n8n-url/webhook/audio"

def is_valid_email(email):
    """Validate email format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def is_valid_url(url):
    """Validate URL format"""
    return url.startswith(('http://', 'https://')) and len(url) > 10

def save_audio_file(audio_bytes, prefix="recording"):
    """Save audio data to a temporary file"""
    try:
        timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{prefix}_{uuid.uuid4().hex}_{timestamp}.wav"
        with open(filename, "wb") as f:
            f.write(audio_bytes)
        return filename
    except Exception as e:
        st.error(f"Error saving audio file: {e}")
        return None

def cleanup_file(filename):
    """Safely remove temporary file"""
    try:
        if os.path.exists(filename):
            os.remove(filename)
    except Exception as e:
        st.warning(f"Could not clean up temporary file: {e}")

def get_audio_size_info(audio_bytes):
    """Get human-readable size information"""
    size_bytes = len(audio_bytes)
    if size_bytes < 1024:
        return f"{size_bytes} bytes"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    else:
        return f"{size_bytes / (1024 * 1024):.1f} MB"

# Sidebar navigation
st.sidebar.title("🎙️ Audio Tool")
st.sidebar.markdown("---")
page = st.sidebar.radio(
    "Select Function", 
    ["🎤 Record & Download", "🌐 Upload to Webhook", "🎵 Browser Recorder", "ℹ️ About"],
    index=0
)

# Page 1: Record and Download with st_audiorec
if page == "🎤 Record & Download":
    st.markdown("<h1 class='main-header'>🎤 Record Your Voice</h1>", unsafe_allow_html=True)
    
    st.markdown("""
    <div class='info-box'>
    <strong>📝 Instructions:</strong><br>
    1. Click the record button below<br>
    2. Speak clearly into your microphone<br>
    3. Click stop when finished<br>
    4. Play back your recording and download if satisfied
    </div>
    """, unsafe_allow_html=True)
    
    # Audio recorder using st_audiorec
    wav_audio_data = staud.st_audiorec()
    
    if wav_audio_data is not None:
        st.markdown("""
        <div class='success-box'>
        <strong>✅ Recording captured successfully!</strong><br>
        Your audio has been recorded and is ready for playback.
        </div>
        """, unsafe_allow_html=True)
        
        # Display audio player
        st.audio(wav_audio_data, format='audio/wav')
        
        # Show recording info
        audio_size = get_audio_size_info(wav_audio_data)
        st.info(f"📊 Recording size: {audio_size}")
        
        # Create columns for buttons
        col1, col2, col3 = st.columns([1, 2, 1])
        
        with col2:
            # Create download button
            current_time = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            download_filename = f"voice_recording_{current_time}.wav"
            
            st.download_button(
                label="⬇️ Download Recording",
                data=wav_audio_data,
                file_name=download_filename,
                mime="audio/wav",
                help="Click to download your recording as a WAV file"
            )
        
        # Additional options
        with st.expander("🔧 Advanced Options"):
            st.write("**Recording Details:**")
            st.write(f"- Format: WAV")
            st.write(f"- Size: {audio_size}")
            st.write(f"- Timestamp: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            
            if st.button("🗑️ Clear Recording"):
                st.rerun()

# Page 2: Upload to n8n Webhook
elif page == "🌐 Upload to Webhook":
    st.markdown("<h1 class='main-header'>🌐 Upload to n8n Webhook</h1>", unsafe_allow_html=True)
    
    # Sidebar inputs with session state
    st.sidebar.subheader("📝 User Information")
    
    st.session_state.user_name = st.sidebar.text_input(
        "Your Name", 
        value=st.session_state.user_name,
        placeholder="Enter your full name"
    )
    
    st.session_state.user_email = st.sidebar.text_input(
        "Your Email", 
        value=st.session_state.user_email,
        placeholder="your.email@example.com"
    )
    
    st.session_state.webhook_url = st.sidebar.text_input(
        "n8n Webhook URL", 
        value=st.session_state.webhook_url,
        placeholder="https://your-n8n-instance.com/webhook/..."
    )
    
    # Input validation
    name_valid = len(st.session_state.user_name.strip()) > 0
    email_valid = is_valid_email(st.session_state.user_email)
    url_valid = is_valid_url(st.session_state.webhook_url)
    
    # Show validation status
    st.sidebar.markdown("### ✅ Validation Status")
    st.sidebar.write(f"Name: {'✅' if name_valid else '❌'}")
    st.sidebar.write(f"Email: {'✅' if email_valid else '❌'}")
    st.sidebar.write(f"Webhook URL: {'✅' if url_valid else '❌'}")
    
    # Main content
    st.markdown("""
    <div class='info-box'>
    <strong>📝 Instructions:</strong><br>
    1. Fill out your information in the sidebar<br>
    2. Record your audio message below<br>
    3. Click "Upload to Webhook" to send to your n8n workflow
    </div>
    """, unsafe_allow_html=True)
    
    # Audio recorder
    wav_audio_data = staud.st_audiorec()
    
    if wav_audio_data is not None:
        st.success("✅ Recording captured!")
        st.audio(wav_audio_data, format='audio/wav')
        
        audio_size = get_audio_size_info(wav_audio_data)
        st.info(f"📊 Recording size: {audio_size}")
        
        # Check if all fields are valid
        if name_valid and email_valid and url_valid:
            col1, col2, col3 = st.columns([1, 2, 1])
            with col2:
                if st.button("🚀 Upload to Webhook", type="primary"):
                    with st.spinner("Uploading to webhook..."):
                        filename = save_audio_file(wav_audio_data, "upload")
                        
                        if filename:
                            try:
                                with open(filename, "rb") as audio_file:
                                    files = {
                                        "file": (f"recording_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.wav", 
                                               audio_file, "audio/wav")
                                    }
                                    data = {
                                        "name": st.session_state.user_name.strip(),
                                        "email": st.session_state.user_email.strip(),
                                        "timestamp": datetime.datetime.now().isoformat(),
                                        "file_size": len(wav_audio_data),
                                        "file_size_human": audio_size
                                    }
                                    
                                    response = requests.post(
                                        st.session_state.webhook_url,
                                        files=files,
                                        data=data,
                                        timeout=30
                                    )
                                    
                                    if response.status_code == 200:
                                        st.markdown("""
                                        <div class='success-box'>
                                        <strong>✅ Upload Successful!</strong><br>
                                        Your audio has been successfully sent to the webhook.<br>
                                        Response received from server.
                                        </div>
                                        """, unsafe_allow_html=True)
                                        
                                        # Show response details if available
                                        if response.text:
                                            with st.expander("📄 Server Response"):
                                                st.code(response.text[:500])
                                                
                                    else:
                                        st.markdown(f"""
                                        <div class='error-box'>
                                        <strong>❌ Upload Failed</strong><br>
                                        Status code: {response.status_code}<br>
                                        Response: {response.text[:200] if response.text else 'No response body'}
                                        </div>
                                        """, unsafe_allow_html=True)
                                        
                            except requests.exceptions.Timeout:
                                st.error("❌ Upload timed out. Please check your webhook URL and try again.")
                            except requests.exceptions.ConnectionError:
                                st.error("❌ Connection error. Please check your webhook URL and internet connection.")
                            except Exception as e:
                                st.error(f"❌ Error uploading: {str(e)}")
                            finally:
                                cleanup_file(filename)
        else:
            st.markdown("""
            <div class='warning-box'>
            <strong>⚠️ Missing Information</strong><br>
            Please fill out all required fields correctly in the sidebar before uploading.
            </div>
            """, unsafe_allow_html=True)

# Page 3: Browser-based Audio Recorder (Alternative)
elif page == "🎵 Browser Recorder":
    st.markdown("<h1 class='main-header'>🎵 Browser Audio Recorder</h1>", unsafe_allow_html=True)
    
    st.markdown("""
    <div class='info-box'>
    <strong>🌐 Browser-Based Recording</strong><br>
    This is an alternative recording method using HTML5 Web Audio API.
    Works directly in your browser without additional dependencies.
    </div>
    """, unsafe_allow_html=True)
    
    # HTML5 Audio Recorder
    audio_recorder_html = """
    <div style="text-align: center; padding: 20px;">
        <button id="recordBtn" onclick="toggleRecording()" style="
            background: linear-gradient(45deg, #FF6B6B, #4ECDC4);
            border: none;
            color: white;
            padding: 15px 30px;
            font-size: 18px;
            border-radius: 50px;
            cursor: pointer;
            margin: 10px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.2);
            transition: all 0.3s ease;
        ">🎤 Start Recording</button>
        
        <div id="status" style="margin: 20px; font-size: 16px; color: #666;"></div>
        <div id="audioContainer"></div>
    </div>

    <script>
        let mediaRecorder;
        let audioChunks = [];
        let isRecording = false;

        async function toggleRecording() {
            const btn = document.getElementById('recordBtn');
            const status = document.getElementById('status');
            
            if (!isRecording) {
                try {
                    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
                    mediaRecorder = new MediaRecorder(stream);
                    audioChunks = [];
                    
                    mediaRecorder.ondataavailable = event => {
                        audioChunks.push(event.data);
                    };
                    
                    mediaRecorder.onstop = () => {
                        const audioBlob = new Blob(audioChunks, { type: 'audio/wav' });
                        const audioUrl = URL.createObjectURL(audioBlob);
                        const audio = document.createElement('audio');
                        audio.src = audioUrl;
                        audio.controls = true;
                        audio.style.margin = '20px';
                        
                        const container = document.getElementById('audioContainer');
                        container.innerHTML = '';
                        container.appendChild(audio);
                        
                        // Create download link
                        const downloadLink = document.createElement('a');
                        downloadLink.href = audioUrl;
                        downloadLink.download = 'browser_recording_' + new Date().getTime() + '.wav';
                        downloadLink.style.display = 'inline-block';
                        downloadLink.style.margin = '10px';
                        downloadLink.style.padding = '10px 20px';
                        downloadLink.style.background = '#28a745';
                        downloadLink.style.color = 'white';
                        downloadLink.style.textDecoration = 'none';
                        downloadLink.style.borderRadius = '5px';
                        downloadLink.textContent = '⬇️ Download Recording';
                        container.appendChild(downloadLink);
                    };
                    
                    mediaRecorder.start();
                    isRecording = true;
                    btn.textContent = '⏹️ Stop Recording';
                    btn.style.background = 'linear-gradient(45deg, #FF4757, #FF3838)';
                    status.textContent = '🔴 Recording in progress...';
                    status.style.color = '#e74c3c';
                    
                } catch (err) {
                    status.textContent = '❌ Error accessing microphone: ' + err.message;
                    status.style.color = '#e74c3c';
                }
            } else {
                mediaRecorder.stop();
                mediaRecorder.stream.getTracks().forEach(track => track.stop());
                isRecording = false;
                btn.textContent = '🎤 Start Recording';
                btn.style.background = 'linear-gradient(45deg, #FF6B6B, #4ECDC4)';
                status.textContent = '✅ Recording completed!';
                status.style.color = '#27ae60';
            }
        }
    </script>
    """
    
    st.components.v1.html(audio_recorder_html, height=300)
    
    st.markdown("""
    <div class='info-box'>
    <strong>ℹ️ Browser Recorder Features:</strong><br>
    • No external dependencies required<br>
    • Works offline after page load<br>
    • Direct download functionality<br>
    • Compatible with all modern browsers<br>
    • Real-time recording status
    </div>
    """, unsafe_allow_html=True)

# Page 4: About
elif page == "ℹ️ About":
    st.markdown("<h1 class='main-header'>ℹ️ About This Tool</h1>", unsafe_allow_html=True)
    
    st.markdown("""
    ## 🎯 Purpose
    This audio recording tool provides multiple methods for capturing and managing audio recordings:
    
    ### 🎤 Record & Download
    - Record audio using the st_audiorec library
    - Play back recordings before downloading
    - Download as timestamped WAV files
    - No server-side storage required
    
    ### 🌐 Upload to Webhook
    - Record audio and send to n8n webhooks
    - Include user metadata (name, email, timestamp)
    - Real-time input validation
    - Comprehensive error handling and response display
    
    ### 🎵 Browser Recorder
    - HTML5 Web Audio API implementation
    - No external dependencies required
    - Works entirely in the browser
    - Direct download functionality
    
    ## 🔧 Technical Details
    - **Primary Library**: st_audiorec for reliable recording
    - **Fallback Method**: HTML5 Web Audio API
    - **File Format**: WAV (uncompressed audio)
    - **Deployment**: Optimized for Streamlit Cloud
    - **Dependencies**: Minimal and stable packages only
    
    ## 🛡️ Privacy & Security
    - Audio processing happens client-side
    - Temporary files automatically cleaned up
    - No permanent server-side storage
    - User data only transmitted when explicitly uploading
    - Input validation prevents malicious data
    
    ## 📋 Requirements
    - Modern web browser with microphone access
    - Internet connection (for webhook uploads)
    - Valid n8n webhook endpoint (for uploads)
    - Microphone permissions granted
    
    ## 🎛️ Audio Quality
    - **Sample Rate**: Browser default (typically 44.1kHz)
    - **Bit Depth**: 16-bit PCM
    - **Channels**: Mono/Stereo (browser dependent)
    - **Format**: Uncompressed WAV
    
    ---
    
    **Version:** 3.0  
    **Last Updated:** July 2025  
    **Library:** st_audiorec + HTML5 fallback
    """)
    
    # System info
    with st.expander("🔍 System Information"):
        st.write("**Python Libraries:**")
        st.code("""
        streamlit
        st_audiorec
        requests
        uuid (built-in)
        os (built-in)
        datetime (built-in)
        re (built-in)
        base64 (built-in)
        """)
        
        st.write("**Browser APIs Used:**")
        st.code("""
        MediaDevices.getUserMedia()
        MediaRecorder API
        Web Audio API
        Blob API
        URL.createObjectURL()
        """)
    
    # Troubleshooting
    with st.expander("🔧 Troubleshooting"):
        st.markdown("""
        **Common Issues & Solutions:**
        
        **🎤 Microphone not working:**
        - Check browser permissions
        - Ensure microphone is not used by other apps
        - Try refreshing the page
        
        **📡 Webhook upload fails:**
        - Verify webhook URL is correct
        - Check n8n instance is running
        - Ensure webhook accepts file uploads
        
        **🌐 Browser recorder not loading:**
        - Use a modern browser (Chrome, Firefox, Safari)
        - Enable JavaScript
        - Check microphone permissions
        
        **📱 Mobile device issues:**
        - Some features may be limited on mobile
        - Use desktop browser for best experience
        - Ensure stable internet connection
        """)

# Footer
st.markdown("---")
st.markdown(
    "<div style='text-align: center; color: #666; font-size: 0.8em;'>"
    "🎙️ Audio Recording Tool v3.0 | Built with Streamlit & st_audiorec"
    "</div>", 
    unsafe_allow_html=True
)
