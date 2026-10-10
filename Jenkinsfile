// Декларативный pipeline для проекта «Библиотека API» (FastAPI + SQLite).
// Jenkins работает на Windows, поэтому шаги выполняются через bat.
//
// CI  — ветки dev и feature/*: установка зависимостей и автотесты.
// CD  — ветка main: то же самое + упаковка и доставка сборки в папку развёртывания.

pipeline {
    agent any

    triggers {
        // запуск по событию push из GitHub (через webhook)
        githubPush()
    }

    options {
        timestamps()
        disableConcurrentBuilds()
        buildDiscarder(logRotator(numToKeepStr: '15'))
    }

    environment {
        PYTHON     = 'C:\\Users\\User\\miniconda3\\python.exe'
        VENV       = '.venv'
        DEPLOY_DIR = 'C:\\deploy\\library-api'
        PYTHONIOENCODING = 'utf-8'
    }

    stages {
        stage('Checkout') {
            steps {
                checkout scm
                bat 'git log -1 --pretty=format:"%%h %%an: %%s"'
            }
        }

        stage('Setup') {
            steps {
                bat '''
                    "%PYTHON%" -m venv %VENV% || exit /b 1
                    %VENV%\\Scripts\\python.exe -m pip install --upgrade pip || exit /b 1
                    %VENV%\\Scripts\\python.exe -m pip install -r requirements.txt || exit /b 1
                '''
            }
        }

        stage('Test') {
            steps {
                bat '%VENV%\\Scripts\\python.exe -m pytest -v --junitxml=reports\\junit.xml'
            }
        }

        stage('Package') {
            when { branch 'main' }
            steps {
                powershell '''
                    New-Item -ItemType Directory -Force -Path dist | Out-Null
                    Compress-Archive -Force -Path app, requirements.txt, README.md `
                        -DestinationPath "dist\\library-api-$env:BUILD_NUMBER.zip"
                '''
                archiveArtifacts artifacts: 'dist/*.zip', fingerprint: true
            }
        }

        stage('Deliver') {
            when { branch 'main' }
            steps {
                powershell '''
                    New-Item -ItemType Directory -Force -Path $env:DEPLOY_DIR | Out-Null
                    Expand-Archive -Force -Path "dist\\library-api-$env:BUILD_NUMBER.zip" `
                        -DestinationPath $env:DEPLOY_DIR
                    Set-Content -Path "$env:DEPLOY_DIR\\VERSION.txt" `
                        -Value "build $env:BUILD_NUMBER, commit $env:GIT_COMMIT, $(Get-Date)"
                    Write-Host "Сборка $env:BUILD_NUMBER доставлена в $env:DEPLOY_DIR"
                '''
            }
        }
    }

    post {
        always {
            junit allowEmptyResults: true, testResults: 'reports/junit.xml'
        }
        success {
            echo "Сборка ${env.BRANCH_NAME} #${env.BUILD_NUMBER} прошла успешно"
        }
        failure {
            echo "Сборка ${env.BRANCH_NAME} #${env.BUILD_NUMBER} упала — смотреть отчёт тестов"
        }
        cleanup {
            cleanWs()
        }
    }
}
