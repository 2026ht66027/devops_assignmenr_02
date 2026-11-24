pipeline {
    agent any

    environment {
        IMAGE_NAME = 'aceest-fitness'
        K8S_NAMESPACE = 'aceest'
    }

    options {
        timestamps()
        disableConcurrentBuilds()
        buildDiscarder(logRotator(numToKeepStr: '15'))
    }

    stages {
        stage('Checkout') {
            steps {
                checkout scm
                sh 'git rev-parse --short HEAD'
            }
        }

        stage('Install dependencies and test') {
            steps {
                sh '''
                    python3 -m venv .venv
                    . .venv/bin/activate
                    pip install --upgrade pip
                    pip install -r requirements.txt
                    pytest -v --junitxml=reports/pytest.xml
                '''
            }
            post {
                always {
                    junit allowEmptyResults: true, testResults: 'reports/pytest.xml'
                }
            }
        }

        stage('SonarQube analysis') {
            steps {
                withSonarQubeEnv('SonarQube') {
                    sh 'sonar-scanner'
                }
            }
        }

        stage('Quality gate') {
            steps {
                timeout(time: 5, unit: 'MINUTES') {
                    waitForQualityGate abortPipeline: true
                }
            }
        }

        stage('Build container image') {
            when { branch 'main' }
            steps {
                withCredentials([usernamePassword(
                    credentialsId: 'dockerhub-credentials',
                    usernameVariable: 'DOCKER_USER',
                    passwordVariable: 'DOCKER_PASS'
                )]) {
                    sh '''
                        IMAGE_TAG=$(git rev-parse --short HEAD)
                        docker build --pull \\
                          -t "$DOCKER_USER/aceest-fitness:$IMAGE_TAG" \\
                          -t "$DOCKER_USER/aceest-fitness:latest" .
                    '''
                }
            }
        }

        stage('Publish image') {
            when { branch 'main' }
            steps {
                withCredentials([usernamePassword(
                    credentialsId: 'dockerhub-credentials',
                    usernameVariable: 'DOCKER_USER',
                    passwordVariable: 'DOCKER_PASS'
                )]) {
                    sh '''
                        echo "$DOCKER_PASS" | docker login -u "$DOCKER_USER" --password-stdin
                        IMAGE_TAG=$(git rev-parse --short HEAD)
                        docker push "$DOCKER_USER/aceest-fitness:$IMAGE_TAG"
                        docker push "$DOCKER_USER/aceest-fitness:latest"
                        docker logout
                    '''
                }
            }
        }

        stage('Deploy rolling update') {
            when { branch 'main' }
            steps {
                withCredentials([usernamePassword(
                    credentialsId: 'dockerhub-credentials',
                    usernameVariable: 'DOCKER_USER',
                    passwordVariable: 'DOCKER_PASS'
                )]) {
                    sh '''
                        IMAGE_TAG=$(git rev-parse --short HEAD)
                        kubectl apply -f k8s/namespace.yaml
                        kubectl apply -f k8s/rolling/
                        kubectl set image deployment/aceest-fitness \\
                          aceest-fitness="$DOCKER_USER/aceest-fitness:$IMAGE_TAG" \\
                          --namespace "$K8S_NAMESPACE"
                        kubectl rollout status deployment/aceest-fitness \\
                          --namespace "$K8S_NAMESPACE" --timeout=180s
                    '''
                }
            }
        }
    }

    post {
        failure {
            echo 'The pipeline failed. If a rollout started, inspect it and run: kubectl rollout undo deployment/aceest-fitness -n aceest'
        }
        always {
            cleanWs deleteDirs: true, notFailBuild: true
        }
    }
}
