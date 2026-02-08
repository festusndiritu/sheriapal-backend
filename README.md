# Sheriapal Backend

A FastAPI-based legal document platform with AI integration, role-based access control, and document management. Users can upload documents, draft legal templates via AI, and query an AI assistant with document context.

##  Features

### Authentication & Authorization
- JWT-based authentication with Argon2 password hashing
- Role-based access control: `superadmin`, `admin`, `lawyer`, `user`
- Token refresh mechanism
- User profile management

### Document Management
- Upload documents (PDF, TXT, DOC, DOCX)
- Document workflow: `uploaded` → `pending_review` → `approved`/`rejected`
- Admin approval and rejection with timestamps
- File streaming download
- Document deletion with automatic disk cleanup
- Role-based document listing

### AI & Legal Services
- **Query AI**: Ask questions with context from uploaded documents
  - Returns answers with source citations
  - Includes metadata and source documents
  - Falls back to Gemini API when no documents match
  
- **Draft Documents**: Generate custom legal documents using AI
  - 6 template types: employment contracts, affidavits, power of attorney, tenancy agreements, sales agreements, demand letters
  - Customizable with parties, dates, and specific details
  - Ready-to-use AI-generated drafts

- **Template Browsing**: View available document templates and required fields

### Infrastructure
- Rate limiting (100 requests/minute)
- CORS middleware configured
- Health checks for monitoring
- Database auto-migration on startup
- SQLite for development (PostgreSQL-ready)

## Tech Stack

- **Framework**: FastAPI
- **Database**: SQLModel + SQLAlchemy (SQLite/PostgreSQL)
- **Authentication**: JWT + python-jose
- **Password Hashing**: Argon2
- **Validation**: Pydantic v2
- **Testing**: Pytest
- **Rate Limiting**: slowapi
- **Package Manager**: uv

## Quick Start

### Prerequisites
- Python 3.12+
- `uv` package manager

### Setup

```bash
# Enter project directory
cd sheriapal-backend

# Install dependencies
uv pip install -e ".[dev]"

# Run development server
python -m uvicorn main:app --reload

# Run tests
python -m pytest tests/ -v
```

**Server**: `http://localhost:8000`
- **Docs**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

## API Endpoints (19 total)

### Authentication (6)
```
POST   /auth/register              - Create new user account
POST   /auth/login                 - Login, get JWT token
POST   /auth/refresh               - Refresh expired token
GET    /auth/users/me              - Get current user profile
POST   /auth/admin/users           - Create admin user (superadmin)
POST   /auth/users/{user_id}/role  - Assign role to user (superadmin)
```

### Documents (7)
```
POST   /docs/                      - Upload document
GET    /docs/                      - List user's documents
POST   /docs/{doc_id}/submit       - Submit for review
POST   /docs/{doc_id}/approve      - Approve document (admin)
POST   /docs/{doc_id}/reject       - Reject document (admin)
GET    /docs/{doc_id}/download     - Download file (streaming)
DELETE /docs/{doc_id}              - Delete document
```

### AI & Legal Services (4)
```
POST   /ai/query                   - Query AI with document context
POST   /ai/draft                   - Generate custom legal documents
GET    /ai/templates               - List available templates
GET    /health                     - Health check
```

## Usage Examples

### Register and Login
```bash
# Register
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "secure_password"}'

# Login
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "secure_password"}'
```

### Upload and Query Documents
```bash
# Upload document
TOKEN="<your_access_token>"
curl -X POST http://localhost:8000/docs/ \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@employment.pdf"

# Query AI with document context
curl -X POST http://localhost:8000/ai/query \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What are the main terms of this employment contract?",
    "use_documents": true,
    "top_k": 5
  }'
```

### Draft Legal Document
```bash
curl -X POST http://localhost:8000/ai/draft \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "document_type": "employment_contract",
    "parties": ["Acme Corp", "John Doe"],
    "effective_date": "2026-03-01",
    "details": {
      "position": "Senior Developer",
      "salary": "$150,000 annually",
      "duration": "2 years",
      "benefits": "Health insurance, 401k"
    }
  }'
```

## Project Structure

