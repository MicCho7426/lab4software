import requests


class DrugInfoService:
    """
    Wrapper around the OpenFDA Drug Label API.

    This service provides methods to retrieve public drug information
    such as name, manufacturer, purpose, and warnings from the
    official OpenFDA API.
    """

    BASE_URL = "https://api.fda.gov/drug/label.json"

    def fetch_external_info(self, drug_name: str):
        """
        Retrieve drug label information for a given medication name.

        Args:
            drug_name (str): The name of the medication to search for.

        Returns:
            dict: A dictionary containing drug info (e.g., brand_name)
                  or an error key.
        """
        if not drug_name:
            return {"error": "drug_name is required"}

        params = {"search": f"openfda.brand_name:{drug_name.lower()}", "limit": 1}

        try:
            resp = requests.get(self.BASE_URL, params=params, timeout=10)

            if resp.status_code != 200:
                return {"error": f"HTTP Error: {resp.status_code}"}

            data = resp.json()
            results = data.get("results")
            if not results:
                return {"error": "No results found for this medication."}

            record = results[0]

            # Map fields based on what test_services.py expects (brand_name)
            return {
                "brand_name": record.get("drug_brand_name", [drug_name])[0] if isinstance(record.get("drug_brand_name"),
                                                                                          list) else drug_name,
                "manufacturer": record.get("manufacturer_name", ["Unknown"])[0] if isinstance(
                    record.get("manufacturer_name"), list) else "Unknown",
                "substance": record.get("substance_name", ["Unknown"])[0] if isinstance(record.get("substance_name"),
                                                                                        list) else "Unknown",
            }

        except requests.exceptions.RequestException as e:
            return {"error": f"Connection Error: {str(e)}"}
        except Exception as e:
            return {"error": f"HTTP Error: {str(e)}"}