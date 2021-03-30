"""
Fetching data from google sheets
"""

import os.path
import pickle
from typing import Any, List, Optional

import pandas as pd
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

READ_SCOPE = 'https://www.googleapis.com/auth/spreadsheets.readonly'


class TokenCache:

    def __init__(self, token_file: Optional[str] = None):
        self.token_file = token_file or 'token.pickle'

    def get(self) -> Optional[Credentials]:
        creds = None
        if os.path.exists(self.token_file):
            with open(self.token_file, 'rb') as token:
                creds = pickle.load(token)

        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())

        return creds

    def put(self, creds: Credentials) -> None:
        with open(self.token_file, 'wb') as token:
            pickle.dump(creds, token)


class LocalServerFlow:
    """
    The authorization flow for local apps and CLIs.
    The code is taken from [here](https://developers.google.com/sheets/api/quickstart/python)
    """

    def __init__(self,
                 credentials_file: Optional[str] = None,
                 scopes: Optional[List[str]] = None,
                 token_cache: Optional[str] = None):
        self.credentials_file = credentials_file or 'credentials.json'
        self.scopes = scopes or [READ_SCOPE]
        self.token_cache = TokenCache(token_cache)

    def get_google_token(self) -> Credentials:
        creds = self.token_cache.get()
        if not creds:
            flow = InstalledAppFlow.from_client_secrets_file(
                self.credentials_file,
                scopes=self.scopes
            )
            creds = flow.run_local_server(port=0)
            self.token_cache.put(creds)
        return creds


class ManualFlow:
    """
    The manual authorization flow. A user has to follow the provided URL and paste
    the code obtained there manually.
    The logic is copied from [Here](https://google-auth-oauthlib.readthedocs.io/en/latest/reference/google_auth_oauthlib.flow.html)
    """

    def __init__(self,
                 credentials_file: Optional[str] = None,
                 scopes: Optional[List[str]] = None,
                 token_cache: Optional[str] = None):
        self.token_cache = TokenCache(token_cache)
        self.credentials_file = credentials_file or 'credentials.json'
        self.scopes = scopes or [READ_SCOPE]
        self.flow = InstalledAppFlow.from_client_secrets_file(
            self.credentials_file,
            scopes=self.scopes,
            redirect_uri='urn:ietf:wg:oauth:2.0:oob'
        )

    def get_url(self) -> str:
        auth_url, _ = self.flow.authorization_url(prompt='consent')
        return auth_url

    def put_code(self, code: str) -> None:
        self.flow.fetch_token(code=code)
        creds = self.flow.credentials
        self.token_cache.put(creds)

    def get_google_token(self) -> Optional[Credentials]:
        return self.token_cache.get()


def pull_sheet_data(token: Credentials, spreadsheet_id: str, range_name: str) -> List[List[Any]]:
    """
    Pulls data from Google Sheets API

    Parameters
    ----------
    token : Credentials
        OAuth2 token see :ref:`ManualFlow` or :ref:`LocalServerFlow`
    spreadsheet_id : str
        id of the spreadsheet (you can copy it from a spreadsheet URL)
    range_name : str
        see range [A1 notation](https://developers.google.com/sheets/api/guides/concepts#a1_notation)

    Returns
    -------
    List[List[Any]]
        list of rows from a given spreadsheet range
    """
    service = build('sheets', 'v4', credentials=token)
    sheet = service.spreadsheets()  # pylint: disable=no-member
    result = sheet.values().get(
        spreadsheetId=spreadsheet_id,
        range=range_name).execute()
    values = result.get('values', [])
    return values


def get_data(spreadsheet_id: str,
             range_name: str,
             token: Credentials,
             columns: Optional[List[str]] = None,
             merged_cols: Optional[List[str]] = None) -> pd.DataFrame:
    """
    Pulls data from Google Sheets API and transforms it into a pandas DataFrame.

    Parameters
    ----------
    token : Credentials
        OAuth2 token see :ref:`ManualFlow` or :ref:`LocalServerFlow`
    spreadsheet_id : str
        id of the spreadsheet (you can copy it from a spreadsheet URL)
    range_name : str
        see range [A1 notation](https://developers.google.com/sheets/api/guides/concepts#a1_notation)
    columns: Optional[List[str]]
        optional schema, if not provided first row of the range is considered as column names
    merged_cols: Optional[List[str]]
        columns that contain merged cells. Google Sheet doesn't copy the value to each merged row
    """

    data = pull_sheet_data(token=token, spreadsheet_id=spreadsheet_id, range_name=range_name)
    if columns:
        df = pd.DataFrame(data, columns=columns)
    else:
        df = pd.DataFrame(data[1:], columns=data[0])

    df = df.replace([''], [None])

    if merged_cols:
        df[merged_cols] = df[merged_cols].ffill()

    return df
