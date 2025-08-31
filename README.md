# Spot-to-Tube Migrator

A simple, locally-hosted web application to migrate your music playlists from Spotify to YouTube Music.

<!-- Add a screenshot of the app in action here -->
 

## Features

-   **Simple Web UI:** An easy-to-use interface that runs right in your browser.
-   **Local & Secure:** Your credentials are never sent to a third-party server. Everything runs on your own machine.
-   **Selective Migration:** Choose exactly which playlists you want to transfer.
-   **Real-time Progress:** See a detailed log of the migration process as it happens.
-   **Final Summary:** Get a clear report of which songs were successfully migrated and which couldn't be found.

## Prerequisites

-   Python 3.7+
-   A web browser (like Chrome, Firefox, etc.)
-   A Spotify account and a YouTube Music (Google) account.

## Setup Instructions

### 1. Get the Code

Clone this repository to your local machine:
```bash
git clone https://github.com/sevencooper/spot-to-tube-migrator.git
cd spot-to-tube-migrator
```

### 2. Set up a Python Virtual Environment

Using a virtual environment is highly recommended to keep dependencies isolated.

```bash
# For macOS/Linux
python3 -m venv venv
source venv/bin/activate

# For Windows
python -m venv venv
.\venv\Scripts\activate
```

### 3. Install Dependencies

Install the required Python libraries from the `requirements.txt` file:
```bash
pip install -r requirements.txt
```

### 4. Configure Spotify API Credentials

You need to register an application with Spotify to get API keys.

1.  Go to the [Spotify Developer Dashboard](https://developer.spotify.com/dashboard/applications) and log in.
2.  Click **"Create an App"**.
3.  Give your app a name (e.g., "My Playlist Migrator") and a description.
4.  Once created, you will see your **Client ID**. Click **"Show client secret"** to see your **Client Secret**.
5.  Now, click **"Edit Settings"**.
6.  In the **Redirect URIs** field, add this exact URL: `http://127.0.0.1:5000/callback`
7.  Click **"Add"** and then **"Save"** at the bottom.

### 5. Create the Environment File

1.  In the project folder, make a copy of `.env.example` and rename it to `.env`.
2.  Open the `.env` file and fill in your Spotify credentials from the previous step.
3.  The `FLASK_SECRET_KEY` can be any long, random string you make up.

    ```ini
    # Example .env file
    FLASK_SECRET_KEY='a_very_long_and_random_string_for_security_123'
    SPOTIPY_CLIENT_ID='YOUR_SPOTIFY_CLIENT_ID_HERE'
    SPOTIPY_CLIENT_SECRET='YOUR_SPOTIFY_CLIENT_SECRET_HERE'
    SPOTIPY_REDIRECT_URI='http://127.0.0.1:5000/callback'
    ```
**Security Note:** The `.gitignore` file is configured to **never** upload your `.env` file to GitHub. Keep your secrets safe!

## How to Run the Application

1.  Make sure your virtual environment is activated.
2.  Run the Flask application from your terminal:
    ```bash
    python app.py
    ```
3.  Open your web browser and navigate to: **http://127.0.0.1:5000**

## How to Use the App

1.  **Connect to Spotify:** Click the "Login with Spotify" button and authorize the application when prompted by Spotify.
2.  **Select Playlists:** Once connected, your Spotify playlists will appear. Use the checkboxes to select the ones you want to migrate.
3.  **Connect to YouTube Music:**
    *   This app uses the `ytmusicapi` library, which requires authentication headers from your browser.
    *   Follow the **[official instructions here](https://ytmusicapi.readthedocs.io/en/latest/setup.html#copy-authentication-headers)** to learn how to copy these headers from your browser's developer tools.
    *   Paste the *entire block of text* into the text area in the app.
    *   Click "Verify & Connect". You should see a success message.
4.  **Start Migration:** The "Start Migration" button will become active. Click it to begin the transfer process.
5.  **View Results:** The progress log will update in real-time. Once finished, a final summary will be displayed at the top of the results section.

## License

This project is open-source and available under the [MIT License](LICENSE).