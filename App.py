import streamlit as st
from audio_recorder_streamlit import audio_recorder
import requests

st.set_page_config(page_title="🎧 AI Book Buddy Recorder", layout="centered")

st.title("🎙️ Audiobook Recorder – AI Book Buddy")

st.markdown("""
Use this tool to record chapters or segments of your audiobook. Click the microphone below to start and stop recording.
After recording, you can download your file or send it directly to an **n8n webhook** for further automation.
""")

# Sidebar Inputs
st.sidebar.title("📤 Send to n8n Webhook")
webhook_url = st.sidebar.text_input("n8n Webhook URL", placeholder="https://example.com/webhook")
filename = st.sidebar.text_input("Recording Name", value="chapter1_audio")

# Audio Recorder
audio_bytes = audio_recorder(
    text="🎙️ Record Audio",
    recording_color="#e63946",   # red while recording
    neutral_color="#457b9d",     # blue when idle
    icon_name="microphone",
    icon_size="3x",
    pause_threshold=2.0,
    sample_rate=41000
)

# Handle Audio Output
if audio_bytes:
    st.success("✅ Audio recorded successfully!")
    st.audio(audio_bytes, format="audio/wav")

    # Download Button
    st.download_button(
        label="⬇️ Download Audio",
        data=audio_bytes,
        file_name=f"{filename}.wav",
        mime="audio/wav"
    )

    # Send to n8n Button
    if webhook_url and st.sidebar.button("🚀 Send to n8n Webhook"):
        try:
            files = {"file": (f"{filename}.wav", audio_bytes, "audio/wav")}
            data = {"name": filename}
            response = requests.post(webhook_url, files=files, data=data)
            if response.status_code == 200:
                st.sidebar.success("✅ Audio sent to n8n successfully!")
            else:
                st.sidebar.error(f"❌ Failed with status code {response.status_code}")
        except Exception as e:
            st.sidebar.error(f"⚠️ Error sending to webhook: {e}")
