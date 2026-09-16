# 🛡️ SarvShield

### AI-Assisted Digital Scam Detection & Safety Guidance Platform

SarvShield is a digital safety platform developed for a college internal hackathon. It helps users analyze suspicious messages, phone numbers, links, and screenshots by combining detection modules, risk analysis, AI-assisted insights, and safety recommendations.

The goal of SarvShield is to increase digital awareness and help users make safer decisions when they encounter potentially fraudulent content.

---

## 🌐 Live Demo

🚀 **Try SarvShield Online:**  
https://sarvshield.vercel.app/

📂 **GitHub Repository:**  
https://github.com/umesh-kumar-meghwal/SarvShield

---

## 🎯 Problem Statement

Digital scams are commonly distributed through:

- Fraudulent messages
- Suspicious phone calls
- Phishing links
- Fake websites
- Fake payment requests
- Fake rewards and offers
- Fraudulent screenshots
- OTP and account-verification requests

Many users cannot easily identify these threats. SarvShield provides a single platform for analyzing suspicious digital content and understanding the possible risk.

---

## 💡 Our Solution

SarvShield analyzes different types of user inputs and generates a structured result containing:

- Individual detection scores
- Overall risk score
- Risk classification
- Supporting evidence
- Scam fingerprint
- Possible attack chain
- What-If risk analysis
- SafeNext safety recommendations

The platform is designed to make technical security information easier to understand for normal users.

---

## ✨ Key Features

### 🔍 Message Detection

Analyzes message content for suspicious patterns such as:

- Urgency and pressure
- Fake rewards and offers
- OTP requests
- Banking-related fraud
- Payment requests
- Account suspension threats
- Personal information requests

### 📞 Phone Number Detection

Analyzes phone numbers through:

- Database lookup
- Spam number records
- External phone intelligence APIs where configured
- Risk scoring
- Detection source information

### 🔗 Link Detection

Analyzes submitted URLs for possible risk indicators, including:

- Suspicious domains
- Phishing patterns
- Untrusted websites
- Fraud-related keywords
- URL-based risk signals

### 🖼️ Screenshot Detection

Allows users to submit screenshots for analysis.

The system can identify possible scam indicators such as:

- Suspicious text
- Fake payment requests
- Fraudulent offers
- Phishing content
- Suspicious instructions
- Scam-related visual information

### 📊 Risk Score Engine

SarvShield combines multiple signals:

- Message score
- Phone score
- Link score
- Screenshot score
- Cross-signal relationships
- Additional risk indicators

The final risk score is normalized between **0 and 100**.

### 🧠 What-If Risk Analysis

What-If Analysis explains how the risk score may change when one input signal is removed.

For example:

- Current risk score
- Risk score without the link
- Risk score without the message
- Risk score without the phone number
- Risk score without the screenshot

This helps users understand which input contributes to the detected risk.

### 🧬 Scam Fingerprint

The platform attempts to identify the possible type or pattern of a scam, such as:

- Phishing
- Financial fraud
- Fake reward scam
- Account verification scam
- Suspicious payment request

### ⛓️ Attack Chain Analysis

SarvShield can explain a possible scam progression:

1. A user receives a suspicious message.
2. The attacker creates urgency or fear.
3. The user is redirected to a link or contact number.
4. Personal information, OTP, or payment is requested.
5. The user may face financial or privacy risks.

### 🛡️ SafeNext Coach

Provides safety recommendations after analysis, such as:

- Do not share OTPs or passwords.
- Avoid opening suspicious links.
- Do not transfer money without verification.
- Block suspicious contacts.
- Report fraudulent content.
- Verify information using official sources.

### 🌐 Language Support

The platform supports language-based output where configured, helping users understand explanations and recommendations in their preferred language.

### 👤 User Features

- Registration
- Login and logout
- OTP verification
- User profile
- Profile picture support
- ScamCheck history
- Scam reporting
- Feedback system
- Analysis history

---

## 🏗️ System Architecture

