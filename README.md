# Shopify Integration Backend

A comprehensive Django-based backend system for Shopify product management with advanced features including AI-powered search, background task processing, and real-time inventory tracking.

## 🚀 Features

- **REST API** endpoints for complete product management (CRUD operations)
- **Advanced filtering and searching** capabilities with semantic search
- **Shopify webhook integration** for real-time inventory updates
- **Customized Django admin interface** with bulk operations
- **Background tasks with Celery** for automated operations
- **AI-powered smart product search** using spaCy/Sentence Transformers
- **Automated inventory insights** and analytics
- **Product discount management** system
- **Inventory change logging** and audit trail
- **Docker containerization** for easy deployment

## 🛠️ Tech Stack

- **Backend**: Python 3.11, Django 4.2, Django REST Framework
- **Database**: PostgreSQL 15
- **Message Broker**: Redis 7
- **Background Tasks**: Celery 5.3.4
- **AI/NLP**: spaCy 3.7.2, Sentence Transformers 2.2.2
- **Containerization**: Docker & Docker Compose
- **Testing**: pytest, pytest-django
- **Data Processing**: pandas 2.1.3

## 📋 Prerequisites

- Docker and Docker Compose
- Python 3.11+ (for local development)
- Git

## 🚀 Quick Start with Docker

### 1. Clone the Repository
```bash
git clone <repository-url>
cd Shopify-Integration
```

### 2. Start All Services
```bash
docker-compose up -d
```

### 3. Run Database Migrations
```bash
docker-compose exec web python manage.py migrate
```

### 4. Create Admin User
```bash
docker-compose exec web python manage.py createsuperuser
```

### 5. Access the Application
- **Django Admin**: http://localhost:8000/admin/
- **API Base URL**: http://localhost:8000/api/v1/
- **API Documentation**: http://localhost:8000/api-auth/

## 🔧 Local Development Setup

### 1. Create Virtual Environment
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Set Environment Variables
Create a `.env` file:
```env
DEBUG=True
USE_SQLITE=True
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0
```

### 4. Start Redis (Required for Celery)
```bash
# Using Docker
docker run -d -p 6379:6379 redis:7

# Or install Redis locally
```

### 5. Run Migrations
```bash
python manage.py migrate
```

### 6. Create Superuser
```bash
python manage.py createsuperuser
```

### 7. Start Development Server
```bash
python manage.py runserver
```

### 8. Start Celery Workers (in separate terminals)
```bash
# Celery Worker
celery -A shop_integration worker -l INFO --pool=solo

# Celery Beat (for scheduled tasks)
celery -A shop_integration beat -l INFO
```

## 📚 API Endpoints

### Authentication
All API endpoints require authentication. Supported methods:
- **Basic Authentication**: Username/Password
- **Session Authentication**: For browser-based access

### Products API

#### List Products
```
GET /api/v1/products/
```
**Query Parameters:**
- `search`: Search by name, SKU, or description
- `min_price`, `max_price`: Filter by price range
- `in_stock`: Filter by stock availability (true/false)
- `ordering`: Sort by field (name, price, inventory_quantity, etc.)
- `page`: Pagination

**Response:**
```json
{
  "count": 100,
  "next": "http://localhost:8000/api/v1/products/?page=2",
  "previous": null,
  "results": [
    {
      "id": 1,
      "name": "Product Name",
      "sku": "SKU123",
      "price": "29.99",
      "inventory_quantity": 50,
      "description": "Product description",
      "created_at": "2025-07-30T10:00:00Z",
      "updated_at": "2025-07-30T10:00:00Z"
    }
  ]
}
```

#### Get Product Details
```
GET /api/v1/products/{id}/
```
**Response:**
```json
{
  "id": 1,
  "name": "Product Name",
  "sku": "SKU123",
  "price": "29.99",
  "inventory_quantity": 50,
  "description": "Product description",
  "shopify_id": "shopify_123",
  "last_inventory_update": "2025-07-30T10:00:00Z",
  "discounts": [
    {
      "id": 1,
      "name": "Summer Sale",
      "discount_percent": "15.00",
      "active": true,
      "start_date": "2025-07-01T00:00:00Z",
      "end_date": "2025-08-31T23:59:59Z"
    }
  ],
  "inventory_logs": [
    {
      "id": 1,
      "previous_quantity": 45,
      "new_quantity": 50,
      "change": 5,
      "change_type": "manual",
      "timestamp": "2025-07-30T10:00:00Z",
      "notes": "Restocked inventory"
    }
  ]
}
```

#### Create Product
```
POST /api/v1/products/
```
**Request Body:**
```json
{
  "name": "New Product",
  "sku": "SKU456",
  "price": "39.99",
  "inventory_quantity": 25,
  "description": "Product description",
  "shopify_id": "shopify_456"
}
```

