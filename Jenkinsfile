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
        sh 'pip3 install build'
        sh 'python3 -m build'
        sh 'find dist -type f -name *.tar.gz -exec cp {} dist/doni.tar.gz \\;'
        archiveArtifacts(artifacts: 'dist/doni.tar.gz', onlyIfSuccessful: true)
      }
    }
  }
}
