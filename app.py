import streamlit as st
import datetime
import os
from dotenv import load_dotenv

load_dotenv()

from utils.logger import UILogger, LogLevel, CriticalError
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
        start_time = st.time_input("Start Time", datetime.time(0, 0))
    with t2:
        end_date = st.date_input("End Date", datetime.date.today())
        end_time = st.time_input("End Time", datetime.time(23, 59))
    
    start_datetime = datetime.datetime.combine(start_date, start_time)
    end_datetime = datetime.datetime.combine(end_date, end_time)

    # 3. Output Directory
    st.markdown("### Output")
    default_out_dir = config.get("output_dir", os.path.join(os.getcwd(), "output"))
    output_dir = st.text_input("Output Directory", value=default_out_dir)

    # 4. Model Selection
    st.markdown("### Model Selection")
    model_options = ["mlx-community/whisper-large-v3-mlp", "mlx-community/whisper-large-v3-turbo", "mlx-community/whisper-tiny-mlp"]
    default_model_index = 1 # Default to turbo
    saved_model = config.get("model_name", "mlx-community/whisper-large-v3-turbo")
    
    if saved_model in model_options:
        default_model_index = model_options.index(saved_model)
            
    model_name = st.selectbox("Whisper Model", model_options, index=default_model_index)

    # Gemini Model
    gemini_models = [
        "models/gemini-2.5-flash-lite", 
        "models/gemini-2.5-flash", 
        "models/gemini-3-flash-preview", 
        "models/deep-research-pro-preview-12-2025", 
        "models/gemini-2.5-pro", 
        "models/gemini-3-pro-preview"
    ]
    
    # Defaults
    default_abstract_model = "models/gemini-2.5-flash-lite"
    default_summary_model = "models/gemini-2.5-pro"
    
    # Load from config or use default
    saved_abstract_model = config.get("gemini_abstract_model", default_abstract_model)
    saved_summary_model = config.get("gemini_summary_model", default_summary_model)
    
    # Ensure saved model is in list (fallback if removed/renamed)
    idx_abstract = gemini_models.index(saved_abstract_model) if saved_abstract_model in gemini_models else gemini_models.index(default_abstract_model)
    idx_summary = gemini_models.index(saved_summary_model) if saved_summary_model in gemini_models else gemini_models.index(default_summary_model)

    # st.markdown("#### Gemini Models")
    gemini_abstract_model = st.selectbox("Abstract Generation Model", gemini_models, index=idx_abstract)
    gemini_summary_model = st.selectbox("Summary Generation Model", gemini_models, index=idx_summary)

# ... (previous code)

with col2:
    st.subheader("Console Log")
    
    # Log Container with Fixed Height for Stability
    console_container = st.container(height=400)
    
    # Place log output inside the fixed container
    log_output = console_container.empty()
    
    # Always set the logger container so updates work on every rerun
    # We need a wrapper to ensure .code() is called on the empty placeholder within the container
    class ContainerWrapper:
        def __init__(self, placeholder):
            self.placeholder = placeholder
        def code(self, text, language="text"):
            self.placeholder.code(text, language=language)
        def empty(self):
            self.placeholder.empty()

    logger.set_container(ContainerWrapper(log_output))
    
    # Render logs on load/rerun
    log_output.code(logger.get_logs(), language="text")
    
    if st.button("Clear Logs", disabled=st.session_state.get("is_processing", False)):
        logger.clear()
        st.rerun()

# Processing Logic
with st.sidebar:
    # API Key Input
    # Support multiple keys: multiline or comma separated
    default_api_keys = os.getenv("GEMINI_API_KEY", "")
    api_key_input = st.text_input("Gemini API Keys (one per line or comma-separated)", value=default_api_keys, type="password")
    
    # Parse keys
    api_keys = []
    if api_key_input:
        # Split by newline or comma
        raw_keys = api_key_input.replace(",", "\n").split("\n")
        api_keys = [k.strip() for k in raw_keys if k.strip()]
    
    if api_keys:
        st.caption(f"Loaded {len(api_keys)} API Key(s)")
        # Show masked keys for verification
        # for k in api_keys:
        #     masked = f"{k[:4]}...{k[-4:]}" if len(k) > 8 else "****"
        #     st.caption(f"- {masked}")
    else:
        st.warning("No API Keys provided.")

