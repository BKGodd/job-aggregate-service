# Goal
Imagine we were to use an arbitrary excel file that contains salary data on 500K+ jobs in the market (like [this one](https://www.foreignlaborcert.doleta.gov/pdf/PerformanceData/2019/H-1B_Disclosure_Data_FY2019.xlsx)), we will then create a service that allows us to load this information into a database and query different jobs for aggregate data. One of the best NoSQL databases available that supports full-text search and fast aggregation calculations on large data is `Elasticsearch`, which is what we will be using. We will also be using `FastAPI`, due to it being a modern, robust micro-framework. We will also be using `Gunicorn` (with `Uvicorn` workers) and `nginx` as a part of our local `docker-compose` deployment.

This project was developed and successfully tested on both MacOS and Linux. The following versions of docker and docker-compose were used, for reference:
```
docker: 20.10.17
docker-compose: 1.29.2
```

# How to deploy
This service was intended to be deployed locally. Being in the root directory (where `docker-compose.yaml` is), you can simply run the following to deploy (and detach to run in the background):
```bash
docker-compose -f docker-compose.yaml up -d --build
```
The way in which this service was built, the initial startup will download the excel file (via the URL in the task description), and initialize the `Elasticsearch` database with the data. You can expect this startup process to take roughly 5-10 minutes (depending on internet connection, system specs, etc.). As long as the docker volumes persist, this initialization process will run only once. Each time the service is re-deployed, it will startup in normal, expected time.

To know when the startup process is complete, simply run the following in order to check the status in the logs:
```bash
docker logs $(docker ps -qf "name=job_app")
```
You will know the startup is in progess if you see `Waiting for application startup` as the last printed log. Once you see the confirmation `Application startup complete` in the logs, then the API is able to start receiving connections.

**Note**: If for some reason an error occurs when deploying, this could be due to how `Elasticsearch` uses virtual memory on Linux. Running the following command can increase the virtual memory limits, as an example on Ubuntu, which may resolve the issue:
```bash
sudo sysctl -w vm.max_map_count=262144
```

# Testing
Once the service is deployed and initialization/startup has completed, you are then free to test it at the following URL. Note that the port `5000` is an environment variable in the `.env` file and can be changed, if needed:
```bash
http://localhost:5000/
```

Perform a GET request, providing the `title` and `location` queries as parameters in the URL. An example GET request: 
```
http://localhost:5000/?title=java&location=oregon
```

You can also run the basic pytests I created. From the root directory, run:
```
pytest services/web/tests/
```

# Docs
After the service has been deployed, feel free to check out the generated Swagger UI documentation at the following URL in a web browser on the machine:
```bash
http://localhost:5000/docs/
```

# How to cleanup
If you want to stop and remove the containers, but intend to re-deploy at a later time (persisting volumes and avoiding initialization again), simply run:
```bash
docker-compose down
```

To stop and completely remove the containers, volumes, and networks, you can run:
```bash
docker-compose down -v --rmi local
```

# Assumptions and Observations
I will briefly explain the assumptions made when completing this project.

1. I assume the job title is required. If this is invalid or missing from any row in the excel file, it will not be used (skipped).
2. I assume a valid salary **and** unit of pay is required. If either is invalid or missing in the excel row, it will not be used (skipped).
3. I assume that city, state, or both must be found in an excel row in order for the data to be valid and inserted into the database. If both are invalid or missing, I assume this is insufficient data and will not be used (skipped).
4. "Salary" is assumed to be "base salary", and this is taken from the `WAGE_RATE_OF_PAY_FROM_1` column in the excel file.
    * From testing and observation, this column is always populated for each job, and so this remains as the  primary source of salary data. A more general approach would be to look at other base salaries if none were found (`WAGE_RATE_OF_PAY_FROM_2`, `WAGE_RATE_OF_PAY_FROM_3`, and so on), but they are largely empty throughout in this case.
5. The salary unit of pay is taken from the `WAGE_UNIT_OF_PAY_1` column in the excel file.
    * From testing and observation, units of pay rarely differ between the different `WAGE_UNIT_OF_PAY_X` columns. If there is a difference, this largely indicates an error within the excel data, where a salary reported as `hourly` should have instead been `yearly`, for example. I assume that if the unit of pay is not `yearly` and is taken at face-value to be calculated at over $10 million, then the unit of pay is mistaken and fixed to `yearly` instead. This will correct most, if not all, "incorrectly" reported salaries.
6. City and state locations are taken from the `WORKSITE_CITY_1` and `WORKSITE_STATE_1` columns in the excel file.
    * From testing and observation, these are the primary columns used in providing worksite locations.
    * Some rows will use the abbreviated form of the state (e.g. CA, TX, ...). I assume the user would not be searching for locations using the abbreviated form, and so all abbreviated states are converted to the full state name.
7. I do not assume a particular order of words from the user's `title` or `location` query. Therefore, the way the `Elasticsearch` query is structured, word ordering does not matter when performing a search.
