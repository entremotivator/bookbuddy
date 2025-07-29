import streamlit as st
from streamlit_webrtc import webrtc_streamer, AudioProcessorBase, ClientSettings
import av
import numpy as np
import wave
import io
import uuid
import os
import requests

st.set_page_config(page_title="Audio Tool", layout="centered")

# Sidebar navigation
page = st.sidebar.radio("Select Page", ["🎙️ Record & Download", "🌐 Upload to n8n Webhook"])

# Audio processor for capturing mic input
class AudioProcessor(AudioProcessorBase):
    def __init__(self) -> None:
        self.audio_buffer = b''

    def recv_audio(self, frame: av.AudioFrame) -> av.AudioFrame:
        audio = frame.to_ndarray()
        pcm = audio.tobytes()
        self.audio_buffer += pcm
        return frame

def save_audio(audio_bytes, filename):
    with wave.open(filename, 'wb') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)  # 16-bit PCM
        wf.setframerate(48000)
        wf.writeframes(audio_bytes)

# Page 1: Record & Download
if page == "🎙️ Record & Download":
    st.title("🎙️ Record and Download Audio")

    ctx = webrtc_streamer(
        key="record-audio",
        mode="sendonly",
        in_audio=True,
        audio_processor_factory=AudioProcessor,
        client_settings=ClientSettings(
            media_stream_constraints={"audio": True, "video": False},
            rtc_configuration={"iceServers": [{"urls": ["stun:stun.l.google.com:19302"]}]}
        )
    )

    if ctx and ctx.audio_processor:
        if st.button("📥 Save Recording"):
            audio_bytes = ctx.audio_processor.audio_buffer
            if audio_bytes:
                filename = f"recording_{uuid.uuid4().hex}.wav"
                save_audio(audio_bytes, filename)
                with open(filename, "rb") as f:
                    st.download_button("⬇️ Download Recording", f, filename, "audio/wav")
                os.remove(filename)
            else:
                st.warning("No audio captured yet.")

# Page 2: Upload to n8n Webhook
elif page == "🌐 Upload to n8n Webhook":
    st.title("🌐 Upload Audio to n8n Webhook")

    # Sidebar input
    user_name = st.sidebar.text_input("Your Name")
    user_email = st.sidebar.text_input("Your Email")
    webhook_url = st.sidebar.text_input("n8n Webhook URL", value="https://your-n8n-url/webhook/audio")

    ctx = webrtc_streamer(
        key="upload-audio",
        mode="sendonly",
        in_audio=True,
        audio_processor_factory=AudioProcessor,
        client_settings=ClientSettings(
            media_stream_constraints={"audio": True, "video": False},
            rtc_configuration={"iceServers": [{"urls": ["stun:stun.l.google.com:19302"]}]}
        )
    )

    if ctx and ctx.audio_processor:
        if st.button("📤 Upload to n8n"):
            audio_bytes = ctx.audio_processor.audio_buffer
            if audio_bytes and user_name and user_email and webhook_url:
                filename = f"upload_{uuid.uuid4().hex}.wav"
                save_audio(audio_bytes, filename)

                with open(filename, "rb") as f:
                    files = {"file": (filename, f, "audio/wav")}
                    data = {"name": user_name, "email": user_email}
                    try:
                        response = requests.post(webhook_url, files=files, data=data)
                        if response.status_code == 200:
                            st.success("✅ Uploaded successfully!")
                        else:
                            st.error(f"❌ Failed with status code {response.status_code}")
                    except Exception as e:
                        st.error(f"❌ Upload error: {e}")
                os.remove(filename)
            else:
                st.warning("Missing audio or sidebar inputs.")

