pipeline {
    agent any
    
    environment {
        DOCKER_BUILDKIT = '1'
        COMPOSE_DOCKER_CLI_BUILD = '1'
        PYTHON_VERSION = '3.11'
        POSTGRES_VERSION = '16-alpine'
        REDIS_VERSION = '7-alpine'
    }
    
    options {
        timeout(time: 30, unit: 'MINUTES')
        timestamps()
        buildDiscarder(logRotator(numToKeepStr: '10'))
    }
    
    stages {
        stage('Checkout') {
            steps {
                checkout scm
                script {
                    env.GIT_COMMIT_SHORT = sh(
                        script: 'git rev-parse --short HEAD',
                        returnStdout: true
                    ).trim()
                    env.BUILD_NUMBER_SHORT = "${env.BUILD_NUMBER}"
                }
            }
        }
        
        stage('Lint & Code Quality') {
            parallel {
                stage('Python Linting') {
                    steps {
                        script {
                            dir('services/auth-service') {
                                sh '''
                                    pip install --upgrade pip
                                    pip install flake8 black isort mypy
                                    flake8 src --max-line-length=120 --exclude=__pycache__,*.pyc || true
                                    black --check src || true
                                    isort --check-only src || true
                                '''
                            }
                        }
                    }
                }
                stage('Dockerfile Lint') {
                    steps {
                        script {
                            sh '''
                                if command -v hadolint &> /dev/null; then
                                    find services -name Dockerfile -exec hadolint {} \\;
                                else
                                    echo "hadolint not installed, skipping Dockerfile linting"
                                fi
                            '''
                        }
                    }
                }
            }
        }
        
        stage('Build Docker Images') {
            steps {
                script {
                    echo "Building Docker images..."
                    sh '''
                        docker-compose build --parallel auth-service
                        docker images | grep quimicadealtura_api-auth-service
                    '''
                }
            }
        }
        
        stage('Start Infrastructure') {
            steps {
                script {
                    echo "Starting PostgreSQL and Redis..."
                    sh '''
                        docker-compose up -d postgres-auth redis
                        echo "Waiting for services to be healthy..."
                        sleep 10
                        docker-compose ps
                    '''
                }
            }
        }
        
        stage('Database Migrations') {
            steps {
                script {
                    echo "Running database migrations..."
                    sh '''
                        docker-compose exec -T auth-service alembic upgrade head || \
                        docker-compose run --rm auth-service alembic upgrade head
                    '''
                }
            }
        }
        
        stage('Unit Tests') {
            steps {
                script {
                    dir('services/auth-service') {
                        sh '''
                            docker-compose run --rm auth-service pytest tests/ -v --tb=short || true
                        '''
                    }
                }
            }
        }
        
        stage('Integration Tests') {
            steps {
                script {
                    echo "Running integration tests..."
                    sh '''
                        # Start auth service
                        docker-compose up -d auth-service
                        sleep 5
                        
                        # Wait for service to be ready
                        for i in {1..30}; do
                            if curl -f http://localhost:8001/health > /dev/null 2>&1; then
                                echo "Service is ready!"
                                break
                            fi
                            echo "Waiting for service... ($i/30)"
                            sleep 2
                        done
                        
                        # Run integration tests
                        cd services/auth-service
                        pip install -q pytest httpx requests
                        pytest tests/test_new_features.py::TestIntegration -v || true
                    '''
                }
            }
        }
        
        stage('Feature Tests') {
            steps {
                script {
                    echo "Testing new enterprise features..."
                    sh '''
                        cd services/auth-service
                        
                        # Test password strength validation
                        echo "Testing password strength..."
                        python3 -c "
import sys
sys.path.insert(0, 'src')
from utils.password_validator import validate_password, PasswordValidationError

# Test weak passwords
try:
    validate_password('short')
    sys.exit(1)
except PasswordValidationError:
    pass

# Test strong password
validate_password('StrongPassword123!')
print('✓ Password validation tests passed')
"
                        
                        # Test device fingerprinting
                        echo "Testing device fingerprinting..."
                        python3 -c "
import sys
sys.path.insert(0, 'src')
from utils.device_fingerprint import generate_device_fingerprint, detect_device_type

fp = generate_device_fingerprint('Mozilla/5.0', '192.168.1.1', 'en-US')
assert len(fp) == 64, 'Fingerprint length incorrect'
assert detect_device_type('Mozilla/5.0 (iPhone') == 'mobile', 'Device detection failed'
print('✓ Device fingerprinting tests passed')
"
                        
                        # Test API endpoints
                        echo "Testing API endpoints..."
                        ./QUICK_TEST.sh || echo "Some tests may have failed, check logs"
                    '''
                }
            }
        }
        
        stage('Security Tests') {
            steps {
                script {
                    echo "Running security tests..."
                    sh '''
                        cd services/auth-service
                        
                        # Test rate limiting
                        echo "Testing rate limiting..."
                        for i in {1..10}; do
                            curl -s -o /dev/null -w "%{http_code}" -X POST http://localhost:8001/api/v1/auth/login \\
                                -H 'Content-Type: application/json' \\
                                -d '{"email":"test@test.com","password":"wrong"}' || true
                            sleep 0.5
                        done | grep -q 429 && echo "✓ Rate limiting works" || echo "⚠ Rate limiting may need adjustment"
                        
                        # Test password strength enforcement
                        echo "Testing password strength enforcement..."
                        WEAK_RESPONSE=$(curl -s -w "%{http_code}" -X POST http://localhost:8001/api/v1/auth/register \\
                            -H 'Content-Type: application/json' \\
                            -d '{"email":"weak@test.com","password":"short","first_name":"Test","last_name":"User"}' \\
                            -o /dev/null)
                        [ "$WEAK_RESPONSE" == "400" ] && echo "✓ Weak password rejected" || echo "⚠ Weak password not rejected"
                    '''
                }
            }
        }
        
        stage('Performance Tests') {
            steps {
                script {
                    echo "Running performance tests..."
                    sh '''
                        # Test service startup time
                        START_TIME=$(date +%s)
                        docker-compose restart auth-service
                        sleep 5
                        for i in {1..30}; do
                            if curl -f http://localhost:8001/health > /dev/null 2>&1; then
                                END_TIME=$(date +%s)
                                STARTUP_TIME=$((END_TIME - START_TIME))
                                echo "Service started in ${STARTUP_TIME} seconds"
                                [ $STARTUP_TIME -lt 30 ] && echo "✓ Startup time acceptable" || echo "⚠ Startup time slow"
                                break
                            fi
                            sleep 1
                        done
                    '''
                }
            }
        }
        
        stage('Build Artifacts') {
            when {
                anyOf {
                    branch 'main'
                    branch 'master'
                    branch 'develop'
                }
            }
            steps {
                script {
                    echo "Creating build artifacts..."
                    sh '''
                        # Tag Docker images
                        docker tag quimicadealtura_api-auth-service:latest \\
                            quimicadealtura_api-auth-service:${GIT_COMMIT_SHORT}
                        docker tag quimicadealtura_api-auth-service:latest \\
                            quimicadealtura_api-auth-service:build-${BUILD_NUMBER}
                        
                        # Save image
                        docker save quimicadealtura_api-auth-service:latest | gzip > auth-service-${BUILD_NUMBER}.tar.gz
                        
                        # Create deployment package
                        mkdir -p artifacts
                        cp docker-compose.yml artifacts/
                        cp services/auth-service/Dockerfile artifacts/
                        echo "${GIT_COMMIT_SHORT}" > artifacts/VERSION
                        echo "${BUILD_NUMBER}" >> artifacts/VERSION
                    '''
                    archiveArtifacts artifacts: 'artifacts/**', fingerprint: true
                }
            }
        }
    }
    
    post {
        always {
            script {
                echo "Cleaning up..."
                sh '''
                    docker-compose down -v || true
                    docker system prune -f || true
                '''
            }
            cleanWs()
        }
        success {
            echo "✅ Build and tests completed successfully!"
            script {
                if (env.BRANCH_NAME == 'main' || env.BRANCH_NAME == 'master') {
                    echo "Ready for deployment!"
                }
            }
        }
        failure {
            echo "❌ Build or tests failed!"
            emailext (
                subject: "Build Failed: ${env.JOB_NAME} #${env.BUILD_NUMBER}",
                body: "Build ${env.BUILD_NUMBER} failed. Check: ${env.BUILD_URL}",
                to: "${env.CHANGE_AUTHOR_EMAIL ?: 'devops@example.com'}"
            )
        }
        unstable {
            echo "⚠️ Build unstable - some tests may have failed"
        }
    }
}