# Initialize processing state
if "is_processing" not in st.session_state:
    st.session_state.is_processing = False

# Start Button with State Management
# Note: Streamlit buttons return True *only* on the click event.
# To disable it *while* the logic runs within that same click event, we rely on the fact that
# the UI won't update *until* the script finishes anyway, effectively blocking interaction.
# However, to explicitly show a "Disabled" state, we need to rerun.
# Since we can't rerun *inside* the button processing without interrupting it, we use a flag.

start_button = st.button("Start Processing", type="primary", disabled=st.session_state.is_processing)

if start_button:
    st.session_state.is_processing = True
    # We force a rerun to update the UI state (disable button) immediately? 
    # No, that would reset the button click. 
    # Streamlit executes the block below. The UI is locked (running) for the user anyway.
    # The 'disabled' prop above is useful if we trigger processing via another thread or async, 
    # but here it's synchronous. The main benefit is preventing double-clicks if we yielded.
    # For now, relying on 'running' state is standard for sync scripts. 
    # But user asked for GRAY button.
    # To truly gray it out, we'd need to set state -> rerun -> run logic -> set state -> rerun.
    # Standard pattern:
    
    # 1. Set processing flag
    # 2. Rerun
    # 3. On next run, if flag is true -> disable button & run logic -> set flag false -> rerun
    
    # Let's try the direct execution first, usually sufficient. 
    # Use st.spinner for visual feedback.
    
    # Save Config
    new_config = {
        "channels": channels_input,
        "output_dir": output_dir,
        "model_name": model_name,
        "gemini_abstract_model": gemini_abstract_model,
        "gemini_summary_model": gemini_summary_model
    }
    save_config(new_config)
    
    if not api_keys:
        logger.critical("Please provide at least one Gemini API Key.")
        # No need to stop() here as critical will raise exception now
        
    try:
        with st.spinner('Processing...'):
            logger.info("Starting processing...")
            logger.info(f"Time Period: {start_datetime} - {end_datetime}")
            logger.info(f"Model: {model_name}")
            
            # Create Trigger Time Folder
            trigger_time_str = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            start_str = start_datetime.strftime("%Y-%m-%d_%H-%M-%S")
            end_str = end_datetime.strftime("%Y-%m-%d_%H-%M-%S")
            
            folder_name = f"Trigger_{trigger_time_str}_From_{start_str}_{end_str}"
            current_output_dir = os.path.join(output_dir, folder_name)
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
                    failed_live_videos = []
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
                        
                        if audio_path == "LIVE_EVENT_UPCOMING":
                            logger.info(f"The audio {video.get('link')} cannot be downloaded in the moment, skip to the next audio")
                            failed_live_videos.append(video.get('link'))
                            continue

                        if audio_path:
                            # 3. Transcribe
                            transcript = transcribe_audio(audio_path, model_name, logger)
                            
                            if transcript:
                                # 4. Summarize
                                summary_data = summarize_transcript(
                                    transcript, 
                                    video.get('link'), 
                                    logger, 
                                    api_keys=api_keys, 
                                    abstract_model=gemini_abstract_model,
                                    summary_model=gemini_summary_model
                                )
                                
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

                    if failed_live_videos:
                        urls_str = "\n\t".join(failed_live_videos)
                        logger.info(f"Here is the video cannot process at the moment, please retry later: \n\t{urls_str}")

            logger.info("All processing complete.")
            
    except CriticalError as e:
        st.error(f"Processing stopped due to critical error: {e}")
    except Exception as e:
        logger.critical(f"An unexpected error occurred: {e}")
        st.error(f"An unexpected error occurred: {e}")
    finally:
        st.session_state.is_processing = False
        # Optional: st.rerun() if we were doing the async state pattern
