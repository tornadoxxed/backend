#! /usr/bin/env python3

import requests
import time
import logging
import json
import os
import streamlit as st

# from dotenv import load_dotenv

# load_dotenv()

log = logging.getLogger("simple_example")
log.setLevel(logging.INFO)

query_id = 1279259
DUNE_API_KEY = os.environ["DUNE_API_KEY"]

headers = {"x-dune-api-key": DUNE_API_KEY}

QUERY_WORKING = ["QUERY_STATE_PENDING", "QUERY_STATE_EXECUTING"]
QUERY_DONE = "QUERY_STATE_COMPLETED"


@st.cache
def execute_query(query_id):
    log.info(f"Executing query {query_id}")
    r = requests.post(
        f"https://api.dune.com/api/v1/query/{query_id}/execute",
        headers=headers,
    )

    r.raise_for_status()

    execute_response = r.json()
    execution_id = execute_response["execution_id"]
    return execution_id


@st.cache
def wait_for_execution(execution_id):
    log.info("Waiting for execution")
    status_response = {}
    while True:
        r = requests.get(
            f"https://api.dune.com/api/v1/execution/{execution_id}/status",
            headers=headers,
        )

        status_response = r.json()

        if status_response["state"] not in QUERY_WORKING:
            break

        log.info("Query is still being executed, waiting")
        time.sleep(3)

    if status_response["state"] != QUERY_DONE:
        raise SystemExit(f'Error: Query state is {status_response["state"]}')


@st.cache
def download_response(execution_id):
    log.info("Downloading response")
    r = requests.get(
        f"https://api.dune.com/api/v1/execution/{execution_id}/results", headers=headers
    )

    r.raise_for_status()

    return r.json()


def parse(raw):
    return raw["result"]["rows"]


def save(parsed):
    with open("site/src/assets/doxxed.json", "w") as file:
        file.write(json.dumps(parsed))


if __name__ == "__main__":

    execution_id = execute_query(query_id)
    wait_for_execution(execution_id)
    raw = download_response(execution_id)
    parsed = parse(raw)
    save(parsed)