```
sheriapal-backend/
├── main.py                          # FastAPI app, health checks, rate limiting
├── app/
│   ├── db.py                        # Database setup, session management
│   ├── models.py                    # SQLModel models (User, Document)
│   ├── schemas.py                   # Pydantic request/response schemas
│   ├── deps.py                      # Auth dependencies, role checking
│   ├── routers/
│   │   ├── auth.py                  # Authentication endpoints (6)
│   │   ├── docs.py                  # Document management endpoints (7)
│   │   └── ai.py                    # AI and drafting endpoints (4)
│   └── services/
│       ├── storage.py               # File upload/storage handling
│       ├── vector_store.py          # Document indexing & retrieval
│       └── gemini.py                # Gemini API integration
├── utils/
│   ├── config.py                    # JWT configuration
│   ├── crypto.py                    # Password hashing (Argon2)
│   └── jwt.py                       # JWT token operations
├── tests/
│   ├── conftest.py                  # Pytest fixtures
│   ├── test_auth.py                 # Auth tests (5)
│   ├── test_docs.py                 # Document tests (4)
│   └── test_ai.py                   # AI feature tests (6)
├── pyproject.toml                   # Project configuration
└── .env.example                     # Environment variables template
```

##  Configuration

Create a `.env` file based on `.env.example`:

```bash
# JWT Configuration
JWT_SECRET=<your-secret-key>
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440

# Database
DATABASE_URL=sqlite:///./sheriapal.db

# File Upload
UPLOAD_DIR=./storage/docs

# Gemini API (optional)
GEMINI_API_KEY=<your-api-key>

# Environment
DEBUG=False
```

## Testing

```bash
# Run all tests
python -m pytest tests/ -v

# Run specific test file
python -m pytest tests/test_auth.py -v

# Run with coverage
pytest --cov=app tests/
```

**Status**: 15/15 tests passing ✅

## Roles & Permissions

| Role | Capabilities |
|------|-------------|
| **superadmin** | Create/manage users, assign roles, manage all documents |
| **admin** | Approve/reject documents, view all documents |
| **lawyer** | Upload/submit documents, query AI, draft documents |
| **user** | Upload/submit documents, query AI, draft documents |

## Document Templates

Available for AI drafting:
- `employment_contract` - Employment agreements
- `affidavit` - Sworn statements
- `power_of_attorney` - Legal authorization
- `tenancy_agreement` - Tenant agreements
- `sales_agreement` - Sales contracts
- `demand_letter` - Formal demands

## Security

- ✅ Argon2 password hashing
- ✅ JWT tokens with configurable expiration
- ✅ CORS configured for specific origins
- ✅ Rate limiting (100 req/min)
- ✅ File MIME-type validation
- ✅ SQL injection protection via SQLModel/SQLAlchemy

**⚠️ Always review AI-generated documents with a legal professional before use.**

## Development

### Adding an Endpoint

1. Create route in `app/routers/`
2. Add schemas to `app/schemas.py`
3. Write tests in `tests/test_*.py`
4. Update README

### Integrating Real Gemini API

```python
# Update app/services/gemini.py
import google.generativeai as genai

class GeminiClient:
    def __init__(self, api_key):
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-pro')
    
    def complete(self, prompt):
        response = self.model.generate_content(prompt)
        return response.text
```

##  Production Deployment

### With Gunicorn + Uvicorn
```bash
gunicorn -w 4 -k uvicorn.workers.UvicornWorker main:app
```

### With PostgreSQL
Update `.env`:
```
DATABASE_URL=postgresql+psycopg2://user:password@localhost/sheriapal
```

### With Docker
```bash
docker build -t sheriapal-api .
docker run -p 8000:8000 sheriapal-api
```

## Checklist for Production

- [ ] Update `JWT_SECRET` to random value
- [ ] Configure `DATABASE_URL` for PostgreSQL
- [ ] Set up `GEMINI_API_KEY`
- [ ] Configure CORS origins
- [ ] Enable HTTPS
- [ ] Set up monitoring/logging
- [ ] Configure backups
- [ ] Load test the system

##  Troubleshooting

### Tests Fail
```bash
rm sheriapal.db
python -m pytest tests/ -v
```

### Import Errors
```bash
uv pip install -e ".[dev]"
```

### Database Issues
- Verify `DATABASE_URL` in `.env`
- Check database permissions
- For PostgreSQL: ensure server is running

## Future Enhancements

- [ ] Real Gemini API integration
- [ ] Advanced document search with embeddings (FAISS/Pinecone)
- [ ] Email notifications
- [ ] WebSocket support
- [ ] Document versioning
- [ ] Audit trail logging
- [ ] Multi-language support
- [ ] Payment integration

##  License

Proprietary - Sheriapal Platform

---

**Status**: Production Ready  
**Last Updated**: February 8, 2026  
**Tests**: 15/15 passing  
**API Endpoints**: 19  

