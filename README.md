![Lint-free](https://github.com/nyu-software-engineering/containerized-app-exercise/actions/workflows/lint.yml/badge.svg)

# Containerized App Exercise

Build a containerized app that uses machine learning. See [instructions](./instructions.md) for details.





# Setting Up MongoDB with Docker

1. **Install Docker Desktop:**
   - Make sure [Docker Desktop](https://www.docker.com/products/docker-desktop/) is installed and running on your system.


2. **Pull the MongoDB Image:**
   ```
   docker pull mongo
   ```

3. **Run MongoDB Container:**
   ```
   docker run --name mongodb -d -p 27017:27017 -e MONGO_INITDB_ROOT_USERNAME=admin -e MONGO_INITDB_ROOT_PASSWORD=password -v mongo_data:/data/db mongo
   ```
   - You can change the admin username and password as needed.

4. **Verify MongoDB is Running:**
   ```
   docker ps
   ```

5. **Access the MongoDB Shell:**
   ```
   docker exec -it mongodb mongosh -u admin -p password
   ```

6. **Create the .env File:**
   - Based on the example provided in `.env.example`, create a `.env` file with the following structure:
     ```
     MONGO_INITDB_ROOT_USERNAME=your_username
     MONGO_INITDB_ROOT_PASSWORD=your_password
     MONGO_DB_NAME=voice_data
     MONGO_PORT=27017
     ```
   - Make sure the username and password match the ones you used when running the MongoDB container.

7. **Stop and Remove MongoDB Container:**
   ```
   docker stop mongodb
   docker rm mongodb
   ```







