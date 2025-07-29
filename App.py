import streamlit as st
from audio_recorder_streamlit import audio_recorder

st.set_page_config(page_title="AudioBook Recorder", layout="centered")

st.title("🎙️ Audiobook Recorder")

st.markdown("""
Use this tool to record your audiobook. Click the microphone to start and stop recording.
""")

# Customize the recorder
audio_bytes = audio_recorder(
    text="Record",
    recording_color="#e63946",   # red while recording
    neutral_color="#457b9d",     # blue when idle
    icon_name="microphone",
    icon_size="3x",
    pause_threshold=2.0,
    sample_rate=41000
)

# Playback and download if audio exists
if audio_bytes:
    st.success("✅ Audio recorded successfully!")
    st.audio(audio_bytes, format="audio/wav")

    # Download button
    st.download_button(
        label="⬇️ Download Audio",
        data=audio_bytes,
        file_name="audiobook_recording.wav",
        mime="audio/wav"
    )