```text
                         ┌───────────────────┐
                         │       User        │
                         └─────────┬─────────┘
                                   │
                                   ▼
                         ┌───────────────────┐
                         │   Flask Web App   │
                         └─────────┬─────────┘
                                   │
              ┌────────────────────┼────────────────────┐
              │                    │                    │
              ▼                    ▼                    ▼
      Message Detector      Phone Detector       Link Detector
              │                    │                    │
              └────────────────────┼────────────────────┘
                                   │
                                   ▼
                         ┌───────────────────┐
                         │ Screenshot Module │
                         └─────────┬─────────┘
                                   │
                                   ▼
                         ┌───────────────────┐
                         │    Risk Engine    │
                         └─────────┬─────────┘
                                   │
              ┌────────────────────┼────────────────────┐
              │                    │                    │
              ▼                    ▼                    ▼
      Scam Fingerprint      Attack Chain       SafeNext Coach
                                   │
                                   ▼
                         ┌───────────────────┐
                         │   Final Result    │
                         │ Score + Guidance  │
                         └───────────────────┘
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
SafeNext Safety Guidance
    │
    ▼
Final Result and History
```

---

## 📈 Risk Classification

| Risk Score | Classification |
|------------|----------------|
| 0–29       | LOW RISK       |
| 30–59      | SUSPICIOUS     |
| 60–79      | HIGH RISK      |
| 80–100     | VERY HIGH RISK |

> Risk scores are indicators generated by the system. A result marked as safe does not guarantee that content is completely safe.

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

### AI and Analysis

- Google GenAI integration
- Requests
- BeautifulSoup
- Pillow
- OpenCV
- NumPy
- Python-based detection modules

### Frontend

- HTML
- CSS
- JavaScript
- Bootstrap/Tailwind where configured

### Deployment

- Vercel for the live project interface
- Python-compatible hosting support for backend deployment

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

## ⚙️ Local Installation

### 1. Clone the Repository

```bash
git clone https://github.com/umesh-kumar-meghwal/SarvShield.git
cd SarvShield
```

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

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

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

> Do not upload your `.env` file or private API keys to GitHub.

### 5. Run the Application

```bash
python app.py
```

Open the local application:

```text
http://127.0.0.1:5000
```

For production execution with Gunicorn:

```bash
gunicorn app:app
```

---

## 🔐 Security Considerations

- Never expose API keys publicly.
- Store secrets in environment variables.
- Use secure password handling.
- Validate uploaded files.
- Restrict upload size and file types.
- Do not trust user-provided URLs.
- Use HTTPS in production.
- Store only necessary personal information.
- Protect authentication and session data.
- Verify suspicious content through official sources.

---

## 👥 Team Members

Our college internal hackathon team consists of six members. Every member contributed to different parts of the project, including backend development, frontend development, database management, AI model research, presentation, and technical research.

| No. | Team Member | Responsibilities |
|-----|-------------|------------------|
| 1 | **Siddhika Modi (Team Leader)** | Database Management, Presentation, Research, AI Model |
| 2 | **Umesh Kumar Meghwal** | Backend Development, Backend Integration, AI Model |
| 3 | **Suhana Khan** | Frontend Development, Presentation, Research, AI Model |
| 4 | **Lakshika Nandawana** | Research, Presentation, Database Management, AI Model |
| 5 | **Amit Potter** | Frontend Development, AI Model |
| 6 | **Alveera** | Backend Development, AI Model |

### 🧠 AI Model Contribution

AI model development was a collaborative effort by the entire team.

- **Siddhika Modi:** AI model development and research.
- **Suhana Khan:** AI model development and research.
- **All Team Members:** Contributed ideas, research, testing, feedback, and improvements related to the AI model.

### 🤝 Team Collaboration

The team worked collaboratively on:

- Backend development
- Frontend development
- Database management
- AI model research and integration
- Presentation preparation
- Technical research
- Testing and feedback
- Project improvement

---

## 🔮 Future Improvements

Possible future improvements include:

- Real-time threat intelligence
- Advanced AI-based screenshot analysis
- Improved phishing URL detection
- Browser extension
- Mobile application
- Automated scam reporting
- Community-based threat database
- Improved multilingual support
- Real-time alerts
- Advanced admin analytics
- Explainable AI reports
- Additional intelligence sources

---

## ⚠️ Disclaimer

SarvShield is designed as a digital safety assistance and awareness platform.

Detection results may not always be accurate. A result marked as safe does not guarantee that the content is completely safe.

Users should verify suspicious messages, websites, phone numbers, and payment requests through trusted official sources.

SarvShield does not replace official cybersecurity authorities or professional investigation.

---

## 🤝 Contributing

Contributions, suggestions, and improvements are welcome.

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

---

### 🛡️ Stay Alert. Stay Safe. Stay Protected with SarvShield.
