pipeline {
  agent any

  options {
    copyArtifactPermission(projectNames: 'doni*')
  }

  stages {
    stage('package') {
      steps {
        dir('dist') {
          deleteDir()
        }
        sh 'pip install build'
        sh 'python -m build'
        sh 'find dist -type f -name *.tar.gz -exec cp {} dist/doni.tar.gz \\;'
        archiveArtifacts(artifacts: 'dist/doni.tar.gz', onlyIfSuccessful: true)
      }
    }
  }
}