#### Update Product
```
PUT /api/v1/products/{id}/
PATCH /api/v1/products/{id}/
```

#### Delete Product
```
DELETE /api/v1/products/{id}/
```

#### Update Inventory
```
POST /api/v1/products/{id}/update_inventory/
```
**Request Body:**
```json
{
  "quantity": 30,
  "notes": "Manual inventory adjustment"
}
```

#### Semantic Search
```
GET /api/v1/products/search/?q=query
```
**Features:**
- AI-powered semantic search using sentence transformers
- Ranks results by relevance
- Supports natural language queries

#### Product Insights
```
GET /api/v1/products/insights/
```
**Response:**
```json
{
  "total_products": 150,
  "low_stock_products": 12,
  "out_of_stock_products": 3,
  "average_price": "45.67",
  "total_inventory_value": "125000.00",
  "trending_products": [
    {
      "id": 1,
      "name": "Popular Product",
      "inventory_quantity": 10,
      "price": "29.99"
    }
  ],
  "recent_updates": [
    {
      "product_name": "Updated Product",
      "change": 5,
      "timestamp": "2025-07-30T10:00:00Z"
    }
  ]
}
```

### Product Discounts API

#### List Discounts
```
GET /api/v1/discounts/
```

#### Create Discount
```
POST /api/v1/discounts/
```
**Request Body:**
```json
{
  "product": 1,
  "name": "Holiday Sale",
  "discount_percent": "20.00",
  "active": true,
  "start_date": "2025-12-01T00:00:00Z",
  "end_date": "2025-12-31T23:59:59Z"
}
```

#### Bulk Create Discounts
```
POST /api/v1/discounts/bulk_create/
```
**Request Body:**
```json
{
  "discounts": [
    {
      "product": 1,
      "name": "Discount 1",
      "discount_percent": "10.00"
    },
    {
      "product": 2,
      "name": "Discount 2",
      "discount_percent": "15.00"
    }
  ]
}
```

### Shopify Webhook

#### Inventory Update Webhook
```
POST /api/v1/webhooks/shopify/inventory/
```
**Headers Required:**
- `X-Shopify-Hmac-Sha256`: HMAC signature for verification
- `X-Shopify-Shop-Domain`: Shopify shop domain
- `X-Shopify-Topic`: Webhook topic (e.g., "inventory_levels/update")

**Request Body:**
```json
{
  "id": 123456789,
  "inventory_item_id": 987654321,
  "location_id": 123456,
  "available": 50,
  "updated_at": "2025-07-30T10:00:00Z"
}
```

## 🔍 Data Models

### Product
- `name`: Product name (CharField)
- `sku`: Stock Keeping Unit (CharField, unique)
- `price`: Product price (DecimalField)
- `inventory_quantity`: Current stock level (PositiveIntegerField)
- `description`: Product description (TextField)
- `shopify_id`: Shopify product ID (CharField)
- `created_at`: Creation timestamp (DateTimeField)
- `updated_at`: Last update timestamp (DateTimeField)
- `last_inventory_update`: Last inventory update (DateTimeField)

### ProductDiscount
- `product`: Related product (ForeignKey)
- `name`: Discount name (CharField)
- `discount_percent`: Discount percentage (DecimalField)
- `active`: Whether discount is active (BooleanField)
- `start_date`: Discount start date (DateTimeField)
- `end_date`: Discount end date (DateTimeField, optional)

### ProductInventoryLog
- `product`: Related product (ForeignKey)
- `previous_quantity`: Previous inventory level (PositiveIntegerField)
- `new_quantity`: New inventory level (PositiveIntegerField)
- `change`: Quantity change (IntegerField)
- `change_type`: Type of change (CharField: manual, webhook, import)
- `timestamp`: Change timestamp (DateTimeField)
- `notes`: Additional notes (TextField)

## 🔧 Docker Commands

### Service Management
```bash
# Start all services
docker-compose up -d

# Stop all services
docker-compose down

# View logs
docker-compose logs web
docker-compose logs celery
docker-compose logs celery-beat

# Restart specific service
docker-compose restart web
docker-compose restart celery

# Check service status
docker-compose ps
```

### Database Operations
```bash
# Run migrations
docker-compose exec web python manage.py migrate

# Create superuser
docker-compose exec web python manage.py createsuperuser

# Create test data
docker-compose exec web python manage.py create_test_data

# Access Django shell
docker-compose exec web python manage.py shell

# Check database connection
docker-compose exec web python manage.py dbshell
```

