import requests
import json
from typing import Dict, Any, Union, Optional


class InstantAPIClient:
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
        payload = {"webpage_url": webpage_url, "api_key": self.api_key}
        response = requests.post(self.base_url + "/next_pages/", json=payload)
        if response.status_code == 200:
            return response.json()
        else:
            return {"error": True, "reason": response.text}
