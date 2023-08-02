pipeline{
    agent any
    environment{
        PROJECT_NAME = "chaoshen-toolbox"
    }
    stages{
        stage('Build'){
            steps{
                sh 'python setup.py build'
            }
        }
        stage('Test'){
            steps{
                echo 'Testing the app'
            }
        }
        stage('msg'){
            steps{
                wxwork(
                    robot: 'jenkins',
                    type: 'text',
                    text: [
                        '${JOB_NAME}-${BUILD_NUMBER} 构建成功',
                        '${PROJECT_NAME} 构建成功',
                    ]
                )
            }
        }
    }
}