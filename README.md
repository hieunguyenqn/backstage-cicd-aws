# Backstage IAC
This project uses [CDK](https://docs.aws.amazon.com/cdk/latest/guide/home.html) to deploy a containerized version of your backstage instance along with the required infrastructure in into a AWS account, to host your own [Backstage](https://backstage.io) based service.


What's Here
-----------
* README.md - this file
* buildspec.yml - this file is used by AWS CodeBuild to package stageback 
  infra for deployment to AWS cloud
* backstage_cicd_aws\infra_pipeline.py - this file is used to deployment of the infra  stack. 
* backstage_cicd_aws\app_pipeline.py - this file is used to deployment of the application stack. 
* backstage_cicd_aws\backstage.py - this file is Backstage Infrastructure Stack.
* configs\env-config.yaml - this file is used to store secrets names and parameters to configure both the CDK deployment and to pass them to your backstage app container at runtime.

Getting Started
---------------

Documentation
------------------
## 