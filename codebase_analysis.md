# ZaraiLink - Complete Codebase Analysis

## Executive Summary

**ZaraiLink** is an Agri-Trade Intelligence Platform designed to connect buyers and suppliers in Pakistan's agricultural sector. Currently, it's a **partially implemented** full-stack web application with a functional authentication system but placeholder features for trade directory and subscriptions.

**Tech Stack:**
- **Backend:** Django 4.2.7 + Django REST Framework (session-based authentication)
- **Frontend:** React 19.2.0 + React Router + Tailwind CSS
- **Database:** PostgreSQL (configured for production)
- **Email:** SMTP (Gmail) for verification emails

---

## Backend Architecture (Django)

### Project Structure
```
backend/
├── zarailink/          # Main project configuration
├── accounts/           # User authentication & management (FULLY IMPLEMENTED)
├── subscriptions/      # Subscription plans (STUB - NOT IMPLEMENTED)
└── trade_directory/    # Supplier/Buyer directory (STUB - NOT IMPLEMENTED)
```

### 1. Core Configuration ([zarailink/settings.py](file:///home/rolex/Salman%20Adnan/HU%20Files/7th%20Semester/FYP/Zarailink-Code/backend/zarailink/settings.py))

**Database:**
- PostgreSQL configured with credentials (name: `zarailink`, user: `postgres`)
- Runs on localhost:5432

**Security:**
- Custom User model: `AUTH_USER_MODEL = 'accounts.User'`
- CORS enabled for React frontend (localhost:3000)
- Session-based authentication (cookies, not JWT despite what README mentions)
- CSRF protection with trusted origins

