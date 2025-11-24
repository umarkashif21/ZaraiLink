# Backend API Implementation - Complete

## ✅ Implementation Summary

Successfully implemented complete token-based contact unlocking REST API.

---

## Files Created/Modified

### New Files Created:
1. **/backend/companies/serializers.py** - REST API serializers
2. **/backend/companies/views.py** - API viewsets and views  
3. **/backend/companies/urls.py** - URL routing

### Modified Files:
1. **/backend/zarailink/settings.py** - Added `rest_framework` to INSTALLED_APPS
2. **/backend/zarailink/urls.py** - Added `/api/` routes
3. **/backend/accounts/models.py** - Added `token_balance` field + methods
4. **/backend/accounts/views.py** - Updated login/check-auth to include token_balance

---

## API Endpoints Implemented

### Company Endpoints:
- `GET /api/companies/` - List companies with filters (search, region, sector, type, role)
- `GET /api/companies/{id}/` - Get company details with products and contacts
- `GET /api/companies/regions/` - Get available regions

### Contact Endpoints:
- `GET /api/key-contacts/?company={id}` - List company contacts
- `POST /api/key-contacts/{id}/unlock/` - Unlock contact (requires auth, deducts token)

### Reference Data:
- `GET /api/sectors/` - List all sectors
- `GET /api/company-types/` - List all company types
- `GET /api/company-roles/` - List all company roles

---

## Key Features

### 1. Dynamic Contact Hiding
Contacts show limited info until unlocked:
- **Locked:** Name, designation visible | Phone/email/WhatsApp = "🔒 Locked"
- **Unlocked:** Full contact info visible
- **Public:** Always visible (no token required)

### 2. Token Deduction Logic
```python
# Unlock endpoint checks:
1. Already unlocked? → Return contact data
2. Public contact? → Create unlock record (no charge)
3. Has tokens? → Deduct 1 token, create unlock record
4. Insufficient tokens? → Return 402 error
```

### 3. Database Relationships
- [KeyContactUnlock](file:///home/rolex/Salman%20Adnan/HU%20Files/7th%20Semester/FYP/Zarailink-Code/backend/companies/models.py#210-235) junction table tracks unlocks
- Unique constraint prevents double-charging
- Timestamps for audit trail

---

## Testing the Backend

### 1. Start Django Server:
```bash
cd backend
python manage.py migrate  # Apply pending migrations
python manage.py runserver
```

### 2. Test Endpoints (using curl/Postman):

**List companies:**
```bash
curl http://localhost:8000/api/companies/
```

**Search companies:**
```bash
curl "http://localhost:8000/api/companies/?search=sugar&region=Punjab"
```

**Get company details:**
```bash
curl http://localhost:8000/api/companies/1/
```

**Unlock contact (requires login):**
```bash
curl -X POST http://localhost:8000/api/key-contacts/1/unlock/ \
  -H "Cookie: sessionid=YOUR_SESSION_ID"
```

---

## User Model Changes

### New Field:
```python
token_balance = IntegerField(default=0)
```

### New Methods:
- [has_tokens(amount=1)](file:///home/rolex/Salman%20Adnan/HU%20Files/7th%20Semester/FYP/Zarailink-Code/backend/accounts/models.py#57-60) - Check balance
- [deduct_tokens(amount=1)](file:///home/rolex/Salman%20Adnan/HU%20Files/7th%20Semester/FYP/Zarailink-Code/backend/accounts/models.py#61-68) - Deduct and save
- [add_tokens(amount)](file:///home/rolex/Salman%20Adnan/HU%20Files/7th%20Semester/FYP/Zarailink-Code/backend/accounts/models.py#69-73) - Add and save

### Updated Responses:
Login and check-auth now return:
```json
{
  "user": {
    "name": "...",
    "email": "...",
    "email_verified": true,
    "token_balance": 10  // NEW
  }
}
```

---

## Next Steps

1. **Apply migration** to add token_balance field
2. **Give users tokens** via Django admin or subscription system
3. **Implement frontend** to consume these APIs
4. **Test unlock flow** end-to-end

---

## Migration Note

Pending migration:
- `accounts/migrations/0003_user_token_balance.py`
- Adds `token_balance` field (default: 0) to all users
- Safe to apply - no data loss
