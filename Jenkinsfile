pipeline {
    agent any

    environment {
        DOCKER_IMAGE = "jstaguan/tj27_edemoapp:latest"
        REGISTRY_CREDENTIALS = 'dockerhub-creds-id'  // Jenkins credential ID
        KUBECONFIG_CREDENTIALS = 'kubeconfig-id'     // Optional: if you're using kubeconfig
    }

    stages {
        stage('Checkout') {
            steps {
                git url: 'https://github.com/tahgoi/eDemoApp.git', branch: 'main'
            }
        }

        stage('Build Docker Image') {
            steps {
                script {
                    docker.build("${DOCKER_IMAGE}")
                }
            }
        }

        stage('Push Docker Image') {
            steps {
                script {
                    docker.withRegistry('', REGISTRY_CREDENTIALS) {
                        docker.image("${DOCKER_IMAGE}").push()
                    }
                }
            }
        }

        stage('Deploy to Kubernetes') {
            steps {
                withCredentials([file(credentialsId: KUBECONFIG_CREDENTIALS, variable: 'KUBECONFIG')]) {
                    sh """
                      kubectl apply -f k8s/deployment.yaml
                    """
                }
            }
        }
    }
}
