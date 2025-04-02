# reference: https://github.com/langchain-ai/langchain/blob/master/cookbook/wikibase_agent.ipynb
import httpx
import json
from mcp.server.fastmcp import FastMCP
from typing import List, Dict

server = FastMCP("Wikidata MCP Server")

WIKIDATA_URL = "https://www.wikidata.org/w/api.php"
HEADER = {"Accept": "application/json", "User-Agent": "foobar"}


async def search_wikidata(query: str, is_entity: bool = True) -> str:
    """
    Search for a Wikidata item or property ID by its query.
    """
    params = {
        "action": "query",
        "list": "search",
        "srsearch": query,
        "srnamespace": 0 if is_entity else 120,
        "srlimit": 1,  # TODO: add a parameter to limit the number of results?
        "srqiprofile": "classic_noboostlinks" if is_entity else "classic",
        "srwhat": "text",
        "format": "json",
    }
    async with httpx.AsyncClient() as client:
        response = await client.get(WIKIDATA_URL, headers=HEADER, params=params)
    response.raise_for_status()
    try:
        title = response.json()["query"]["search"][0]["title"]
        title = title.split(":")[-1]
        return title
    except KeyError:
        return "No results found. Consider changing the search term."


@server.tool()
async def search_entity(query: str) -> str:
    """
    Search for a Wikidata entity ID by its query.

    Args:
        query (str): The query to search for. The query should be unambiguous enough to uniquely identify the entity.

    Returns:
        str: The Wikidata entity ID corresponding to the given query."
    """
    return await search_wikidata(query, is_entity=True)


@server.tool()
async def search_property(query: str) -> str:
    """
    Search for a Wikidata property ID by its query.

    Args:
        query (str): The query to search for. The query should be unambiguous enough to uniquely identify the property.

    Returns:
        str: The Wikidata property ID corresponding to the given query."
    """
    return await search_wikidata(query, is_entity=False)


@server.tool()
async def get_properties(entity_id: str) -> List[str]:
    """
    Get the properties associated with a given Wikidata entity ID.

    Args:
        entity_id (str): The entity ID to retrieve properties for. This should be a valid Wikidata entity ID.

    Returns:
        list: A list of property IDs associated with the given entity ID. If no properties are found, an empty list is returned.
    """
    params = {
        "action": "wbgetentities",
        "ids": entity_id,
        "props": "claims",
        "format": "json",
    }
    async with httpx.AsyncClient() as client:
        response = await client.get(WIKIDATA_URL, headers=HEADER, params=params)
    response.raise_for_status()
    data = response.json()
    return list(data.get("entities", {}).get(entity_id, {}).get("claims", {}).keys())


@server.tool()
async def execute_sparql(sparql_query: str) -> str:
    """
    Execute a SPARQL query on Wikidata.

    You may assume the following prefixes:
    PREFIX wd: <http://www.wikidata.org/entity/>
    PREFIX wdt: <http://www.wikidata.org/prop/direct/>
    PREFIX p: <http://www.wikidata.org/prop/>
    PREFIX ps: <http://www.wikidata.org/prop/statement/>

    Args:
        sparql_query (str): The SPARQL query to execute.

    Returns:
        str: The JSON-formatted result of the SPARQL query execution. If there are no results, an empty JSON object will be returned.
    """
    url = "https://query.wikidata.org/sparql"
    async with httpx.AsyncClient() as client:
        response = await client.get(
            url, params={"query": sparql_query, "format": "json"}
        )
    response.raise_for_status()
    result = response.json()["results"]["bindings"]
    return json.dumps(result)


@server.tool()
async def get_metadata(entity_id: str, language: str = "en") -> Dict[str, str]:
    """
    Retrieve the English label and description for a given Wikidata entity ID.

    Args:
        entity_id (str): The entity ID to retrieve metadata for.
        language (str): The language code for the label and description (default is "en"). Use ISO 639-1 codes.

    Returns:
        dict: A dictionary containing the label and description of the entity, if available.
    """
    params = {
        "action": "wbgetentities",
        "ids": entity_id,
        "props": "labels|descriptions",
        "languages": language,  # specify the desired language
        "format": "json",
    }
    async with httpx.AsyncClient() as client:
        response = await client.get(WIKIDATA_URL, params=params)
    response.raise_for_status()
    data = response.json()
    entity_data = data.get("entities", {}).get(entity_id, {})
    label = (
        entity_data.get("labels", {}).get(language, {}).get("value", "No label found")
    )
    descriptions = (
        entity_data.get("descriptions", {})
        .get(language, {})
        .get("value", "No label found")
    )
    return {"Label": label, "Descriptions": descriptions}


if __name__ == "__main__":
    server.run()
