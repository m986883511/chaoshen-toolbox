pipeline{
    agent any
    stages{
        stage('Build'){
            steps{
                python setup.py build
            }
        }
        stage('Test'){
            steps{
                echo 'Testing the app'
            }
        }
        stage('Deploy'){
            steps{
                echo 'Deploying the app'
            }
        }
    }
}