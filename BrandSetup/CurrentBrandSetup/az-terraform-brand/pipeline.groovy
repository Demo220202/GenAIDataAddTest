pipeline{
    agent any
    environment {
        ARM_CLIENT_ID = credentials('ARM_CLIENT_ID')
        ARM_CLIENT_SECRET = credentials('ARM_CLIENT_SECRET')
        ARM_TENANT_ID = credentials('ARM_TENANT_ID')
    }
    stages{
        stage ('refresh'){
            steps{
                sh "az account list --refresh"
            }
        }
        stage ('AZ Terraform init'){
            steps{
                dir("az-terraform-brand"){
                    sh "rm -rf .terraform* *tfstate*"
                    sh "terraform init"
                }
            }
        }

        stage ('Resource Registration'){
            steps{
                dir("az-terraform-brand/PyCode"){
                    sh '''
                        python3.10 -m venv venv
                        . venv/bin/activate
                        pip install --upgrade pip
                        pip install -r requirements.txt
                        python3 resourceRegistration.py --subscription_id $subscription_id
                        echo "Deteling the resources now!"
                        python3 deleteTempResources.py --subscription_id $subscription_id
                    '''
                }
            }
        }

        stage ('AZ Terraform Plan'){
            steps{
                dir("az-terraform-brand"){
                    sh "terraform plan -var 'subscription_name=$subscription_id' -var 'diagnostic_setting=$diagnostic_settings' -var 'storage_name=$storage_account' -var 'Brand=$brand'"
                }
            }
        }
        stage('Approval'){
            input {
                message  "Apply Changes to Infrastructure ?"
                ok "Approve"
            }
            steps {
                echo "Need Approval !"
            }
        }
        stage ('AZ Terraform Apply'){
            
            steps{
                dir("az-terraform-brand"){
                    sh "terraform apply --auto-approve -var 'subscription_name=$subscription_id' -var 'diagnostic_setting=$diagnostic_settings' -var 'storage_name=$storage_account' -var 'Brand=$brand'"
                }
            }
        }

        stage ('Budget Creation'){
            steps{
                dir("az-terraform-brand/PyCode"){
                    sh '''
                        . venv/bin/activate
                        python3 BudgetCreation.py --subscription_id $subscription_id
                    '''
                }
            }
        }

        stage ('CLU Resources Creation'){
            steps{
                dir("az-terraform-brand/PyCode"){
                    sh '''
                        . venv/bin/activate
                        python3 AzureCLUScript.py --subscription_id $subscription_id --brand $brand
                    '''
                }
            }
        }

    }
    post {
        success {
            dir('az-terraform-brand') {
                sh "terraform output > azure.json && cat azure.json"
            }
        }
        failure {
            sh "pwd"
            dir('az-terraform-brand'){
                sh "terraform destroy --auto-approve -var 'subscription_name=$subscription_id' -var 'diagnostic_setting=$diagnostic_settings' -var 'storage_name=$storage_account' -var 'Brand=$brand'"
                sh "rm -rf *tfstate*"
            }
        }
    }
}
