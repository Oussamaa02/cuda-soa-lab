pipeline {
    agent any

    environment {
        REPO = "https://github.com/Oussamaa02/cuda-soa-lab.git"
        IMAGE = "gpu-service:${env.BUILD_NUMBER}"
        STUDENT_PORT = "8127"
    }

    stages {

        stage('Checkout') {
            steps {
                git url: env.REPO
            }
        }

        stage('List workspace') {
            steps {
                // Debug: show files and Dockerfile contents on the agent
                sh '''
                    echo "--- ls -la workspace ---"
                    ls -la
                    echo "--- stat Dockerfile ---"
                    if [ -f Dockerfile ]; then stat -c "%n %s bytes (%a)" Dockerfile || true; else echo "Dockerfile not found"; fi
                    echo "--- head of Dockerfile ---"
                    if [ -f Dockerfile ]; then sed -n '1,200p' Dockerfile || true; else true; fi
                '''
            }
        }

        stage('Build Image') {
            steps {
                sh """
                    docker build -t ${IMAGE} --build-arg STUDENT_PORT=${STUDENT_PORT} .
                """
            }
        }

        stage('Stop Old Container') {
            steps {
                sh """
                    docker rm -f gpu_service || true
                """
            }
        }

        stage('Run New Container') {
            steps {
                sh """
                    docker run -d --gpus all \
                        --name gpu_service \
                        -p ${STUDENT_PORT}:${STUDENT_PORT} \
                        ${IMAGE}
                """
            }
        }

    }
}
