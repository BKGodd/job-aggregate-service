"""
Created by: Brandon Goddard
Description: This module is for defining the API and
             handling requests to the database service.
"""
from os.path import isfile, join
from os import environ
from tempfile import TemporaryDirectory

from ssl import create_default_context
from fastapi import FastAPI, HTTPException
from elasticsearch import AsyncElasticsearch
from pydantic import BaseModel

from database import download_excel, load_bulk, build_query


app = FastAPI()

class OutputSchema(BaseModel):
    """
    API response model for validation.

    Attriubutes:
        data_points (int): Total number of data point hits
                           from Elasticsearch query, defaults
                           to zero.
        mean_salary (float): Mean salary from aggregations,
                             defaults to None.
        median_salary (float): Median salary from aggregations,
                               defaults to None.
        percentile_25 (float): 25th percentile of salary from
                               aggregations, defaults to None.
        percentile_75 (float): 75th percentile of salary from
                               aggregations, defaults to None.
    """
    data_points: int = 0
    mean_salary: float = None
    median_salary: float = None
    percentile_25: float = None
    percentile_75: float = None


def get_elastic_db():
    """
    Establish and return a connection to the Elasticsearch database.

    Returns:
        (AsyncElasticsearch): Database connection instance.
    """
    context = create_default_context(cafile=environ['ESDB_CERT'])
    elastic_db = AsyncElasticsearch(hosts=f"https://esdb:{environ['ESDB_PORT']}",
                            basic_auth=(environ['ELASTIC_USERNAME'],
                                        environ['ELASTIC_PASSWORD']),
                            ssl_context=context)

    return elastic_db


@app.on_event("startup")
async def init_elastic_db():
    """Initialize Elasticsearch database on service startup."""
    elastic_db = get_elastic_db()
    # Create elasticsearch index if DNE
    if not await elastic_db.indices.exists(index=environ['ESDB_INDEX']):
        # Explicit mappings
        mappings = {"properties": {
                        "job_title": {"type": "text"},
                        "city_state": {"type": "text"},
                        "salary": {"type": "half_float"}}}
        await elastic_db.indices.create(index=environ['ESDB_INDEX'], mappings=mappings)

    # If no data is in the index, load in the excel file
    num_docs = await elastic_db.count(index=environ['ESDB_INDEX'])
    if num_docs['count'] == 0:
        with TemporaryDirectory() as tmpdir:
            # Donwload excel file if not already present in directory
            tmp_excel_filepath = join(tmpdir, 'tmp.xlsx')
            if not isfile(tmp_excel_filepath):
                download_excel(environ['EXCEL_URL'], tmp_excel_filepath)
            # Process and load all excel data into Elasticsearch
            await load_bulk(tmp_excel_filepath, elastic_db)


@app.on_event("shutdown")
async def shutdown():
    """Close database connections when service is shutdown."""
    elastic_db = get_elastic_db()
    await elastic_db.close()


@app.get("/", response_model=OutputSchema)
async def get(title: str = '', location: str = ''):
    """
    Handles HTTP GET requests to the Elasticsearch database,
    querying salary aggregations. We want either the job title,
    the job location, or both queries to be possible for the user.

    Args:
        title (str, optional): Job title query text
                               (given as URL parameter).
        location (str, optional): Location query text
                                  (given as URL parameter).

    Returns:
        (dict): Response of the Elasticsearch query aggregations
                (automatically converted to JSON).
    """
    # The user needs to provide either one or both inputs to be a valid query
    title = title.strip()
    location = location.strip()
    if not (title or location):
        detail = "Not enough inputs provided, expected either 'title' or 'location'"
        raise HTTPException(status_code=404, detail=detail)

    # Create our aggregation query, then perform a search
    query, aggs = build_query((title, location))
    elastic_db = get_elastic_db()
    result = await elastic_db.search(index=environ['ESDB_INDEX'], query=query,
                                    aggs=aggs, size=0, track_total_hits=True)

    # Gather our outputs from the response
    percentiles = result['aggregations']['salary_percentiles']['values']
    mean = result['aggregations']['salary_mean']['value']
    # Elasticsearch stored our scaled-down salaries, scale them back up
    if mean is not None:
        mean = round(mean*1e3, 2)
        percentiles['50.0'] = round(percentiles['50.0']*1e3, 2)
        percentiles['25.0'] = round(percentiles['25.0']*1e3, 2)
        percentiles['75.0'] = round(percentiles['75.0']*1e3, 2)
    response = {
        "data_points": result['hits']['total']['value'],
        "mean_salary": mean,
        "median_salary": percentiles['50.0'],
        "percentile_25": percentiles['25.0'],
        "percentile_75": percentiles['75.0']
    }

    return response