### Celery Operations
```bash
# Check Celery worker status
docker-compose exec web celery -A shop_integration inspect active

# Monitor Celery tasks
docker-compose exec web celery -A shop_integration monitor

# Purge Celery queue
docker-compose exec web celery -A shop_integration purge
```

## 🧪 Testing

### Run Tests
```bash
# Using Docker
docker-compose exec web python manage.py test

# Local development
python manage.py test
```

### Run with Coverage
```bash
# Install coverage
pip install coverage

# Run tests with coverage
coverage run --source='.' manage.py test
coverage report
coverage html  # Generate HTML report
```

## 🔒 Security

### Authentication & Permissions
- **IsAuthenticated**: Required for all API endpoints
- **IsInProductManagerGroup**: Required for product management
- **IsAdminUser**: Required for admin-only operations

### Webhook Security
- HMAC signature verification for Shopify webhooks
- CSRF protection disabled for webhook endpoints
- Authentication bypassed for webhook endpoints

## 📊 Background Tasks

### Scheduled Tasks
- **Nightly Inventory Update**: Runs at 2:00 AM daily
- **Inventory Report Generation**: Automated reporting
- **Data Import Processing**: CSV import handling

### Manual Tasks
- `products.tasks.generate_inventory_report`
- `products.tasks.import_products_from_csv`
- `products.tasks.nightly_inventory_update`
- `products.tasks.validate_and_update_inventory`

## 🚨 Troubleshooting

### Common Issues

#### 1. Redis Connection Error
```bash
# Check if Redis is running
docker ps | grep redis

# Restart Redis
docker-compose restart redis
```

#### 2. Database Connection Error
```bash
# Check database status
docker-compose exec db pg_isready

# Restart database
docker-compose restart db
```

#### 3. Celery Worker Not Starting
```bash
# Check Celery logs
docker-compose logs celery

# Restart Celery services
docker-compose restart celery celery-beat
```

#### 4. Migration Issues
```bash
# Reset migrations (WARNING: This will delete data)
docker-compose exec web python manage.py migrate --fake-initial

# Show migration status
docker-compose exec web python manage.py showmigrations
```

#### 5. Port Conflicts
```bash
# Check if ports are in use
netstat -tulpn | grep :8000
netstat -tulpn | grep :6379

# Change ports in docker-compose.yml if needed
```

### Performance Optimization

#### Database Indexes
- SKU field indexed for fast lookups
- Price and inventory fields indexed for filtering
- Updated timestamp indexed for sorting

#### Caching
- Redis used for Celery result backend
- Django cache configured for embeddings
- Query result caching for expensive operations

## 📈 Monitoring

### Health Checks
```bash
# Check application health
curl http://localhost:8000/admin/

# Check API health
curl http://localhost:8000/api/v1/products/
```

### Logs
```bash
# View application logs
docker-compose logs -f web

# View Celery logs
docker-compose logs -f celery

# View database logs
docker-compose logs -f db
```

## 🤝 Contributing

### Development Workflow
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Run the test suite
6. Submit a pull request

### Code Style
- Follow PEP 8 for Python code
- Use meaningful variable and function names
- Add docstrings for all functions and classes
- Include type hints where appropriate

## 👥 Leadership and Collaboration

### Code Review Checklist for Junior Developers

#### API Endpoint Design and Documentation
- [ ] **RESTful Conventions**: Follow REST principles with appropriate HTTP methods (GET, POST, PUT, DELETE)
- [ ] **Status Codes**: Use correct HTTP status codes (200, 201, 400, 404, 500, etc.)
- [ ] **Input Validation**: Implement proper request validation and error handling
- [ ] **Documentation**: Add comprehensive docstrings and comments for all endpoints
- [ ] **Response Format**: Ensure consistent JSON response structure
- [ ] **Error Messages**: Provide clear, user-friendly error messages
- [ ] **API Versioning**: Use proper versioning strategy (e.g., `/api/v1/`)
- [ ] **Rate Limiting**: Implement appropriate rate limiting for public endpoints

#### Database Query Optimization
- [ ] **Select Related**: Use `select_related()` for ForeignKey relationships
- [ ] **Prefetch Related**: Use `prefetch_related()` for ManyToMany relationships
- [ ] **Database Indexes**: Create indexes for frequently queried fields
- [ ] **N+1 Queries**: Avoid N+1 query problems with proper prefetching
- [ ] **Query Optimization**: Use Django ORM features like `F()` expressions and aggregations
- [ ] **Transaction Management**: Implement proper transaction handling for data integrity
- [ ] **Query Analysis**: Use `django-debug-toolbar` to analyze query performance
- [ ] **Bulk Operations**: Use `bulk_create()` and `bulk_update()` for multiple records

