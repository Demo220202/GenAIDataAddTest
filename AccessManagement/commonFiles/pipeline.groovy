pipeline{
    agent any

    stages{

        stage ('Access given to users as per labels'){
            steps{
                dir("PyCode"){
                    sh '''
                        python3.10 -m venv venv
                        . venv/bin/activate
                        pip install --upgrade pip
                        pip install -r requirements.txt
                        python3 AccessBasedOnLabels.py --brand "$brand_name" --env $env --email $user_email --label $label --label_value "$label_name"
                    '''
                }
            }
        }

    }
    post {
        success {
            dir('PyCode') {
                sh """
                   cat output_json.json || echo "output_json.json not found"
                   rm output_json.json
               """
            }
        }
        failure {
            dir('PyCode'){
               sh '''
                   cat output_json.json || echo "output_json.json not found"
                   rm -f output_json.json
               '''
            }
        }
    }
}
