import streamlit as st
from audio_recorder_streamlit import audio_recorder
import requests
import pandas as pd
import io
import time
from datetime import datetime

# Page configuration
st.set_page_config(
    page_title="🎧 AI Book Buddy Recorder",
    page_icon="🎙️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        text-align: center;
        padding: 2rem 0;
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        color: white;
        border-radius: 10px;
        margin-bottom: 2rem;
    }
    
    .recording-section {
        background: #f8f9fa;
        padding: 2rem;
        border-radius: 15px;
        border: 2px solid #e9ecef;
        margin: 1rem 0;
    }
    
    .stats-card {
        background: white;
        padding: 1.5rem;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        text-align: center;
        margin: 0.5rem;
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
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'recordings' not in st.session_state:
    st.session_state.recordings = []
if 'total_duration' not in st.session_state:
    st.session_state.total_duration = 0

# Main header
st.markdown("""
<div class="main-header">
    <h1>🎙️ AI Book Buddy - Audiobook Recorder</h1>
    <p>Professional audiobook recording and management platform</p>
</div>
""", unsafe_allow_html=True)

# Sidebar configuration
with st.sidebar:
    st.title("📤 Recording Settings")
    
    # Webhook configuration
    st.subheader("n8n Webhook Integration")
    webhook_url = st.text_input(
        "n8n Webhook URL", 
        placeholder="https://example.com/webhook",
        help="Enter your n8n webhook URL for automated processing"
    )
    
    # Recording settings
    st.subheader("Recording Configuration")
    filename = st.text_input(
        "Recording Name", 
        value=f"chapter_{len(st.session_state.recordings) + 1}_audio",
        help="Name for your audio recording"
    )
    
    # Audio quality settings
    sample_rate = st.selectbox(
        "Sample Rate",
        [22050, 44100, 48000],
        index=1,
        help="Higher sample rates provide better quality but larger files"
    )
    
    pause_threshold = st.slider(
        "Pause Threshold (seconds)",
        min_value=1.0,
        max_value=5.0,
        value=2.0,
        step=0.5,
        help="Time to wait before stopping recording automatically"
    )
    
    # Recording statistics
    st.subheader("📊 Session Statistics")
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Total Recordings", len(st.session_state.recordings))
    with col2:
        st.metric("Total Duration", f"{st.session_state.total_duration:.1f}s")

# Main content area
col1, col2 = st.columns([2, 1])

with col1:
    st.markdown("""
    <div class="recording-section">
    """, unsafe_allow_html=True)
    
    st.markdown("### 🎤 Recording Studio")
    st.markdown("""
    Use this professional recording interface to capture chapters or segments of your audiobook. 
    Click the microphone below to start and stop recording. Your audio will be automatically 
    processed and can be sent to your n8n workflow for further automation.
    """)
    
    # Audio recorder with enhanced settings
    audio_bytes = audio_recorder(
        text="🎙️ Start Recording",
        recording_color="#e63946",   # red while recording
        neutral_color="#457b9d",     # blue when idle
        icon_name="microphone",
        icon_size="4x",
        pause_threshold=pause_threshold,
        sample_rate=sample_rate,
        key="audio_recorder"
    )
    
    st.markdown("</div>", unsafe_allow_html=True)

with col2:
    st.markdown("### 🎛️ Quick Actions")
    
    # Quick recording templates
    if st.button("📖 Chapter Recording", use_container_width=True):
        st.session_state.recording_type = "chapter"
        st.info("Chapter recording mode activated")
    
    if st.button("🎵 Intro/Outro", use_container_width=True):
        st.session_state.recording_type = "intro_outro"
        st.info("Intro/Outro recording mode activated")
    
    if st.button("🔄 Retake", use_container_width=True):
        st.session_state.recording_type = "retake"
        st.warning("Retake mode activated")
    
    # Recording tips
    st.markdown("### 💡 Recording Tips")
    st.markdown("""
    - Find a quiet environment
    - Speak clearly and at a steady pace
    - Keep consistent distance from microphone
    - Take breaks between chapters
    - Review recordings before finalizing
    """)

# Handle audio output
if audio_bytes:
    st.markdown("""
    <div class="success-message">
        ✅ Audio recorded successfully! Duration: {:.1f} seconds
    </div>
    """.format(len(audio_bytes) / (sample_rate * 2)), unsafe_allow_html=True)
    
    # Audio playback
    st.audio(audio_bytes, format="audio/wav")
    
    # Recording metadata
    recording_info = {
        'name': filename,
        'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        'duration': len(audio_bytes) / (sample_rate * 2),
        'sample_rate': sample_rate,
        'size_kb': len(audio_bytes) / 1024
    }
    
    # Display recording info
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Duration", f"{recording_info['duration']:.1f}s")
    with col2:
        st.metric("Sample Rate", f"{recording_info['sample_rate']} Hz")
    with col3:
        st.metric("File Size", f"{recording_info['size_kb']:.1f} KB")
    with col4:
        st.metric("Quality", "High" if sample_rate >= 44100 else "Standard")
    
    # Action buttons
    col1, col2, col3 = st.columns(3)
    
    with col1:
        # Download button
        st.download_button(
            label="⬇️ Download Audio",
            data=audio_bytes,
            file_name=f"{filename}.wav",
            mime="audio/wav",
            use_container_width=True
        )
    
    with col2:
        # Save to session
        if st.button("💾 Save to Session", use_container_width=True):
            st.session_state.recordings.append(recording_info)
            st.session_state.total_duration += recording_info['duration']
            st.success("Recording saved to session!")
            st.rerun()
    
    with col3:
        # Send to webhook
        if webhook_url and st.button("🚀 Send to n8n", use_container_width=True):
            try:
                with st.spinner("Sending to n8n webhook..."):
                    files = {"file": (f"{filename}.wav", audio_bytes, "audio/wav")}
                    data = {
                        "name": filename,
                        "timestamp": recording_info['timestamp'],
                        "duration": recording_info['duration'],
                        "sample_rate": recording_info['sample_rate']
                    }
                    response = requests.post(webhook_url, files=files, data=data, timeout=30)
                    
                    if response.status_code == 200:
                        st.markdown("""
                        <div class="success-message">
                            ✅ Audio sent to n8n successfully!
                        </div>
                        """, unsafe_allow_html=True)
                    else:
                        st.markdown(f"""
                        <div class="error-message">
                            ❌ Failed with status code {response.status_code}
                        </div>
                        """, unsafe_allow_html=True)
            except Exception as e:
                st.markdown(f"""
                <div class="error-message">
                    ⚠️ Error sending to webhook: {str(e)}
                </div>
                """, unsafe_allow_html=True)

# Recording history
if st.session_state.recordings:
    st.markdown("### 📚 Recording History")
    
    # Convert to DataFrame for better display
    df = pd.DataFrame(st.session_state.recordings)
    
    # Display as a nice table
    st.dataframe(
        df,
        use_container_width=True,
        column_config={
            "name": "Recording Name",
            "timestamp": "Recorded At",
            "duration": st.column_config.NumberColumn("Duration (s)", format="%.1f"),
            "sample_rate": "Sample Rate (Hz)",
            "size_kb": st.column_config.NumberColumn("Size (KB)", format="%.1f")
        }
    )
    
    # Bulk actions
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("📊 Export Session Report"):
            report = df.to_csv(index=False)
            st.download_button(
                "Download Report",
                report,
                f"recording_session_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                "text/csv"
            )
    
    with col2:
        if st.button("🗑️ Clear History"):
            st.session_state.recordings = []
            st.session_state.total_duration = 0
            st.rerun()
    
    with col3:
        if st.button("📈 View Analytics"):
            st.info("Analytics feature coming soon!")

# Footer
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #666; padding: 1rem;">
    🎧 AI Book Buddy Recorder v2.0 | Built with Streamlit | 
    <a href="#" style="color: #667eea;">Documentation</a> | 
    <a href="#" style="color: #667eea;">Support</a>
</div>
""", unsafe_allow_html=True)

