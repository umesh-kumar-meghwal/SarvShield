# 🛡️ SarvShield

### AI-Assisted Digital Scam Detection & Safety Guidance Platform

SarvShield is a digital safety platform designed to help users identify suspicious messages, phone numbers, links, and screenshots.

It analyzes multiple risk signals and provides a risk score, threat classification, scam fingerprint, attack-chain insights, and safety recommendations.

---

## 🚀 Live Project

🔗 **GitHub Repository:**  
https://github.com/umesh-kumar-meghwal/SarvShield

---

## 🎯 Project Objective

Online scams are increasing rapidly through:

- Fraudulent messages
- Fake phone calls
- Phishing links
- Fake websites
- Fake payment requests
- Fraudulent screenshots
- Urgent financial requests

SarvShield aims to provide users with a centralized platform where they can analyze suspicious digital content and understand the possible risks.

---

## ✨ Key Features

### 🔍 1. Message Detection

Analyzes text messages and identifies suspicious patterns such as:

- Urgency and pressure
- Fake rewards and offers
- OTP requests
- Banking fraud
- Payment requests
- Account suspension threats

---

### 📞 2. Phone Number Detection

Provides phone number risk analysis using:

- Database lookup
- Spam number records
- External phone intelligence APIs
- Risk scoring
- Detection source information

---

### 🔗 3. Link Detection

Analyzes URLs and checks for potentially suspicious indicators, including:

- Suspicious domains
- Phishing patterns
- Fake websites
- Untrusted links
- Domain-related risk signals

---

### 🖼️ 4. Screenshot Detection

Allows users to upload screenshots for analysis.

The screenshot detection system can analyze:

- Suspicious text
- Fraudulent offers
- Fake payment requests
- Phishing content
- Scam-related visual information

---

### 📊 5. Risk Score Engine

SarvShield combines different detection signals to generate an overall risk score.

The system considers:

- Message risk score
- Phone number risk score
- Link risk score
- Screenshot risk score
- Cross-signal relationships
- Additional risk indicators

The final score is normalized between **0 and 100**.

---

### 🧠 6. What-If Risk Analysis

The What-If Analysis feature explains how the risk score may change if a particular signal is removed.

For example:

- Risk score with the link
- Risk score without the link
- Risk score with the message
- Risk score without the message

This helps users understand which input contributes most to the overall risk.

---

### 🧬 7. Scam Fingerprint

SarvShield attempts to identify the possible scam pattern or fingerprint.

Examples include:

- Phishing
- Financial fraud
- Fake reward scam
- Account verification scam
- Suspicious payment request

---

### ⛓️ 8. Attack Chain Analysis

The platform can explain how a suspicious interaction may progress, such as:

1. User receives a suspicious message
2. Attacker creates urgency
3. User is redirected to a link
4. Personal information or payment is requested
5. User may face financial or privacy risks

---

### 🛡️ 9. SafeNext Coach

SarvShield provides safety guidance after analysis.

Recommendations may include:

- Do not share OTPs
- Avoid suspicious links
- Do not transfer money
- Block suspicious contacts
- Report fraudulent content
- Verify information through official sources

---

### 🌐 10. Multilingual Output

The platform supports output in the selected language where configured.

Users can select their preferred language for explanations and safety recommendations.

---

### 👤 11. User Account Features

- User registration
- Login and logout
- OTP-based verification
- User profile
- Profile picture support
- ScamCheck history
- Report scam
- Feedback system

---

## 🏗️ System Architecture

```text
                  ┌─────────────────────┐
                  │       User          │
                  └──────────┬──────────┘
                             │
                             ▼
                  ┌─────────────────────┐
                  │   Flask Web App     │
                  └──────────┬──────────┘
                             │
          ┌──────────────────┼──────────────────┐
          │                  │                  │
          ▼                  ▼                  ▼
   Message Detector   Phone Detector     Link Detector
          │                  │                  │
          └──────────────────┼──────────────────┘
                             │
                             ▼
                  ┌─────────────────────┐
                  │ Screenshot Detector │
                  └──────────┬──────────┘
                             │
                             ▼
                  ┌─────────────────────┐
                  │   Risk Engine       │
                  └──────────┬──────────┘
                             │
          ┌──────────────────┼──────────────────┐
          │                  │                  │
          ▼                  ▼                  ▼
   Scam Fingerprint   Attack Chain      SafeNext Coach
                             │
                             ▼
                  ┌─────────────────────┐
                  │  Final Result       │
                  │ Score + Explanation │
                  └─────────────────────┘
```

---

## 🧰 Technology Stack

### Backend

- Python
- Flask
- Flask-CORS
- Gunicorn

### Database and Storage

- Supabase
- PostgreSQL
- Supabase Storage

### Detection and Analysis

- Python-based detection modules
- Google GenAI integration
- Requests
- BeautifulSoup
- Pillow
- OpenCV
- NumPy

### Frontend

