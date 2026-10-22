// Декларативный pipeline проекта «Библиотека» (ЛР3: микросервисы в Kubernetes).
// Jenkins работает на Windows, шаги — через bat/powershell, Docker и Kubernetes — Docker Desktop.
//
// Все ветки (CI):    тестовые образы трёх сервисов -> модульные тесты в контейнерах -> рабочие образы
// dev  и main:       + отправка образов на Docker Hub с тегом <ветка>-<номер сборки>
// main (CD):         + развёртывание в кластер Kubernetes (namespace library) -> ожидание готовности
//                      -> smoke-тест через http://localhost:30080 -> тег latest на Docker Hub
//                      (если smoke-тест не прошёл — автоматический откат: kubectl rollout undo)
//
// Код ЛР1 и ЛР2 сохранён в метках (tags) lr1 и lr2 репозитория.

SERVICES = ['catalog', 'readers', 'loans']
DEPLOYMENTS = ['catalog', 'readers', 'loans', 'web']

pipeline {
    agent any

    triggers {
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
        // от системной учётной записи: явно указываем путь к docker.exe/kubectl.exe
        // и отдельные каталоги настроек Docker и Kubernetes для Jenkins
        PATH = "C:\\Users\\User\\AppData\\Local\\Programs\\DockerDesktop\\resources\\bin;${env.PATH}"
        DOCKER_CONFIG = 'C:\\ProgramData\\Jenkins\\docker-config'
        KUBECONFIG = 'C:\\ProgramData\\Jenkins\\kube\\config'
        DOCKERHUB_USER = 'anna234567890'
        K8S_NAMESPACE = 'library'
        APP_URL = 'http://localhost:30080'
        PYTHON = 'C:\\Users\\User\\miniconda3\\python.exe'
        PYTHONIOENCODING = 'utf-8'
    }

    stages {
        stage('Checkout') {
            steps {
                checkout scm
                script {
                    env.SHORT_COMMIT = bat(returnStdout: true, script: '@git rev-parse --short HEAD').trim()
                    env.IMAGE_TAG = "${env.BRANCH_NAME.replace('/', '-')}-${env.BUILD_NUMBER}"
                }
                echo "Ветка ${env.BRANCH_NAME}, коммит ${env.SHORT_COMMIT}, тег образов ${env.IMAGE_TAG}"
            }
        }

        stage('Tools') {
            steps {
                bat 'docker version --format "Docker {{.Server.Version}}"'
                bat 'kubectl version --client'
            }
        }

        stage('Unit tests') {
            steps {
                script {
                    // каждый микросервис тестируется отдельно, в своём тестовом образе
                    for (s in SERVICES) {
                        bat "docker build --load --target test -t library-${s}-test:%IMAGE_TAG% -f services\\${s}\\Dockerfile services"
                        bat """
                            docker rm -f lib-test-${s} >nul 2>&1
                            docker run --name lib-test-${s} library-${s}-test:%IMAGE_TAG%
                            set RC=%ERRORLEVEL%
                            if not exist reports mkdir reports
                            docker cp lib-test-${s}:/app/reports/junit.xml reports\\${s}.xml
                            docker rm lib-test-${s} >nul
                            exit /b %RC%
                        """
                    }
                }
            }
        }

        stage('Build images') {
            steps {
                script {
                    for (s in SERVICES) {
                        bat "docker build --load --target runtime -t %DOCKERHUB_USER%/library-${s}:%IMAGE_TAG% -f services\\${s}\\Dockerfile services"
                    }
                }
                bat 'docker build --load -t %DOCKERHUB_USER%/library-web:%IMAGE_TAG% web'
                bat 'docker image ls --filter "reference=%DOCKERHUB_USER%/library-*:%IMAGE_TAG%"'
            }
        }

        stage('Push to Docker Hub') {
            when { anyOf { branch 'main'; branch 'dev' } }
            steps {
                // логин и токен Docker Hub — в Jenkins Credentials (ID docker-hub-credentials)
                withCredentials([usernamePassword(credentialsId: 'docker-hub-credentials',
                                                  usernameVariable: 'DH_USER',
                                                  passwordVariable: 'DH_TOKEN')]) {
                    bat 'echo %DH_TOKEN%| docker login -u %DH_USER% --password-stdin'
                    script {
                        for (s in DEPLOYMENTS) {
                            bat "docker push %DOCKERHUB_USER%/library-${s}:%IMAGE_TAG%"
                        }
                    }
                }
            }
            post {
                always { bat(returnStatus: true, script: 'docker logout') }
            }
        }

        stage('Deploy to Kubernetes') {
            when { branch 'main' }
            steps {
                bat 'kubectl get nodes -o wide'
                // в манифестах k8s/ тег :latest заменяется на тег этой сборки,
                // подставляются номер сборки и коммит
                powershell '''
                    $files = Get-ChildItem k8s -Filter *.yaml | Sort-Object Name
                    $text = ($files | ForEach-Object { [IO.File]::ReadAllText($_.FullName) }) -join "`n---`n"
                    $text = $text.Replace(':latest', ":$env:IMAGE_TAG")
                    $text = $text.Replace('APP_BUILD: "local"', "APP_BUILD: `"$env:BUILD_NUMBER`"")
                    $text = $text.Replace('APP_COMMIT: "local"', "APP_COMMIT: `"$env:SHORT_COMMIT`"")
                    [IO.File]::WriteAllText((Join-Path $env:WORKSPACE 'k8s-rendered.yaml'), $text)
                    Write-Host "Подготовлены манифесты: $($files.Name -join ', ')"
                '''
                bat 'kubectl apply -f k8s-rendered.yaml'
                bat 'kubectl -n %K8S_NAMESPACE% rollout status statefulset/postgres --timeout=180s'
                script {
                    for (d in DEPLOYMENTS) {
                        bat "kubectl -n %K8S_NAMESPACE% rollout status deployment/${d} --timeout=240s"
                    }
                }
                bat 'kubectl -n %K8S_NAMESPACE% get deployments,replicasets,pods,services -o wide'
            }
        }

        stage('Smoke test') {
            when { branch 'main' }
            steps {
                // проверка «как пользователь»: запросы с компьютера на NodePort кластера
                // (скрипт использует только стандартную библиотеку Python)
                bat '"%PYTHON%" services\\e2e\\smoke.py %APP_URL%'
                bat 'curl -fsS %APP_URL%/api/svc/catalog/info'
            }
            post {
                failure {
                    // новая версия не работает — возвращаем предыдущую
                    script {
                        for (d in DEPLOYMENTS) {
                            bat(returnStatus: true, script: "kubectl -n %K8S_NAMESPACE% rollout undo deployment/${d}")
                        }
                    }
                }
            }
        }

        stage('Publish latest') {
            when { branch 'main' }
            steps {
                // тег latest получает только версия, прошедшая smoke-тест в кластере
                withCredentials([usernamePassword(credentialsId: 'docker-hub-credentials',
                                                  usernameVariable: 'DH_USER',
                                                  passwordVariable: 'DH_TOKEN')]) {
                    bat 'echo %DH_TOKEN%| docker login -u %DH_USER% --password-stdin'
                    script {
                        for (s in DEPLOYMENTS) {
                            bat "docker tag %DOCKERHUB_USER%/library-${s}:%IMAGE_TAG% %DOCKERHUB_USER%/library-${s}:latest"
                            bat "docker push %DOCKERHUB_USER%/library-${s}:latest"
                        }
                    }
                }
            }
            post {
                always { bat(returnStatus: true, script: 'docker logout') }
            }
        }
    }

    post {
        always {
            junit allowEmptyResults: true, testResults: 'reports/*.xml'
            script {
                for (s in SERVICES) {
                    bat(returnStatus: true, script: "docker image rm library-${s}-test:%IMAGE_TAG% >nul 2>&1")
                }
            }
            bat(returnStatus: true, script: 'docker image prune -f')
        }
        success {
            script {
                if (env.BRANCH_NAME == 'main') {
                    echo "Сборка main #${env.BUILD_NUMBER} развёрнута в Kubernetes: ${env.APP_URL}"
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
