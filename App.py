import streamlit as st
import streamlit_audiorec as sar
import uuid
import os
import requests

st.set_page_config(page_title="Audio Tool", layout="centered")

# Sidebar navigation
page = st.sidebar.radio("Select Page", ["🎙️ Record & Download", "🌐 Upload to n8n Webhook"])

# Page 1: Record and Download
if page == "🎙️ Record & Download":
    st.title("🎙️ Record Your Voice and Download")

    audio_data = sar.audio_recorder()

    if audio_data:
        st.audio(audio_data, format="audio/wav")
        filename = f"recording_{uuid.uuid4().hex}.wav"

        # Save audio locally
        with open(filename, "wb") as f:
            f.write(audio_data)

        # Provide download
        with open(filename, "rb") as f:
            st.download_button(
                label="⬇️ Download Recording",
                data=f,
                file_name="my_recording.wav",
                mime="audio/wav"
            )

        # Clean up
        os.remove(filename)

# Page 2: Upload to n8n Webhook
elif page == "🌐 Upload to n8n Webhook":
    st.title("🌐 Upload Audio to n8n Webhook")

    # Sidebar inputs
    user_name = st.sidebar.text_input("Your Name")
    user_email = st.sidebar.text_input("Your Email")
    webhook_url = st.sidebar.text_input("n8n Webhook URL", value="https://your-n8n-url/webhook/audio")

    audio_data = sar.audio_recorder()

    if audio_data and webhook_url and user_name and user_email:
        st.audio(audio_data, format="audio/wav")
        filename = f"upload_{uuid.uuid4().hex}.wav"

        with open(filename, "wb") as f:
            f.write(audio_data)

        with open(filename, "rb") as audio_file:
            files = {"file": (filename, audio_file, "audio/wav")}
            data = {"name": user_name, "email": user_email}
            try:
                response = requests.post(webhook_url, files=files, data=data)
                if response.status_code == 200:
                    st.success("✅ Uploaded successfully to n8n webhook!")
                else:
                    st.error(f"❌ Upload failed. Status code: {response.status_code}")
            except Exception as e:
                st.error(f"❌ Error uploading: {e}")

        os.remove(filename)
    else:
        st.info("Record audio and fill out all fields in the sidebar.")