#### Django Best Practices
- [ ] **Fat Models, Thin Views**: Keep business logic in models, not views
- [ ] **Class-Based Views**: Use appropriate CBVs (ListCreateAPIView, RetrieveUpdateDestroyAPIView)
- [ ] **Django Forms**: Use Django forms for input validation when appropriate
- [ ] **Third-Party Packages**: Evaluate and use established packages (DRF, django-filter, etc.)
- [ ] **App Organization**: Structure apps with clear responsibilities and separation of concerns
- [ ] **Settings Management**: Use environment variables and separate settings files
- [ ] **Middleware Usage**: Leverage Django middleware for cross-cutting concerns
- [ ] **Custom Managers**: Create custom model managers for complex queries

#### Security Considerations
- [ ] **Authentication**: Implement proper authentication (Basic, Session, Token)
- [ ] **Authorization**: Use appropriate permission classes
- [ ] **CSRF Protection**: Enable CSRF protection for state-changing operations
- [ ] **Input Sanitization**: Sanitize all user inputs
- [ ] **SQL Injection**: Use Django ORM to prevent SQL injection
- [ ] **XSS Protection**: Escape user-generated content
- [ ] **Secrets Management**: Never hardcode secrets, use environment variables
- [ ] **Dependency Updates**: Keep dependencies updated for security patches

### Junior Developer Onboarding Plan

#### Week 1: Project Introduction and Setup
**Day 1-2: Environment Setup**
- Install Docker and Docker Compose
- Clone the repository and run the application
- Set up local development environment
- Familiarize with project structure and architecture

**Day 3-4: Django Fundamentals**
- Review Django basics (models, views, URLs, templates)
- Understand Django REST Framework concepts
- Study the existing codebase and documentation
- Complete Django tutorial if needed

**Day 5: Project Walkthrough**
- Code review session with senior developer
- Understanding of the business domain (e-commerce, Shopify integration)
- Overview of API endpoints and data models
- Introduction to Celery and background tasks

**Assignment**: Create a simple API endpoint following project conventions

#### Week 2: Feature Development and Testing
**Day 1-2: Testing Practices**
- Learn about Django testing framework
- Write unit tests for existing functionality
- Understand test-driven development (TDD)
- Practice writing tests for new features

**Day 3-4: Feature Implementation**
- Work on a small feature with guidance
- Implement proper error handling
- Add comprehensive tests
- Follow code review process

**Day 5: Code Review and Feedback**
- Present completed feature to team
- Receive feedback and iterate
- Learn about code review best practices
- Understand Git workflow and branching strategy

**Assignment**: Implement a new API endpoint with full test coverage

#### Week 3: Advanced Concepts and Integration
**Day 1-2: Database and Performance**
- Learn about database optimization
- Understand query performance and indexing
- Practice with Django ORM advanced features
- Introduction to database migrations

**Day 3-4: Background Tasks and Celery**
- Understand asynchronous processing
- Learn about Celery task implementation
- Practice creating and monitoring background tasks
- Introduction to message queues and Redis

**Day 5: API Design and Documentation**
- Learn RESTful API design principles
- Practice API documentation
- Understand authentication and authorization
- Introduction to API testing tools

**Assignment**: Create a background task and corresponding API endpoint

#### Week 4: Production Readiness and Deployment
**Day 1-2: Docker and Containerization**
- Understand Docker concepts and benefits
- Learn about Docker Compose for multi-service applications
- Practice building and running containers
- Introduction to container orchestration

**Day 3-4: Monitoring and Debugging**
- Learn about application monitoring
- Understand logging best practices
- Practice debugging techniques
- Introduction to performance profiling

**Day 5: Deployment and CI/CD**
- Overview of deployment strategies
- Introduction to CI/CD pipelines
- Understanding of production considerations
- Security best practices review

**Assignment**: Deploy a feature to staging environment

#### Ongoing Support and Mentoring
- **Weekly Code Reviews**: Regular feedback sessions
- **Pair Programming**: Collaborative coding sessions
- **Knowledge Sharing**: Weekly tech talks and discussions
- **Mentorship**: One-on-one sessions with senior developers
- **Documentation**: Contributing to project documentation
- **Community**: Participation in team meetings and discussions

#### Success Metrics
- **Code Quality**: Passing all code reviews
- **Test Coverage**: Maintaining >80% test coverage
- **Documentation**: Contributing to API documentation
- **Collaboration**: Active participation in team discussions
- **Learning**: Completing assigned tasks and learning objectives

## 🆘 Support

For support and questions:
- Create an issue in the repository
- Check the troubleshooting section above
- Review the Django and DRF documentation

---

**Note**: This application is designed for development and testing purposes. For production deployment, ensure proper security configurations, environment variables, and monitoring are in place. 