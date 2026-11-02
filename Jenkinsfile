// Taskboard CI - declarative pipeline.
//
// What triggers a build
//   * Every pushed commit: pollSCM below, or (better) a GitHub/GitLab webhook.
//   * "Build with Parameters" in the Jenkins UI (BACKEND / PLATFORM).
//
// Commit-message directives (read from the HEAD commit) narrow an automatic build:
//   [skip ci]            nothing is built
//   [python] / [node]    only that backend
//   [linux]  / [windows] only that platform
// e.g.  git commit -m "fix(node): handle empty body [node] [linux]"
//
// Agents: needs nodes labelled `linux` and `windows` with git, Python 3.10+ and Node 18+.
// Plugins: Pipeline, Git, JUnit, Timestamper.

def headCommitMessage() {
    if (isUnix()) {
        return sh(script: 'git log -1 --pretty=%B', returnStdout: true).trim()
    }
    return bat(script: '@git log -1 --pretty=%%B', returnStdout: true).trim()
}

// First option found in the message wins; otherwise fall back to the build parameter.
def pickFromMessage(String message, List<String> options, String fallback) {
    for (String option : options) {
        if (message.contains("[${option}]")) {
            return option
        }
    }
    return fallback
}

def runScript(String name, String backend) {
    if (isUnix()) {
        sh "chmod +x scripts/*.sh && ./scripts/${name}.sh ${backend}"
    } else {
        bat "powershell -NoProfile -ExecutionPolicy Bypass -File scripts\\${name}.ps1 -Backend ${backend}"
    }
}

pipeline {
    agent none

    options {
        timestamps()
        timeout(time: 30, unit: 'MINUTES')
        buildDiscarder(logRotator(numToKeepStr: '20'))
    }

    parameters {
        choice(name: 'BACKEND', choices: ['all', 'python', 'node'], description: 'Backend implementation(s) to build')
        choice(name: 'PLATFORM', choices: ['all', 'linux', 'windows'], description: 'Agent OS(es) to build on')
    }

    triggers {
        pollSCM('H/5 * * * *')
    }

    stages {
        stage('Plan') {
            agent any
            steps {
                script {
                    def message = headCommitMessage()
                    echo "HEAD commit message:\n${message}"
                    env.SKIP_CI = (message.contains('[skip ci]') || message.contains('[ci skip]')) ? 'true' : 'false'
                    env.WANT_BACKEND = pickFromMessage(message, ['python', 'node'], params.BACKEND)
                    env.WANT_PLATFORM = pickFromMessage(message, ['linux', 'windows'], params.PLATFORM)
                    currentBuild.description = env.SKIP_CI == 'true'
                        ? 'skipped: [skip ci]'
                        : "backend=${env.WANT_BACKEND} platform=${env.WANT_PLATFORM}"
                    echo currentBuild.description
                }
            }
        }

        stage('Build & Test') {
            when {
                beforeAgent true
                environment name: 'SKIP_CI', value: 'false'
            }
            matrix {
                axes {
                    axis {
                        name 'OS'
                        values 'linux', 'windows'
                    }
                    axis {
                        name 'IMPL'
                        values 'python', 'node'
                    }
                }
                when {
                    beforeAgent true
                    allOf {
                        expression { env.WANT_PLATFORM in ['all', env.OS] }
                        expression { env.WANT_BACKEND in ['all', env.IMPL] }
                    }
                }
                agent { label "${OS}" }
                stages {
                    stage('Build') {
                        steps {
                            script { runScript('build', env.IMPL) }
                        }
                    }
                    stage('Test') {
                        steps {
                            script { runScript('test', env.IMPL) }
                        }
                    }
                }
                post {
                    always {
                        junit allowEmptyResults: true, testResults: 'reports/*.xml'
                    }
                    success {
                        archiveArtifacts artifacts: 'dist/*.tar.gz, dist/*.zip', allowEmptyArchive: true, fingerprint: true
                    }
                }
            }
        }
    }
}
