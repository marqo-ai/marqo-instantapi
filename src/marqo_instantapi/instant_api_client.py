import requests
import json
from typing import Dict, Any, Union, Optional


class InstantAPIClient:
    """A client for the InstantAPI API."""

    def __init__(self, api_key):
        self.api_key = api_key
        self.base_url = "https://instantapi.ai/api"
        self.headers = {"Content-Type": "application/json"}

    def retrieve(
        self,
        webpage_url: str,
        api_method_name: str,
        api_response_structure: Union[str, Dict[str, Any]],
        api_parameters: Optional[Union[str, Dict[str, Any]]] = None,
        country_code: Optional[str] = None,
        verbose: bool = False,
        wait_for_xpath: Optional[str] = None,
        enable_javascript: Optional[bool] = None,
        cache_ttl: Optional[int] = None,
        serp_limit: Optional[int] = None,
        serp_site: Optional[str] = None,
        serp_page_num: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Implements an interface to the InstantAPI retrieve endpoint.

        Args:
            webpage_url (str): The URL of the webpage to retrieve data from.
            api_method_name (str): The name of the API method to use.
            api_response_structure (Union[str, Dict[str, Any]]): The structure of the API response.
            api_parameters (Optional[Union[str, Dict[str, Any]]], optional): The parameters to pass to the API method. Defaults to None.
            country_code (Optional[str], optional): The country code to use for the request. Defaults to None.
            verbose (bool, optional): Whether to return verbose output. Defaults to False.
            wait_for_xpath (Optional[str], optional): The XPath to wait for before returning the response. Defaults to None.
            enable_javascript (Optional[bool], optional): Whether to enable JavaScript in the browser. Defaults to None.
            cache_ttl (Optional[int], optional): The time-to-live for the cache. Defaults to None.
            serp_limit (Optional[int], optional): The number of results to return for SERP requests. Defaults to None.
            serp_site (Optional[str], optional): The site to use for SERP requests. Defaults to None.
            serp_page_num (Optional[int], optional): The page number to use for SERP requests. Defaults to None.

        Returns:
            Dict[str, Any]: The response from the InstantAPI retrieve endpoint.
        """

        if isinstance(api_response_structure, dict):
            api_response_structure = json.dumps(api_response_structure)

        payload = {
            "webpage_url": webpage_url,
            "api_method_name": api_method_name,
            "api_response_structure": api_response_structure,
            "api_key": self.api_key,
        }

        if api_parameters:
            payload["api_parameters"] = api_parameters
        if country_code:
            payload["country_code"] = country_code
        if verbose:
            payload["verbose"] = verbose
        if wait_for_xpath:
            payload["wait_for_xpath"] = wait_for_xpath
        if not enable_javascript:
            payload["enable_javascript"] = enable_javascript
        if cache_ttl:
            payload["cache_ttl"] = cache_ttl
        if serp_limit:
            payload["serp_limit"] = serp_limit
        if serp_site:
            payload["serp_site"] = serp_site
        if serp_page_num:
            payload["serp_page_num"] = serp_page_num

        request_url = self.base_url + "/retrieve/"

        response = requests.post(request_url, json=payload, headers=self.headers)

        if response.status_code == 200:
            return json.loads(response.text)
        else:
            return {
                "error": True,
                "reason": response.text,
                "status_code": response.status_code,
            }

    def next_pages(self, webpage_url: str) -> dict:
        """TODO: Implement the next_pages method."""
        payload = {"webpage_url": webpage_url, "api_key": self.api_key}
        response = requests.post(self.base_url + "/next_pages/", json=payload)
        if response.status_code == 200:
            return response.json()
        else:
            return {"error": True, "reason": response.text}
