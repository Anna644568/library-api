// Декларативный pipeline для проекта «Библиотека» (ЛР2: контейнеризация).
// Jenkins работает на Windows, шаги выполняются через bat, Docker — Docker Desktop.
//
// Все ветки (CI):   сборка тестового образа -> автотесты в контейнере -> сборка образов api и web
// dev  (staging):    + развёртывание контейнеров на http://localhost:8082 и smoke-тест
// main (production): + развёртывание контейнеров на http://localhost:8081 и smoke-тест

pipeline {
    agent any

    triggers {
        // запуск по событию push из GitHub (вебхук)
        githubPush()
    }

    options {
        timestamps()
        disableConcurrentBuilds()
        buildDiscarder(logRotator(numToKeepStr: '15'))
    }

    environment {
        DOCKER_BUILDKIT = '1'
        // Docker Desktop установлен в профиль пользователя User, а служба Jenkins работает
        // от системной учётной записи и не видит его настроек. Поэтому:
        //  - добавляем папку с docker.exe в начало PATH;
        //  - указываем отдельную папку настроек Docker для Jenkins (там config.json
        //    с путём к плагинам docker compose и docker buildx)
        PATH = "C:\\Users\\User\\AppData\\Local\\Programs\\DockerDesktop\\resources\\bin;${env.PATH}"
        DOCKER_CONFIG = 'C:\\ProgramData\\Jenkins\\docker-config'
    }

    stages {
        stage('Checkout') {
            steps {
                checkout scm
                script {
                    env.SHORT_COMMIT = bat(returnStdout: true, script: '@git rev-parse --short HEAD').trim()
                    // тег образов: <ветка>-<номер сборки>, например main-5, feature-docker-2
                    env.IMAGE_TAG  = "${env.BRANCH_NAME.replace('/', '-')}-${env.BUILD_NUMBER}"
                    env.APP_BUILD  = env.BUILD_NUMBER
                    env.APP_COMMIT = env.SHORT_COMMIT
                    // в какое окружение разворачивать
                    if (env.BRANCH_NAME == 'main') {
                        env.APP_ENV = 'production'; env.STACK = 'library-prod';    env.WEB_PORT = '8081'
                    } else if (env.BRANCH_NAME == 'dev') {
                        env.APP_ENV = 'staging';    env.STACK = 'library-staging'; env.WEB_PORT = '8082'
                    } else {
                        env.APP_ENV = 'none'
                    }
                }
                echo "Ветка ${env.BRANCH_NAME}, коммит ${env.SHORT_COMMIT}, тег образов ${env.IMAGE_TAG}, окружение ${env.APP_ENV}"
            }
        }

        stage('Docker info') {
            steps {
                bat 'docker version'
                bat 'docker compose version'
            }
        }

        stage('Build test image') {
            steps {
                // этап test из Dockerfile: код приложения + pytest + тесты;
                // --load: готовый образ обязательно загружается в Docker (нужно, если
                // сборщик BuildKit работает в отдельном контейнере)
                bat 'docker build --load --target test -t library-api-test:%IMAGE_TAG% .'
            }
        }

        stage('Unit tests') {
            steps {
                // тесты выполняются ВНУТРИ контейнера; отчёт junit.xml копируется из контейнера в workspace
                bat '''
                    docker rm -f lib-test-%IMAGE_TAG% >nul 2>&1
                    docker run --name lib-test-%IMAGE_TAG% library-api-test:%IMAGE_TAG%
                    set RC=%ERRORLEVEL%
                    if not exist reports mkdir reports
                    docker cp lib-test-%IMAGE_TAG%:/app/reports/junit.xml reports\\junit.xml
                    docker rm lib-test-%IMAGE_TAG% >nul
                    exit /b %RC%
                '''
            }
        }

        stage('Build images') {
            steps {
                // образы library-api:<тег> и library-web:<тег> по описанию из docker-compose.yml
                bat 'docker compose build'
                bat 'docker image ls --filter "reference=library-*"'
            }
        }
        stage('Push to Docker Hub') {
            steps {
                // 1. Переименовываем локальные образы под аккаунт Docker Hub
                bat "docker tag library-api:%IMAGE_TAG% anna234567890/library-api:%IMAGE_TAG%"
                bat "docker tag library-web:%IMAGE_TAG% anna234567890/library-web:%IMAGE_TAG%"
                
                // 2. Логинимся и пушим (Jenkins берёт логин/токен из Credentials)
                withDockerRegistry(registry: [credentialsId: 'docker-hub-credentials'], toolName: 'docker')  {
                    bat "docker push anna234567890/library-api:%IMAGE_TAG%"
                    bat "docker push anna234567890/library-web:%IMAGE_TAG%"
                }
            }
        }
        stage('Deploy') {
            when { anyOf { branch 'main'; branch 'dev' } }
            steps {
                // пересоздаются только контейнеры, том library-data с базой сохраняется
                bat 'docker compose -p %STACK% up -d --no-build --remove-orphans --wait --wait-timeout 120'
                bat 'docker compose -p %STACK% ps'
            }
        }

        stage('Smoke test') {
            when { anyOf { branch 'main'; branch 'dev' } }
            steps {
                // 1) изнутри Docker-сети: тестовый контейнер -> nginx -> api -> БД
                bat 'docker run --rm --network %STACK%_backend library-api-test:%IMAGE_TAG% python e2e/smoke.py http://web'
                // 2) снаружи, как пользователь: через опубликованный порт
                bat 'curl -fsS http://localhost:%WEB_PORT%/api/info'
            }
        }
    }

    post {
        always {
            junit allowEmptyResults: true, testResults: 'reports/junit.xml'
            // тестовый образ больше не нужен; удаляем и «висячие» слои старых сборок
            bat(returnStatus: true, script: 'docker image rm library-api-test:%IMAGE_TAG% >nul 2>&1')
            bat(returnStatus: true, script: 'docker image prune -f')
        }
        success {
            script {
                if (env.APP_ENV != 'none') {
                    echo "Сборка ${env.BRANCH_NAME} #${env.BUILD_NUMBER} развёрнута (${env.APP_ENV}): http://localhost:${env.WEB_PORT}"
                } else {
                    echo "Сборка ${env.BRANCH_NAME} #${env.BUILD_NUMBER}: тесты пройдены, образы собраны"
                }
            }
        }
        failure {
            echo "Сборка ${env.BRANCH_NAME} #${env.BUILD_NUMBER} упала — смотреть журнал этапа и отчёт тестов"
        }
        cleanup {
            cleanWs()
        }
    }
}
