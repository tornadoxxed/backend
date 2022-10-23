#! /usr/bin/env python3

import pandas as pd
from flask import Flask
from flask_caching import Cache
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from dotenv import load_dotenv

load_dotenv()

from dune import get_query

LOOKUP_QUERY_ID = 1279259
SEARCH_QUERY_ID = 1279881

config = {
    "DEBUG": True,  # some Flask specific configs
    "CACHE_TYPE": "SimpleCache",  # Flask-Caching related configs
    "CACHE_DEFAULT_TIMEOUT": 300,
}

app = Flask(__name__)
app.config.from_mapping(config)
cache = Cache(app)
CORS(app)
limiter = Limiter(
    app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"],
    storage_uri="memory://",
)


@app.route("/lookup")
@cache.memoize(timeout=60 * 60 * 24)
def lookup():
    """Returnt list of acconst most likely compromised"""

    response = get_query(LOOKUP_QUERY_ID)

    raw_df = pd.DataFrame(response)
    formated_df = raw_df[
        ["depositor_list", "recipient_list", "0.1 ETH", "1 ETH", "10 ETH", "100 ETH"]
    ]
    formated_df = formated_df.rename(
        columns={"depositor_list": "Depositor", "recipient_list": "Recipient"}
    )
    return formated_df.to_dict("records")


@app.route("/search/<account>")
@cache.memoize(timeout=60 * 60 * 24)
def search(account):
    """Search for a specific account or ENS"""

    response = get_query(SEARCH_QUERY_ID, parameters={"entry": account})

    return response
