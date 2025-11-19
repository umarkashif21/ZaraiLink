# ZaraiLink Email Verification Setup Guide

This guide will help you configure Gmail SMTP to send real verification emails for ZaraiLink.

## 📋 Prerequisites

- A Gmail account
- Python 3.8+ installed
- Node.js LTS installed

---

## 🔐 Step 1: Generate Gmail App Password

Google requires an "App Password" for third-party applications to send emails via Gmail SMTP.

### Instructions:

1. **Enable 2-Step Verification** (if not already enabled):
   - Go to https://myaccount.google.com/security
   - Click on "2-Step Verification"
   - Follow the prompts to enable it

2. **Generate App Password**:
   - Go to https://myaccount.google.com/apppasswords
   - Sign in if prompted
   - In the "Select app" dropdown, choose "Mail"
   - In the "Select device" dropdown, choose "Other (Custom name)"
   - Enter "ZaraiLink" as the custom name
   - Click "Generate"
   - **Copy the 16-character password** (it will look like: `abcd efgh ijkl mnop`)
   - **Save this password securely** - you won't be able to see it again!

---

## ⚙️ Step 2: Configure Backend Environment Variables

1. **Navigate to the backend directory**:
   ```bash
   cd backend
   ```

2. **Create a `.env` file** (copy from .env.example):
   ```bash
   cp .env.example .env
   ```

3. **Edit the `.env` file** with your credentials:
   ```env
   # Django Secret Key (keep this secret!)
   SECRET_KEY=django-insecure-q*&&ex7!4ntiu9(h3nx+n51snfjts*hn7415&q6yu0nl2e9=g@

   # Email Configuration (Gmail)
   EMAIL_HOST_USER=your-email@gmail.com
   EMAIL_HOST_PASSWORD=abcd efgh ijkl mnop

   # Frontend URL (for email verification links)
   FRONTEND_URL=http://localhost:3000
   ```

   **Replace**:
   - `your-email@gmail.com` with your actual Gmail address
   - `abcd efgh ijkl mnop` with the App Password you generated (remove spaces)

   **Example**:
   ```env
   EMAIL_HOST_USER=john.doe@gmail.com
   EMAIL_HOST_PASSWORD=abcdefghijklmnop
   ```

---

## 🚀 Step 3: Install Dependencies

### Backend:

```bash
cd backend
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### Frontend:

```bash
cd frontend
npm install
```

---

## 🗄️ Step 4: Run Database Migrations

```bash
cd backend
source venv/bin/activate
python manage.py migrate
```

---

## 🎯 Step 5: Test the Email System

### Start the Backend:

```bash
cd backend
source venv/bin/activate
python manage.py runserver
```

You should see:
```
Starting development server at http://127.0.0.1:8000/
```

### Start the Frontend (in a new terminal):

```bash
cd frontend
npm start
```

Browser should automatically open at: `http://localhost:3000`

---

## ✅ Step 6: Test Complete Flow

1. **Sign Up**:
   - Go to `http://localhost:3000/signup`
   - Fill in the registration form
   - Click "Verify Your Email"

2. **Check Your Email**:
   - Open your Gmail inbox
   - You should receive an email from ZaraiLink with the subject: **"Verify your ZaraiLink Account"**
   - The email will have a green "Verify Email Address" button

3. **Click Verification Link**:
   - Click the button in the email
   - You'll be redirected to a success page
   - After 3 seconds, you'll be redirected to the login page

4. **Login**:
   - Enter your email and password
   - You should successfully log in!

---

## 🔧 Troubleshooting

### Email Not Sending

**Check 1: App Password is Correct**
- Make sure you copied the App Password correctly (16 characters, no spaces)
- Try generating a new App Password if needed

**Check 2: Environment Variables Loaded**
- Verify `.env` file exists in `/backend` directory
- Check that variables are set correctly (no quotes needed)
- Restart the Django server after changing `.env`

**Check 3: Gmail Security Settings**
- Ensure 2-Step Verification is enabled
- Check https://myaccount.google.com/lesssecureapps is OFF (use App Passwords instead)

**Check 4: Check Django Console for Errors**
- Look at the terminal where Django is running
- Any email errors will be displayed there

### Email Goes to Spam

- Check your Gmail Spam folder
- Mark the email as "Not Spam" to whitelist it
- For production, consider using a dedicated email service (SendGrid, AWS SES, etc.)

### Verification Link Expired

- Verification links expire after **24 hours**
- Request a new verification email from the "Email Verification" page
- Click "Resend Verification Email"

### Login Says "Email Not Verified"

- Make sure you clicked the verification link in the email
- The email must be verified before you can login
- Check your email for the verification link

---

## 📧 Email Content

Users will receive a professional HTML email with:
- ZaraiLink branding (green theme)
- Clear "Verify Email Address" button
- Direct verification link
- 24-hour expiration notice
- Plain text fallback for email clients that don't support HTML

---

## 🔒 Security Notes

1. **Never commit `.env` file to git** - It contains sensitive credentials
2. **Keep your App Password secure** - Treat it like a password
3. **Regenerate App Password** if you suspect it's compromised
4. **For Production**:
   - Use environment variables or secret management services
   - Consider using dedicated email services (SendGrid, AWS SES, Mailgun)
   - Set up SPF, DKIM, and DMARC records for better deliverability

---

## 🌐 Production Deployment Notes

When deploying to production:

1. **Update FRONTEND_URL** in `.env`:
   ```env
   FRONTEND_URL=https://your-production-domain.com
   ```

2. **Consider Using Dedicated Email Services**:
   - **SendGrid**: Free tier allows 100 emails/day
   - **AWS SES**: Very affordable, great for high volume
   - **Mailgun**: 5000 free emails/month
   - **Postmark**: Excellent deliverability

3. **Update Django Settings for Production**:
   - Set `DEBUG = False`
   - Use a secure `SECRET_KEY` from environment
   - Configure `ALLOWED_HOSTS`
   - Use PostgreSQL instead of SQLite

---

## 📞 Support

If you encounter any issues:

1. Check the troubleshooting section above
2. Review the Django server logs for error messages
3. Ensure all environment variables are set correctly
4. Verify Gmail App Password is valid

---

**Ready to Go!** 🚀

Your ZaraiLink email verification system is now fully configured!
