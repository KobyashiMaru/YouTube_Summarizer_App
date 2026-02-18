# YouTube Summarizer App (Apple Silicon Optimized)

## What does this repo do?
This is a local, high-performance tool designed for macOS (Apple Silicon) to automate the analysis of YouTube videos. It monitors specific YouTube channels for new uploads within a given timeframe, downloads the audio, transcribes it locally using optimized MLX Whisper models, and generates concise summaries and outlines using Google's Gemini models.

## How does this app work?
1.  **Monitor**: It checks the RSS feeds of the provided YouTube channel URLs to find videos published between your specified start and end times.
2.  **Download**: It uses `yt-dlp` to download the audio track (m4a) from the identified videos.
3.  **Transcribe**: It uses `mlx-whisper` (optimized for Apple Silicon) to transcribe the audio locally. This is faster and more efficient on M-series Macs than standard Whisper.
4.  **Summarize**: The transcript is sent to Google's Gemini Flash models (1.5, 2.0, or 3.0) to generate a summary, outline, and key takeaways.
5.  **Report**: The final output is saved as a Markdown file containing video metadata, the summary, and the full transcript.

## File Structure
*   **`app.py`**: The main Streamlit application. Handles the UI, user inputs, and orchestrates the entire workflow.
*   **`requirements.txt`**: List of Python dependencies.
*   **`config.json`**: Automatically created to persist your last-used settings (channels, models, output directory).
*   **`.env`**: (Optional) Stores your API keys securely.
*   **`utils/`**:
    *   **`channel_monitor.py`**: Parses YouTube RSS feeds to filter videos by date.
    *   **`downloader.py`**: Handles audio downloading with `yt-dlp` and real-time progress logging.
    *   **`transcriber.py`**: Manages audio transcription using `mlx-whisper` with chunking and progress updates.
    *   **`summarizer.py`**: Interfaces with Google Gemini API to generate summaries.
    *   **`logger.py`**: Custom logging utility that updates the Streamlit console in real-time.

## Installation Guide

### Prerequisites
*   **macOS with Apple Silicon** (M1/M2/M3/M4) is highly recommended for `mlx-whisper`.
*   **Python 3.10+** (Recommended to use Conda).
*   **FFmpeg**: Required for audio processing.

### Steps

1.  **Clone the repository**:
    ```bash
    git clone <repo-url>
    cd YouTube_Summarizer_App
    ```

2.  **Install FFmpeg** (if not installed):
    ```bash
    brew install ffmpeg
    ```

3.  **Create and Activate Environment** (Recommended):
    ```bash
    conda create -n yt-analysis python=3.10
    conda activate yt-analysis
    ```

4.  **Install Dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

5.  **Set up Gemini API Key**:
    You need a Google Gemini API key to use the summarization feature. Get one [here](https://aistudio.google.com/app/apikey).

    **Option A: Using `.env` (Recommended)**
    1.  Create a file named `.env` in the root directory.
    2.  Add your key:
        ```env
        GEMINI_API_KEY=your_actual_api_key_here
        ```
    
    **Option B: UI Input**
    *   You can also enter your API key directly in the sidebar of the app every time you run it.

## How to Use the App

1.  **Run the App**:
    ```bash
    streamlit run app.py
    ```

2.  **Configure**:
    *   **Channels**: Paste YouTube channel URLs (one per line) in the sidebar.
    *   **Date Range**: Select the start and end date/time to filter videos.
    *   **Output Directory**: Choose where to save the markdown reports.
    *   **Models**: Select the Whisper model (transcription) and Gemini model (summary).

3.  **Start**:
    *   Click **Start Processing**.
    *   Monitor the real-time logs in the console.
    *   The "Start Processing" button will be disabled while running.

4.  **View Results**:
    *   Check the `output/` directory (or your custom path) for folders named by timestamp.
    *   Inside, you will find `.md` files for each processed video.



## Todo List
- [ ] Work on the prompt for the summarizer to make it more concise and informative.
- [x] Use transcript and gemini-generated summary to generate a more detailed summary.
- [ ] Consider the algorithm of the transcribe process, maybe we should get rid of the chunking process method, but remain the user experience of the progress bar.