**Email System:**
- SMTP backend via Gmail
- Credentials loaded from [.env](file:///home/rolex/Salman%20Adnan/HU%20Files/7th%20Semester/FYP/Zarailink-Code/backend/.env) file
- Sends HTML + plain text verification emails

**Environment Variables:**
- `SECRET_KEY` - Django secret
- `EMAIL_HOST_USER` - Gmail address
- `EMAIL_HOST_PASSWORD` - Gmail app password
- `FRONTEND_URL` - React app URL (default: http://localhost:3000)

### 2. User Model ([accounts/models.py](file:///home/rolex/Salman%20Adnan/HU%20Files/7th%20Semester/FYP/Zarailink-Code/backend/accounts/models.py))

Custom User extending `AbstractUser`:

**Fields:**
- [email](file:///home/rolex/Salman%20Adnan/HU%20Files/7th%20Semester/FYP/Zarailink-Code/backend/accounts/views.py#249-280) - Unique, primary identifier (USERNAME_FIELD)
- `username` - Optional, can be blank
- `first_name`, `last_name` - Required for registration
- `bio` - Optional text field (max 500 chars)
- `country` - Optional country selection
- `email_verified` - Boolean flag (default: False)
- [verification_token](file:///home/rolex/Salman%20Adnan/HU%20Files/7th%20Semester/FYP/Zarailink-Code/backend/accounts/models.py#36-42) - UUID4 token for email verification
- `token_created_at` - Timestamp for token expiration (24 hours)

**Key Methods:**
- [is_verification_token_valid()](file:///home/rolex/Salman%20Adnan/HU%20Files/7th%20Semester/FYP/Zarailink-Code/backend/accounts/models.py#36-42) - Checks if token is within 24-hour window
- [regenerate_verification_token()](file:///home/rolex/Salman%20Adnan/HU%20Files/7th%20Semester/FYP/Zarailink-Code/backend/accounts/models.py#43-48) - Creates new token for resend functionality

**Authentication Flow:**
- Email is the primary login identifier
- Users are set to `is_active=False` until email verification
- Password validation with Django's built-in validators

### 3. Authentication API Endpoints ([accounts/urls.py](file:///home/rolex/Salman%20Adnan/HU%20Files/7th%20Semester/FYP/Zarailink-Code/backend/accounts/urls.py) + [views.py](file:///home/rolex/Salman%20Adnan/HU%20Files/7th%20Semester/FYP/Zarailink-Code/backend/accounts/views.py))

**API Endpoints:**

| Endpoint | Method | Purpose | Status |
|----------|--------|---------|--------|
| `/accounts/api/signup/` | POST | Create new user account | ✅ Fully Implemented |
| `/accounts/api/login/` | POST | Authenticate user | ✅ Fully Implemented |
| `/accounts/api/logout/` | POST | End user session | ✅ Fully Implemented |
| `/accounts/api/check-auth/` | GET | Verify authentication status | ✅ Fully Implemented |
| `/accounts/api/verify-email/<token>/` | GET | Verify email via token | ✅ Fully Implemented |
| `/accounts/api/resend-verification/` | POST | Resend verification email | ✅ Fully Implemented |
| `/accounts/api/forgot-password/` | POST | Initiate password reset | ✅ Fully Implemented |
| `/accounts/password_reset_confirm/<uidb64>/<token>/` | GET | Server-rendered password reset | ✅ Django built-in |

#### Signup Flow ([api_signup](file:///home/rolex/Salman%20Adnan/HU%20Files/7th%20Semester/FYP/Zarailink-Code/backend/accounts/views.py#38-153)):
1. Receive user data (name, email, password, country)
2. Validate with [UserRegisterForm](file:///home/rolex/Salman%20Adnan/HU%20Files/7th%20Semester/FYP/Zarailink-Code/backend/accounts/forms.py#8-48) (Django form)
3. Split name into first_name/last_name
4. Create user with `is_active=False` and `email_verified=False`
5. Generate UUID verification token
6. Send styled HTML verification email
7. Return success response

**Validation:**
- Email uniqueness checked by Django
- Password minimum 8 characters
- Password complexity validated by Django validators
- Country selection required

#### Login Flow ([api_login](file:///home/rolex/Salman%20Adnan/HU%20Files/7th%20Semester/FYP/Zarailink-Code/backend/accounts/views.py#155-196)):
1. Check if email exists and is verified (before authentication)
2. Authenticate credentials
3. Return error if email not verified (HTTP 403)
4. Create session via Django's [login()](file:///home/rolex/Salman%20Adnan/HU%20Files/7th%20Semester/FYP/Zarailink-Code/frontend/src/context/AuthContext.js#42-66) function
5. Return user data (name, email, email_verified)

**Security:**
- CSRF protection disabled via `@csrf_exempt` (API endpoints)
- Session cookies used for authentication state
- Email verification required before login

#### Email Verification ([api_verify_email](file:///home/rolex/Salman%20Adnan/HU%20Files/7th%20Semester/FYP/Zarailink-Code/backend/accounts/views.py#249-280)):
1. Receive token from URL parameter
2. Query user by [verification_token](file:///home/rolex/Salman%20Adnan/HU%20Files/7th%20Semester/FYP/Zarailink-Code/backend/accounts/models.py#36-42)
3. Check if already verified → redirect to frontend with status
4. Check if token expired (>24 hours) → redirect with expired status
5. Set `email_verified=True` and `is_active=True`
6. Redirect to React app with verification result

**Redirect URLs:**
- Success: `{FRONTEND_URL}/verify-email/{token}?status=verified`
- Already verified: `{FRONTEND_URL}/verify-email/{token}?status=already_verified`
- Expired: `{FRONTEND_URL}/verify-email/{token}?status=expired`
- Invalid: `{FRONTEND_URL}/verify-email/{token}?status=invalid`

#### Password Reset Flow:
1. User submits email via `/accounts/api/forgot-password/`
2. Backend generates token using Django's `default_token_generator`
3. Sends email with reset link
4. Django's built-in views handle password reset confirmation

**Email Templates:**
- Branded HTML emails with ZaraiLink green theme (#1A4D2E)
- Includes company tagline: "Optimize Data. Empower Tomorrow."
- Plain text fallback included

### 4. Placeholder Apps

**`subscriptions/` and `trade_directory/`:**
- Empty models (only default Django boilerplate)
- No views, URLs, or functionality
- Mentioned in README but not implemented
- Frontend has UI components but no backend integration

---

## Frontend Architecture (React)

### Project Structure
```
frontend/src/
├── App.js              # Main routing configuration
├── index.js            # React root
├── components/
│   ├── Auth/           # Authentication pages (6 components)
│   ├── Dashboard/      # Main dashboard (2 components)
│   ├── TradeDirectory/ # Trade features (5 components, UI only)
│   ├── Subscriptions/  # Subscription page (1 component, UI only)
│   ├── Common/         # Shared components (3 components)
│   └── Layout/         # Navigation components (2 components)
├── context/
│   └── AuthContext.js  # Authentication state management
└── services/
    └── api.js          # Empty file (not used)
```

### 1. Routing & Protection ([App.js](file:///home/rolex/Salman%20Adnan/HU%20Files/7th%20Semester/FYP/Zarailink-Code/frontend/src/App.js))

**Routes:**

| Path | Component | Protection | Redirect Behavior |
|------|-----------|------------|-------------------|
| `/` | - | - | Redirects to `/login` |
| `/signup` | Signup | PublicRoute | If logged in → `/dashboard` |
| `/login` | Login | PublicRoute | If logged in → `/dashboard` |
| `/forgot-password` | ForgotPassword | None | - |
| `/verify-email` | EmailVerification | None | - |
| `/verify-email/:token` | VerifyEmailSuccess | None | - |
| `/reset-password/:token` | ResetPassword | None | - |
| `/dashboard` | Dashboard | ProtectedRoute | If not logged in → `/login` |

**Route Guards:**
- [ProtectedRoute](file:///home/rolex/Salman%20Adnan/HU%20Files/7th%20Semester/FYP/Zarailink-Code/frontend/src/App.js#23-41): Requires authentication, shows loading spinner during check
- [PublicRoute](file:///home/rolex/Salman%20Adnan/HU%20Files/7th%20Semester/FYP/Zarailink-Code/frontend/src/App.js#42-60): Redirects authenticated users to dashboard
- Loading state prevents flash of wrong content

### 2. Authentication Context ([AuthContext.js](file:///home/rolex/Salman%20Adnan/HU%20Files/7th%20Semester/FYP/Zarailink-Code/frontend/src/context/AuthContext.js))

**State Management:**
- Global auth state using React Context API
- Provides `user`, [login](file:///home/rolex/Salman%20Adnan/HU%20Files/7th%20Semester/FYP/Zarailink-Code/frontend/src/context/AuthContext.js#42-66), [logout](file:///home/rolex/Salman%20Adnan/HU%20Files/7th%20Semester/FYP/Zarailink-Code/frontend/src/context/AuthContext.js#67-79), `loading`, `isAuthenticated`

**Initialization:**
- On mount, calls `/accounts/api/check-auth/` to verify existing session
- Automatically logs user in if valid session exists
- Sets loading to false after check completes

**Login Method:**
```javascript
login(email, password)
  → POST /accounts/api/login/
  → Returns: { success, user, error, email_not_verified }
  → Updates user state on success
```

**Logout Method:**
```javascript
logout()
  → POST /accounts/api/logout/
  → Clears user state
```

**Key Feature:**
- Uses `credentials: 'include'` for all fetch calls to send cookies
- No manual token management (session-based)

### 3. Authentication Components

#### **Signup.js** (254 lines)
**Features:**
- Full name, email, password, confirm password, country dropdown
- Client-side validation:
  - Email format regex
  - Password minimum 8 characters
  - Password strength indicator (Weak/Moderate/Strong)
  - Matching password confirmation
  - Country selection required
- Country list with 195+ countries
- Backend error mapping from Django form errors
- Navigates to `/verify-email` on success with email in state

**UI:**
- Tailwind CSS with green theme (#1A4D2E)
- Gradient background (green-50 to green-100)
- Terms of Service and Privacy Policy placeholders
- Loading state with disabled button

#### **Login.js** (162 lines)
**Features:**
- Email and password fields
- Client-side email format validation
- Integration with AuthContext for login
- Special handling for unverified emails:
  - Shows error message
  - Provides link to resend verification
- Forgot password link
- Sign up link for new users

**Error Handling:**
- Email not verified → shows `email_not_verified` error
- Invalid credentials → generic error message
- Network errors → user-friendly message

#### **EmailVerification.js** (120 lines)
**Features:**
- Displays email address passed from Signup
- Resend verification button with loading state
- Calls `/accounts/api/resend-verification/` endpoint
- Shows success/error messages

**Known Issue (from TODO.txt):**
- Resend email verification doesn't work when redirected from Login page
- Works fine when coming from Signup page

#### **VerifyEmailSuccess.js** (status handler)
**Handles URL statuses:**
- `?status=verified` → Success message
- `?status=already_verified` → Already verified message
- `?status=expired` → Expired token message
- `?status=invalid` → Invalid token message

#### **ForgotPassword.js** (164 lines)
**Features:**
- Email input with validation
- Currently uses **simulated API call** (setTimeout)
- Shows success screen with checkmark icon
- Resend option
- Back to Sign In button

**Note:** Password reset backend is implemented, but frontend uses mock data

#### **ResetPassword.js**
- Server-rendered Django template (not React)
- Handles actual password change

### 4. Dashboard Component ([Dashboard.js](file:///home/rolex/Salman%20Adnan/HU%20Files/7th%20Semester/FYP/Zarailink-Code/frontend/src/components/Dashboard/Dashboard.js))

**Features:**
- Welcome message with user's name
- Navbar with ZaraiLink branding and logout button
- User account info card (name, email, verification status)
- Feature cards for:
  - Trade Directory (placeholder)
  - Market Intelligence (placeholder)
  - Analytics Dashboard (placeholder)
  - Subscription Plans (placeholder)
- "Explore Features" button (not functional)

**Status Display:**
- Green checkmark if email verified
- Yellow "Pending Verification" if not verified

### 5. Trade Directory Components (UI Only - No Backend)

**Components:**
- [FindSuppliers.js](file:///home/rolex/Salman%20Adnan/HU%20Files/7th%20Semester/FYP/Zarailink-Code/frontend/src/components/TradeDirectory/FindSuppliers.js) - UI for searching suppliers
- [FindBuyers.js](file:///home/rolex/Salman%20Adnan/HU%20Files/7th%20Semester/FYP/Zarailink-Code/frontend/src/components/TradeDirectory/FindBuyers.js) - UI for searching buyers
- [CompanyProfile.js](file:///home/rolex/Salman%20Adnan/HU%20Files/7th%20Semester/FYP/Zarailink-Code/frontend/src/components/TradeDirectory/CompanyProfile.js) - Display company details
- [OverviewTab.js](file:///home/rolex/Salman%20Adnan/HU%20Files/7th%20Semester/FYP/Zarailink-Code/frontend/src/components/TradeDirectory/OverviewTab.js) - Company overview info
- [KeyContactsTab.js](file:///home/rolex/Salman%20Adnan/HU%20Files/7th%20Semester/FYP/Zarailink-Code/frontend/src/components/TradeDirectory/KeyContactsTab.js) - Contact information

**Status:** UI components exist but no backend API integration

### 6. Common Components

**[ContactUnlockModal.js](file:///home/rolex/Salman%20Adnan/HU%20Files/7th%20Semester/FYP/Zarailink-Code/frontend/src/components/Common/ContactUnlockModal.js):**
- Modal for unlocking contact details with tokens
- No backend implementation

**[TokenPurchaseModal.js](file:///home/rolex/Salman%20Adnan/HU%20Files/7th%20Semester/FYP/Zarailink-Code/frontend/src/components/Common/TokenPurchaseModal.js):**
- Modal for purchasing tokens
- No backend implementation

**[ProtectedRoute.js](file:///home/rolex/Salman%20Adnan/HU%20Files/7th%20Semester/FYP/Zarailink-Code/frontend/src/components/Common/ProtectedRoute.js):**
- Likely duplicate of route protection in App.js

### 7. Layout Components

**[Navbar.js](file:///home/rolex/Salman%20Adnan/HU%20Files/7th%20Semester/FYP/Zarailink-Code/frontend/src/components/Layout/Navbar.js) & [Sidebar.js](file:///home/rolex/Salman%20Adnan/HU%20Files/7th%20Semester/FYP/Zarailink-Code/frontend/src/components/Layout/Sidebar.js):**
- Navigation components for main app layout
- Not currently integrated into main app

### 8. Subscriptions Component

**[SubscriptionPage.js](file:///home/rolex/Salman%20Adnan/HU%20Files/7th%20Semester/FYP/Zarailink-Code/frontend/src/components/Subscriptions/SubscriptionPage.js):**
- UI for viewing/purchasing subscription plans
- No backend integration

---

## API Integration & Data Flow

### Current Implementation

**Authentication Flow:**
```
React Component
  ↓ (fetch with credentials: 'include')
Django View
  ↓ (session cookie authentication)
Database Query
  ↓
JSON Response
  ↓
React State Update
```

**Session Management:**
- CSRF cookies sent from Django
- Session ID stored in HTTP-only cookie
- `SESSION_COOKIE_AGE = 1209600` (2 weeks)
- `SESSION_EXPIRE_AT_BROWSER_CLOSE = False`

**CORS Configuration:**
- Allowed origins: `http://localhost:3000`, `http://127.0.0.1:3000`
- Credentials allowed for cookie sharing
- All standard HTTP methods permitted

### Missing Implementations

1. **Trade Directory API:**
   - No models for suppliers/buyers
   - No endpoints for searching/filtering
   - No contact unlock logic

2. **Subscription System:**
   - No subscription plans in database
   - No payment processing
   - No token management system

3. **API Service Layer:**
   - [services/api.js](file:///home/rolex/Salman%20Adnan/HU%20Files/7th%20Semester/FYP/Zarailink-Code/frontend/src/services/api.js) is empty
   - Direct fetch calls in components (not abstracted)

---

## Database Schema

### Current Tables (from migration)

**`accounts_user`:**
```sql
id (BigAutoField, PK)
password (CharField, hashed)
last_login (DateTimeField, nullable)
is_superuser (BooleanField)
first_name (CharField, max 150)
last_name (CharField, max 150)
is_staff (BooleanField)
is_active (BooleanField)
date_joined (DateTimeField, auto_now_add)
email (EmailField, UNIQUE)
username (CharField, nullable)
bio (CharField, max 500)
country (CharField, max 100, nullable)
email_verified (BooleanField, default False)
email_verification_token (UUIDField, UNIQUE)
token_created_at (DateTimeField)
```

**Django Auth Tables:**
- `auth_group`
- `auth_permission`
- `accounts_user_groups` (M2M)
- `accounts_user_user_permissions` (M2M)

### Missing Tables
- Subscription plans
- User subscriptions
- Tokens/credits
- Suppliers/Buyers
- Products/Commodities
- Contact unlock history

---

## Styling & Design System

### Tailwind CSS Configuration

**Primary Colors:**
- Brand Green: `#1A4D2E`
- Hover Darker Green: `#163f26`
- Background Gradients: `from-green-50 via-white to-green-100`

**Component Patterns:**
- Rounded corners: `rounded-lg` (8px), `rounded-2xl` (16px)
- Shadows: `shadow-sm`, `shadow-lg`
- Focus rings: `focus:ring-2 focus:ring-green-200`
- Button hover: `hover:bg-[#163f26]` with `transition`

**Email Design:**
- Consistent brand colors (#1A4D2E)
- Responsive max-width container (600px)
- Branded header, content area, footer
- Call-to-action buttons matching web design

---

## Known Issues & TODO Items

1. **Email Verification Resend Bug:**
   - Doesn't work when navigated from Login page
   - Works correctly from Signup flow
   - Issue: Email state not passed properly from Login → EmailVerification route

2. **Authentication Discrepancy:**
   - README mentions JWT authentication
   - Actual implementation uses session-based authentication
   - No JWT tokens in codebase

3. **Incomplete Features:**
   - Trade directory (0% backend, UI exists)
   - Subscriptions (0% backend, UI exists)
   - Token system (0% implemented)
   - Market intelligence (0% implemented)

4. **Security Considerations:**
   - DEBUG=True in settings (production unsafe)
   - CSRF disabled on API endpoints
   - Secret key in .env (good) but fallback in settings (bad)

---

## Setup & Dependencies

### Backend Dependencies ([requirements.txt](file:///home/rolex/Salman%20Adnan/HU%20Files/7th%20Semester/FYP/Zarailink-Code/backend/requirements.txt))
```
Django==4.2.7
djangorestframework==3.14.0
djangorestframework-simplejwt==5.3.0  # Installed but NOT used
django-cors-headers==4.3.1
python-dotenv==1.0.0
psycopg2-binary==2.9.11
```

### Frontend Dependencies ([package.json](file:///home/rolex/Salman%20Adnan/HU%20Files/7th%20Semester/FYP/Zarailink-Code/frontend/package.json))
```
react: 19.2.0
react-dom: 19.2.0
react-router-dom: 7.9.6
axios: 1.13.2  # Installed but NOT used (using fetch instead)
```

### Environment Setup Requirements
1. PostgreSQL database named `zarailink`
2. Gmail account with app password for SMTP
3. [.env](file:///home/rolex/Salman%20Adnan/HU%20Files/7th%20Semester/FYP/Zarailink-Code/backend/.env) file with SECRET_KEY, EMAIL_HOST_USER, EMAIL_HOST_PASSWORD
4. Node.js for React frontend
5. Python 3.8+ for Django backend

---

## Architecture Summary

### What Works ✅
1. Complete user registration with email verification
2. Login/logout with session management
3. Password reset flow
4. Email verification with 24-hour expiration
5. Protected routes on frontend
6. Styled, responsive UI with Tailwind CSS
7. PostgreSQL database integration

### What Doesn't Work ❌
1. Trade directory functionality (no backend)
2. Subscription plans (no backend)
3. Token/credit system (no backend)
4. Market intelligence features (no backend)
5. Resend verification from login page
6. No actual API service abstraction layer

### Current State
This is a **functional authentication system** with a **placeholder application**. The core user management is production-ready, but all advertised features (trade directory, subscriptions, market intelligence) are either completely missing or exist only as non-functional UI mockups.

The codebase is well-structured with clear separation of concerns, consistent styling, and good security practices for the implemented features. However, it's approximately **20% complete** based on the stated objectives in the README.