- HTML
- CSS
- JavaScript
- Bootstrap/Tailwind where configured

---

## 📁 Project Structure

```text
SarvShield/
│
├── app.py
├── ai_helper.py
├── db.py
│
├── message_detect.py
├── phone.py
├── phone_detect.py
├── link_detect.py
├── screenshot_detect.py
│
├── risk_engine.py
├── scam_fingerprint.py
├── safe_next.py
│
├── requirements.txt
├── .env
├── .gitignore
│
├── templates/
│   ├── login.html
│   ├── register.html
│   ├── user-dashboard.html
│   ├── scamcheck.html
│   └── ...
│
└── static/
    ├── css/
    ├── js/
    └── images/
```

---

## ⚙️ Installation and Setup

### 1. Clone the Repository

```bash
git clone https://github.com/umesh-kumar-meghwal/SarvShield.git
```

Move into the project directory:

```bash
cd SarvShield
```

---

### 2. Create a Virtual Environment

#### Windows

```bash
python -m venv venv
venv\Scripts\activate
```

#### Linux/macOS

```bash
python3 -m venv venv
source venv/bin/activate
```

---

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

---

### 4. Configure Environment Variables

Create a `.env` file in the project root directory.

Example:

```env
SUPABASE_URL=your_supabase_project_url
SUPABASE_KEY=your_supabase_key

FLASK_SECRET_KEY=your_secret_key

GOOGLE_API_KEY=your_google_api_key

SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_EMAIL=your_email
SMTP_PASSWORD=your_app_password
```

> Never upload your `.env` file or private API keys to GitHub.

---

### 5. Run the Application

```bash
python app.py
```

Open the application in your browser:

```text
http://127.0.0.1:5000
```

---

## 📦 Requirements

The project uses the following major dependencies:

```text
Flask
Flask-CORS
supabase
python-dotenv
requests
gunicorn
google-genai
Pillow
beautifulsoup4
opencv-python-headless
numpy
```

Install all dependencies using:

```bash
pip install -r requirements.txt
```

---

## 🔄 ScamCheck Processing Flow

```text
User Input
    │
    ▼
Message / Phone / Link / Screenshot
    │
    ▼
Individual Detection Modules
    │
    ▼
Risk Score Calculation
    │
    ▼
Cross-Signal Analysis
    │
    ▼
Scam Fingerprint Generation
    │
    ▼
Attack Chain Analysis
    │
    ▼
SafeNext Safety Recommendation
    │
    ▼
Final Result
```

---

## 📈 Risk Classification

SarvShield uses risk-score thresholds to classify results.

| Risk Score | Classification |
|------------|----------------|
| 0–29       | LOW RISK       |
| 30–59      | SUSPICIOUS     |
| 60–79      | HIGH RISK      |
| 80–100     | VERY HIGH RISK |

> Risk scores are indicators generated by the detection system. Users should verify important information through trusted official sources.

---

## 🔐 Security Considerations

- Never expose API keys publicly.
- Store secrets inside environment variables.
- Use secure password handling.
- Validate uploaded files.
- Restrict file upload size and type.
- Do not trust user-provided URLs.
- Use HTTPS in production.
- Avoid storing unnecessary personal information.
- Protect authentication and session data.

---

## 🚀 Deployment

The application can be deployed using a compatible Python hosting platform.

For production deployment with Gunicorn:

```bash
gunicorn app:app
```

Make sure that:

- All environment variables are configured.
- Supabase credentials are valid.
- Required dependencies are installed.
- Production secrets are not committed to GitHub.
- Uploaded files are securely handled.

---

## 🔮 Future Improvements

Planned improvements may include:

- Real-time threat intelligence
- More advanced AI-based screenshot analysis
- Improved phishing URL detection
- Browser extension
- Mobile application
- Automated scam reporting
- Community-based threat database
- Better multilingual support
- Real-time alerts
- Advanced admin analytics
- Explainable AI reports
- More external intelligence sources

---

## ⚠️ Disclaimer

SarvShield is designed as a digital safety assistance and awareness platform.

Detection results may not always be accurate. A result marked as safe does not guarantee that content is completely safe.

Always verify suspicious messages, websites, phone numbers, and payment requests through official sources.

SarvShield does not replace official cybersecurity authorities or professional investigation.

---

## 👨‍💻 Team

### Founder

**Umesh Kumar Meghwal**

- GitHub: https://github.com/umesh-kumar-meghwal

### Project

**SarvShield – Digital Safety and Scam Detection Platform**

---

## 🤝 Contributing

Contributions, suggestions, and improvements are welcome.

To contribute:

1. Fork the repository.
2. Create a new branch.
3. Make your changes.
4. Test the application.
5. Create a pull request.

---

## 📄 License

License information can be added according to the project's distribution requirements.

---

## ⭐ Support

If you find this project useful, consider giving the repository a ⭐ on GitHub.

### Stay Alert. Stay Safe. Stay Protected with SarvShield. 🛡️
