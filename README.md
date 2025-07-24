# Shopify Integration Backend

A simplified backend system using Python, Django, and Django REST Framework that integrates with Shopify for product management.

## Features

- REST API endpoints for managing products (CRUD operations)
- Advanced filtering and searching capabilities
- Shopify webhook integration for inventory updates
- Customized Django admin interface
- Background tasks with Celery for nightly operations
- AI-powered smart product search using spaCy/Sentence Transformers
- Automated inventory insights

## Tech Stack

- Python 3.11
- Django 4.2
- Django REST Framework
- PostgreSQL
- Redis
- Celery
- spaCy / Sentence Transformers
- Docker & Docker Compose

## Setup Instructions

### Using Docker (Recommended)

1. Clone this repository:
   ```
   git clone <repository-url>
   cd shopify-integration
   ```

2. Start the Docker containers:
   ```
   docker-compose up -d
   ```

3. Run migrations:
   ```
   docker-compose exec web python manage.py migrate
   ```

4. Create a superuser:
   ```
   docker-compose exec web python manage.py createsuperuser
   ```

5. Load initial data (optional):
   ```
   docker-compose exec web python manage.py loaddata initial_data
   ```

6. Access the application:
   - API: http://localhost:8000/api/v1/
   - Admin: http://localhost:8000/admin/

### Local Development Setup

1. Create a virtual environment:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Set environment variables (create a .env file):
   ```
   DEBUG=True
   USE_SQLITE=True
   ```

4. Apply migrations:
   ```
   python manage.py migrate
   ```

5. Create a superuser:
   ```
   python manage.py createsuperuser
   ```

6. Run the development server:
   ```
   python manage.py runserver
   ```

## API Endpoints

- **Products**: `/api/v1/products/`
  - GET: List all products (with filtering)
  - POST: Create a new product

- **Product Detail**: `/api/v1/products/{id}/`
  - GET: Retrieve product details
  - PUT/PATCH: Update a product
  - DELETE: Delete a product

- **Product Search**: `/api/v1/products/search/?q=query`
  - GET: Search products with semantic ranking

- **Product Insights**: `/api/v1/products/insights/`
  - GET: Get inventory insights and trending products

- **Shopify Webhook**: `/api/v1/webhooks/shopify/inventory/`
  - POST: Receive inventory updates from Shopify

- **Product Discounts**: `/api/v1/discounts/`
  - CRUD operations for product discounts

## Authentication

API endpoints require authentication. The following methods are supported:
- Basic Authentication
- Session Authentication

## Testing

Run tests with:
```
python manage.py test
```

For coverage report:
```
coverage run --source='.' manage.py test
coverage report
```

## Junior Developer Code Review Checklist

### API Endpoint Design
- [ ] Follow RESTful conventions
- [ ] Use appropriate HTTP methods and status codes
- [ ] Implement proper input validation and error handling
- [ ] Add appropriate permissions
- [ ] Document all endpoints with docstrings and comments

### Database Queries
- [ ] Use select_related() and prefetch_related() for related objects
- [ ] Create appropriate indexes for frequently queried fields
- [ ] Avoid N+1 query problems
- [ ] Use Django ORM features correctly (F expressions, aggregations)
- [ ] Implement transaction management for data integrity

### Django Best Practices
- [ ] Follow the "fat models, thin views" principle
- [ ] Use class-based views appropriately
- [ ] Leverage Django's built-in functionality before custom solutions
- [ ] Organize code in reusable apps with clear responsibilities
- [ ] Use Django forms for input validation

### Security Considerations
- [ ] Protect against CSRF, XSS, and SQL injection
- [ ] Implement proper authentication and authorization
- [ ] Never expose sensitive information in responses
- [ ] Rate limit API endpoints
- [ ] Audit AI-generated code for security risks (e.g., secrets in prompts)

## Onboarding Plan for Junior Developers

### Week 1: Project Introduction and Setup
- Development environment setup
- Code walkthrough and architecture overview
- Introduction to Django and DRF concepts
- Assignment of simple bugfixes or small features

### Week 2: Feature Development
- Implement a small feature with guidance
- Learn about testing and writing unit tests
- Code review process introduction
- Project management tools and workflow

### Week 3: Integration and Deployment
- Understanding Docker and containerization
- CI/CD pipeline overview
- Database management and migrations
- Deployment process

### Week 4: Advanced Topics
- Celery tasks and async processing
- API design principles
- Performance optimization techniques
- Security best practices 