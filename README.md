# Task Management Application along with CICD Deployment

This repository contains a Flask-based **Task Management Application** with a CI/CD pipeline for building, testing, and deploying Docker images.

The application includes user authentication, task management features, and Prometheus metrics for monitoring.

---

## Features

- **Task Management**: Add, view, and manage tasks with priority and completion status.
- **User Authentication**: Secure login and signup functionality.
- **Prometheus Metrics**: Exposes `/metrics` endpoint for monitoring.
- **MongoDB Integration**: Stores user and task data in MongoDB.
- **CI/CD Pipeline**: Automated Docker image build, vulnerability scanning, and deployment using GitHub Actions.
- **Google Cloud Pub/Sub**: Publishes deployment notifications.

---

## Prerequisites

- **Python 3.9+**
- **Docker**
- **MongoDB**
- **Harbor Registry**
- **Google Cloud Pub/Sub**

---

## Installation

1. Clone the repository:

```bash
git clone https://github.com/yagnesh0312/cicd-deployment.git
cd cicd-deployment
```

2. Install dependencies

```bash
pip install -r requirements.txt
```

3. Set up environment variables: Create a `.env` file in the root directory with the following:

```text
MONGO_CONN_STRING=<your-mongo-connection-string>
MONGO_DB_NAME=<your-database-name>
MONGO_COLLECTION_NAME=<your-collection-name>
SECRET_KEY=<your-secret-key>
PORT=3000
```

4. Run the application

```bash
python app.py
```

5. Access the application at `http://localhost:3000`

## Docker Usage

- Build the Docker Image

```bash
docker build -t task-management-app .
```

- Run the Docker Container

```bash
docker run -p 3000:3000 --env-file .env task-management-app
```

## CI/CD Pipeline

The CI/CD pipeline is defined in .github/workflows/Build-Deployment-Harsh.yml and includes the following steps:

**`Build Docker Image`**: Builds the application image.
**`Run Tests`**: Executes tests inside a Docker container.
**`Trivy Scan`**: Scans the Docker image for vulnerabilities.
**`Push to Harbor`**: Pushes the image to the Harbor registry.
**`Google Cloud Pub/Sub`**: Publishes a deployment notification.

## Prometheus Metrics

The application exposes Prometheus metrics at the /metrics endpoint. These metrics include:

- HTTP request counts
- Request latencies
- Custom application metrics

## Project Structure

```text
.
├── app.py                 # Main application code
├── Dockerfile             # Docker configuration
├── requirements.txt       # Python dependencies
├── .github/workflows/     # CI/CD pipeline configuration
├── templates/             # HTML templates for Flask
├── static/                # Static files (CSS, JS, images)
└── README.md              # Project documentation
```

## Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository.
2. Create a new branch: git checkout -b feature-name.
3. Commit your changes: git commit -m "Add feature-name".
4. Push to the branch: git push origin feature-name.
5. Open a pull request.

## Contact

```text
Feel free to customize the content further based on your specific project details!
```
