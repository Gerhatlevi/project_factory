## Repos and Files

* **Fast Fabric Repo:** [https://github.com/GoogleCloudPlatform/cloud-foundation-fabric](https://github.com/GoogleCloudPlatform/cloud-foundation-fabric)
* **Project Factory App Repo:** [https://github.com/akoskohl/project-factory-app](https://github.com/akoskohl/project-factory-app)
* **Required YAML file schema:** `./schema.json`

## Technology Components

* **Firebase:**
    * Essentially a predefined and interconnected cloud infrastructure with built-in services like FireAuth.
    * The application will be deployed here.
* **Streamlit:**
    * A Python-based web application development framework.
    * Installation: `pip install streamlit`
    * Import: `import streamlit as st`
    * Run: `streamlit run <python_file>`
    * In this project, it will be used as the web application coding tool. It will generate the YAML file based on user inputs.
* **Eventarc:**
    * An event-driven service.
    * Collects events and publishes them to a central bus.
    * In this case, it will send an event to subscribers when an YAML file is created or modified (object.finalize)
* **Pub/Sub:**
    * A publisher-subscriber messaging service, enabling asynchronous communication.
    * Eventarc will publish events to a Pub/Sub topic.
* **Cloud Build:**
    * This will be the event subscriber.
    * It builds the project based on the provided parameters. The YAML file will contain the project configuration details for the Project Factory App.
* **State file:**
    Used to save the configuration state for a specific project for future modifications. **A separate state file will be maintained for each created project**, likely stored in Cloud Storage, containing the current state of that project's infrastructure.

## Workflow

1.  The user provides the necessary project configuration parameters through the Streamlit web application.
2.  The Streamlit application generates a YAML file based on the `./schema.json` schema using the provided inputs.
3.  The generated YAML file is uploaded to a Cloud Storage bucket.
4.  Eventarc detects the object finalization event in this bucket.
5.  Eventarc sends a message to a Pub/Sub topic.
6.  Cloud Build subscribes to this Pub/Sub topic and is triggered upon receiving the message.
7.  The Cloud Build pipeline reads the YAML file from Cloud Storage.
8.  Cloud Build uses the Cloud Foundation Fabric and the Project Factory App to create the Google Cloud project according to the configuration in the YAML file and the corresponding state file.