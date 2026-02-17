import streamlit as st
import datetime
import os
from dotenv import load_dotenv

load_dotenv()

from utils.logger import UILogger, LogLevel
from utils.channel_monitor import check_for_new_videos
from utils.downloader import download_audio
from utils.transcriber import transcribe_audio
from utils.summarizer import summarize_transcript

# Initialize Logger
if "logger" not in st.session_state:
    st.session_state.logger = UILogger()

logger = st.session_state.logger

st.set_page_config(page_title="YouTube Video Analysis", layout="wide")

st.title("YouTube Video Analysis App")

import json

CONFIG_FILE = "config.json"

def load_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r") as f:
                return json.load(f)
        except:
            pass
    return {}

def save_config(config):
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f)

config = load_config()

# Layout: Inputs
col1, col2 = st.columns(2)

with col1:
    st.subheader("Configuration")
    
    # 1. YouTube Channels
    default_channels = config.get("channels", "https://www.youtube.com/@ExampleChannel")
    channels_input = st.text_area("YouTube Channel URLs (one per line)", value=default_channels, height=150)
    
    # 2. Time Period
    st.markdown("### Time Period")
    t1, t2 = st.columns(2)
    with t1:
        start_date = st.date_input("Start Date", datetime.date.today())
        start_time = st.time_input("Start Time", datetime.time(6, 0))
    with t2:
        end_date = st.date_input("End Date", datetime.date.today())
        end_time = st.time_input("End Time", datetime.time(8, 0))
    
    start_datetime = datetime.datetime.combine(start_date, start_time)
    end_datetime = datetime.datetime.combine(end_date, end_time)

    # 3. Output Directory
    default_out_dir = config.get("output_dir", os.path.join(os.getcwd(), "output"))
    output_dir = st.text_input("Output Directory", value=default_out_dir)

    # 4. Whisper Model
    model_options = ["mlx-community/whisper-large-v3-mlp", "mlx-community/whisper-turbo-mlp", "mlx-community/whisper-tiny-mlp"]
    default_model_index = 1 # Default to turbo
    saved_model = config.get("model_name", "mlx-community/whisper-turbo-mlp")
    
    if saved_model in model_options:
        default_model_index = model_options.index(saved_model)
            
    model_name = st.selectbox("Whisper Model", model_options, index=default_model_index)

with col2:
    st.subheader("Console Log")
    
    # Log Container
    log_container = st.empty()
    
    # Function to render logs
    def render_logs():
        logs = logger.get_logs()
        log_container.code(logs, language="text")

    render_logs()
    
    if st.button("Clear Logs"):
        logger.clear()
        st.rerun()

# Processing Logic
with st.sidebar:
    api_key = st.text_input("Gemini API Key", type="password", value=os.getenv("GEMINI_API_KEY", ""))

if st.button("Start Processing", type="primary"):
    # Save Config
    new_config = {
        "channels": channels_input,
        "output_dir": output_dir,
        "model_name": model_name
    }
    save_config(new_config)
    
    if not api_key:
        logger.critical("Please provide a Gemini API Key.")
        render_logs()
        st.stop()
        
    logger.info("Starting processing...")
    logger.info(f"Time Period: {start_datetime} - {end_datetime}")
    logger.info(f"Model: {model_name}")
    
    # Create Trigger Time Folder
    trigger_time_str = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    current_output_dir = os.path.join(output_dir, trigger_time_str)
    if not os.path.exists(current_output_dir):
        os.makedirs(current_output_dir)
        
    logger.info(f"Output Directory: {current_output_dir}")
    
    if not channels_input.strip():
        logger.warning("No channels provided.")
    else:
        channel_list = [url.strip() for url in channels_input.split('\n') if url.strip()]
        logger.info(f"Processing {len(channel_list)} channels.")
        
        # 1. Check for videos
        videos = check_for_new_videos(channel_list, start_datetime, end_datetime, logger)
        
        if not videos:
            logger.info("No videos found in the specified time period.")
        else:
            for video in videos:
                video_title = video.get('title', 'Unknown_Title')
                channel_name = video.get('channel_name', 'Unknown_Channel')
                upload_time = video.get('published') # datetime object
                
                # Format for filename: <upload_time>_<YouTube_Channel_Name>_<Video_Title>
                # Sanitize filename
                def sanitize(name):
                    return "".join([c for c in name if c.isalpha() or c.isdigit() or c in (' ', '-', '_')]).rstrip()
                
                upload_time_str = upload_time.strftime("%Y-%m-%d_%H-%M-%S") if upload_time else "UnknownTime"
                safe_title = sanitize(video_title)
                safe_channel = sanitize(channel_name)
                
                # Truncate if too long to avoid FS errors
                filename_base = f"{upload_time_str}_{safe_channel}_{safe_title}"[:200]
                
                logger.info(f"Processing video: {video_title}")
                
                # 2. Download
                audio_path = download_audio(video.get('link'), current_output_dir, logger)
                
                if audio_path:
                    # 3. Transcribe
                    transcript = transcribe_audio(audio_path, model_name, logger)
                    
                    if transcript:
                        # 4. Summarize
                        summary_data = summarize_transcript(transcript, logger, api_key=api_key)
                        
                        if summary_data:
                            # 5. Save Report
                            report_filename = f"{filename_base}.md"
                            report_path = os.path.join(current_output_dir, report_filename)
                            
                            with open(report_path, "w", encoding="utf-8") as f:
                                f.write(f"# {video_title}\n\n")
                                f.write(f"**Channel:** {channel_name}\n")
                                f.write(f"**Upload Time:** {upload_time}\n")
                                f.write(f"**Link:** {video.get('link')}\n\n")
                                f.write("## Summary & Outline\n\n")
                                f.write(summary_data['summary_content'])
                                f.write("\n\n## Detailed Transcript\n\n")
                                f.write(summary_data['detailed_transcript'])
                                
                            logger.info(f"Report saved to: {report_path}")
                            
                    # Optional: Cleanup audio file
                    try:
                        os.remove(audio_path)
                        logger.info(f"Removed temp audio: {audio_path}")
                    except:
                        pass
                
                logger.info(f"Finished processing {video_title}")

    render_logs()
