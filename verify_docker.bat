@echo off
echo 🚀 Docker Setup Verification
echo ==================================================

echo.
echo 🔍 Checking Docker Installation...
docker --version
if %errorlevel% neq 0 (
    echo ❌ Docker not found or not running
    pause
    exit /b 1
)

docker-compose --version
if %errorlevel% neq 0 (
    echo ❌ Docker Compose not found
    pause
    exit /b 1
)

echo ✅ Docker and Docker Compose are installed

echo.
echo 🔍 Building and starting containers...
docker-compose build
docker-compose up -d

echo.
echo 🔍 Checking container status...
docker-compose ps

echo.
echo 🔍 Running database migrations...
docker-compose exec -T web python manage.py migrate

echo.
echo 🔍 Creating test data...
docker-compose exec -T web python manage.py create_test_data --count 5

echo.
echo ==================================================
echo 📊 VERIFICATION COMPLETE
echo ==================================================
echo.
echo ✅ If all commands above completed successfully, your Docker setup is working!
echo.
echo 📝 Next Steps:
echo 1. Access the admin interface: http://localhost:8000/admin/
echo 2. Create a superuser: docker-compose exec web python manage.py createsuperuser
echo 3. Test the API: http://localhost:8000/api/v1/products/
echo.
echo 🔧 If you see errors, try:
echo - docker-compose logs web
echo - docker-compose restart
echo.
pause 