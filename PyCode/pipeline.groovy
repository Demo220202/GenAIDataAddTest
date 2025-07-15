pipeline{
    agent any
    environment {
        ARM_CLIENT_ID = credentials('ARM_CLIENT_ID')
        ARM_CLIENT_SECRET = credentials('ARM_CLIENT_SECRET')
        ARM_TENANT_ID = credentials('ARM_TENANT_ID')
    }
    stages{

        stage ('GenAI DataAddition'){
            steps{
                dir("PyCode"){
                    sh '''
                        python3 -m venv venvgenaidata
                        . venvgenaidata/bin/activate
                        pip install --upgrade pip
                        pip install -r requirements.txt

                        # Convert multi-line account_list into individual quoted args
                        ACCOUNT_ARGS=""
                        while IFS= read -r line; do
                            ACCOUNT_ARGS+=" \"$line\""
                        done <<< "$account_list"

                        # Safely run Python script with proper quoting
                        eval "python3 GenAI_Data_Addition.py --env \\"$env\\" --brand_name \\"$brand_name\\" --csbaemail \\"$csbaemail\\" --account_list $ACCOUNT_ARGS --scenario \\"$scenario\\""
                    '''
                }
            }
        }

//         stage ('Deployment Resource Creation and Enabling Dynamic Quota'){
//             steps{
//                 dir("PyCode"){
//                     sh '''
//                         . venvgenai/bin/activate
//                         python3 GenAI_automation_P2.py
//                     '''
//                 }
//             }
//         }
//
//
//         stage ('DB Insertions'){
//
//             steps{
//                 dir("PyCode"){
//                     sh '''
//                         . venvgenai/bin/activate
//                         python3 GenAI_add_voices.py --env_m $env_main
//                         python3 AzureGenAIResourceDBInsertions.py --env_m $env_main  --user_email $user_email
//                         python3 GenAIPredictionWrapperDB.py --user_email $user_email --env_m $env_main
//                         python3 ProdCoachDBInsertions.py --env $env_pa  --email $user_email --env_m $env_main
//                     '''
//                 }
//             }
//         }
//
//         stage ('Checking DB Conection!'){
//             steps{
//                 dir("PyCode"){
//                     sh '''
//                         . venvgenai/bin/activate
//                         python3 ProdDBConnCheck.py --env_m $env_main  --env_p $env_pa --user_email $user_email --brands "$brand_names"
//                     '''
//                 }
//             }
//         }
//
//         stage ('Creation of Action Group and Alerts'){
//             steps{
//                 dir("PyCode"){
//                     sh '''
//                         . venvgenai/bin/activate
//                         python3 ActionGroupNAlerts.py
//                     '''
//                 }
//             }
//         }

//     }
//     post {
//         success {
//             dir('PyCode') {
//                 sh """
//                    cat openai_resources.json
//                    rm openai_resources.json
//                    cat alert_resources.json || echo "alert_resources.json not found"
//                    rm -f alert_resources.json
//                """
//             }
//         }
//         failure {
//             dir('PyCode'){
//                sh '''
//                    . venvgenai/bin/activate
//                    python3 GenAI_automation_P2_Revert.py
//                    if [ -f alert_resources.json ]; then
//                        python3 ActionGroupNAlerts_Revert.py
//                    else
//                        echo "alert_resources.json not found, skipping ActionGroupNAlerts_Revert.py"
//                    fi
//                    python3 GenAI_automation_Revert.py --subscription_id $subscription_id
//                    rm -f openai_resources.json
//                    rm -f alert_resources.json
//                '''
//             }
//         }
    }
}
