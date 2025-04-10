![Lint-free](https://github.com/nyu-software-engineering/containerized-app-exercise/actions/workflows/lint.yml/badge.svg)
![CI](https://github.com/nyu-software-engineering/containerized-app-exercise/actions/workflows/ci.yml/badge.svg)

# Containerized App Exercise

Build a containerized app that uses machine learning. See [instructions](./instructions.md) for details.

# Voice Transcription Web App 

This is a full-stack, containerized web application that allows users to upload audio files, which are then transcribed using a machine learning service (Deepgram API). Transcriptions are stored in MongoDB and displayed in a user-friendly interface.

## Team

- [Tony Zhao](https://github.com/Tonyzsp)
- [Rin Qi](https://github.com/Rin-Qi)
- [Corrine Huang](https://github.com/ChuqiaoHuang)

## Prerequisites

- [Docker Desktop](https://www.docker.com/products/docker-desktop/)
- A Deepgram API key (register for free at [deepgram.com](https://www.deepgram.com/))


## Structure

- `web-app/`: Frontend + backend Flask app
- `machine-learning-client/`: Deepgram ML client for transcript generation
- `docker-compose.yml`: Service orchestration
- `.env`: Runtime environment variables


## Getting Started

### 1. Clone the Repository

```bash
git clone https://github.com/your-username/4-containers-aaa.git
cd 4-containers-aaa
```

### 2. Create Environment Configuration

Create a `.env` file in the root directory of the project:

```env
MONGO_INITDB_ROOT_USERNAME=your_username
MONGO_INITDB_ROOT_PASSWORD=your_password
MONGO_DB_NAME=voice_data
MONGO_PORT=27017
MONGO_HOST=localhost

DEEPGRAM_API_KEY=your_deepgram_api_key
```

### 3. Start the Application

From the root of the project:

```bash
docker-compose up --build -d
```

This will:
- Build Docker images for `web-app`, `ml-client`, and `mongodb`
- Set up a Docker network for inter-service communication
- Mount shared volumes for audio file transfer

### 4. Access the Web App

Once containers are up, go to:

```
http://localhost:5000
```

## Notes

- Audio files are uploaded to `web-app/static/uploaded_audio`
- Transcription is triggered automatically on upload
- Shared volume between web and ML client ensures ML has access to the audio file
- You cannot either upload the MP3 or record
for debugging, use ....  log


## For Debugging

To check logs for debugging:

```bash
docker logs web-app
```
```bash
docker logs ml-client
```





