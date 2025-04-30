Based on the information gathered, here is the draft for your README.md file for the EduCampus repository:

# EduCampus

EduCampus is a chatbot platform designed to facilitate online learning and campus management. This repository contains the core components of the EduCampus chatbot system, including backend services, frontend applications, and deployment configurations.

## Table of Contents
- [Introduction](#introduction)
- [Technologies Used](#technologies-used)
- [Installation](#installation)
- [Usage](#usage)
- [Contributing](#contributing)
- [License](#license)
- [Contributors](#contributors)


## Introduction
EduCampus aims to provide a seamless online education experience through an intelligent chatbot, offering tools for both students and administrators. The platform includes features such as course management, student tracking, online assessments, and more.

## Technologies Used
EduCampus is built using the following technologies:
- **Backend**: Python, Flask, Groq, Langchain
- **Frontend**: Vue.js
- **Markup**: HTML
- **Containerization**: Docker
- **Scripting**: JavaScript
- **Database**: Qdrant

## Installation
To set up EduCampus locally, follow these steps:

1. **Clone the repository**:
    ```sh
    git clone https://github.com/parthpetkar/EduCampus.git
    cd EduCampus
    ```

2. **Set up the backend**:
    ```sh
    # Create a virtual environment
    python -m venv venv
    source venv/bin/activate  # On Windows, use `venv\Scripts\activate`

    # Install backend dependencies
    pip install -r requirements.txt
    ```

3. **Set up the frontend**:
    ```sh
    cd frontend
    npm install
    npm run serve
    ```
4. **Set up environmental variables**:
   
   Use .env.example

5. Set up Qdrant
   ```sh
    docker pull qdrant/qdrant 
    docker run -p 6333:6333 -v .:/qdrant/storage qdrant/qdrant
   ```

6. **Set up database**:
    ```sh
    # Run the file ingest.py
    python ingest.py
    ```
7. **Run the Docker container**:
    ```sh
    docker-compose up --build
    ```

## Usage
Once the installation is complete, you can start using EduCampus by navigating to `http://localhost:8080` in your web browser. Log in with your credentials to access the platform's features.

## Contributing
We welcome contributions from the community! To contribute to EduCampus, please follow these steps:

1. Fork the repository.
2. Create a new branch (`git checkout -b feature-branch`).
3. Make your changes and commit them (`git commit -m 'Add new feature'`).
4. Push to the branch (`git push origin feature-branch`).
5. Open a pull request.

Please make sure to follow our [Code of Conduct](CODE_OF_CONDUCT.md) and [Contributing Guidelines](CONTRIBUTING.md).

## License
EduCampus is licensed under the MIT License. See the [LICENSE](LICENSE) file for more information.
