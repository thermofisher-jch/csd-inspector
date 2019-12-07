pipeline {
    agent {
        label "docker-host"
    }

    stages {
        stage('Build') {
            steps {
                sh "python3 setup_dev_environment.py"
                sh "docker-compose build"
            }
        }
        stage('Test') {
            steps {
                sh "docker-compose run django python manage.py test --noinput --parallel"
            }
        }
    }
}
