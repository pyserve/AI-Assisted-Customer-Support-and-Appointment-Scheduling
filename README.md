# AI-Assisted Customer Support and Appointment Scheduling (ACAS)

_The AI-Assisted Customer Support and Appointment Scheduling (ACAS) system leverages AI-driven technology to enhance customer interactions and streamline appointment scheduling. By integrating advanced natural language processing with telephony services, ACAS offers a scalable and efficient solution for real-time, interactive customer support._

## Requirements

1. **Django/Python Web Server**: `pip install django`
2. **Twilio Account**: Set up a Twilio account (Free Tier available).
3. **Hugging Face**: Obtain an Access Token from Hugging Face.
4. **Ngrok Server**: `pip install pyngrok` or download and install the Ngrok executable.
5. **Pip Install Requirements**:
   - `pip install -r requirements.txt`

## Configuration

**Step 1: Setup Django Project**

- Install Django: `pip install django`

**Step 2: Install Ngrok**

- Install Ngrok: `pip install pyngrok` or download and install the Ngrok executable.

**Step 3: Create a Twilio Account and Set Up a TwiML App**

1. Create a Twilio account and set up a TwiML app.
2. Add the numbers you want to call into the list of verified caller ids.
3. Set the request URL inside the TwiML app to the Ngrok server URL after running it: `python ngrok.py`.
4. In the Twilio Account, go to your active number, and within the configure tab, set up "Configure with" as "TwiML App" and select your newly created app as "TwiML App".

**Step 4: Create a Hugging Face Account and Generate an Access Token**

- Create a Hugging Face account and generate an access token for API access.

## Running the System

1. Download and unzip the code folder.
2. Open a command terminal inside the directory.
3. Run: `pip install -r requirements.txt`
4. Start the Ngrok server: `python ngrok.py` (make sure it points to the same address or port used by the web server).
5. Copy the Ngrok domain URL (e.g., `xxxxxxx-xxx-x.ngrok-free.app`) into the `settings.py` file in the project folder.
6. Copy the full Ngrok URL (e.g., `https://xxxxxxx-xxx-x.ngrok-free.app/inbounds/`) into the voice configuration > Request URL inside the TwiML App.
7. Run the project's web server: `python manage.py runserver`.
8. **Change the following tokens to your own values in settings.py:**

   ```
   SECRET_KEY = "YOUR_DJANGO_SECRET_KEY"
   DEBUG = True

   HUGGINGFACE_TOKEN = "YOUR_HUGGINGFACE_TOKEN"
   TWILIO_ACCOUNT_SID = "YOUR_TWILIO_ACCOUNT_SID"
   TWILIO_AUTH_TOKEN = "YOUR_TWILIO_AUTH_TOKEN"
   TWILIO_PHONE_NUMBER = "YOUR_TWILIO_PHONE_NUMBER"
   ```

9. Call your Twilio number from a registered number (must be listed in the verified caller list in Twilio).

## Key Features

- **Natural Language Processing**: AI-driven interactions tailored to customer needs.
- **Appointment Scheduling**: Automated scheduling based on availability.
