"""
This module defines the `main()` coroutine for the Apify Actor, executed from the `__main__.py` file.

Feel free to modify this file to suit your specific needs.

To build Apify Actors, utilize the Apify SDK toolkit, read more at the official documentation:
https://docs.apify.com/sdk/python
"""

import traceback

from urllib.parse import urljoin

from bs4 import BeautifulSoup
from httpx import AsyncClient

from apify import Actor
from apify_shared.consts import ActorExitCodes


BASE_URL = "https://www.avx.io/sectors/physical-sciences"


async def main() -> None:
    """
    The main coroutine is being executed using `asyncio.run()`, so do not attempt to make a normal function
    out of it, it will not work. Asynchronous execution is required for communication with Apify platform,
    and it also enhances performance in the field of web scraping significantly.
    """
    async with Actor:
        # Read the Actor input
        actor_input = await Actor.get_input() or {}
        # start_urls = actor_input.get('start_urls', [{'url': 'https://apify.com'}])
        # max_depth = actor_input.get('max_depth', 1)

        # Fetch the content from the URL
        try:
            async with AsyncClient() as client:
                response = await client.get(BASE_URL, follow_redirects=True)
                response.raise_for_status()
        except:
            e = Exception("The website is changed!")
            await Actor.fail(exit_code=ActorExitCodes.ERROR_USER_FUNCTION_THREW, exception=e)
            return

        # Parse the HTML content
        soup = BeautifulSoup(response.content, 'html.parser')

        # Select all the elements that match the CSS selector
        elements_list = soup.select("body > div.section > div > div.venture-list > div > div.w-dyn-items > div")
        
        Names, Solutions, Websites, Institutions = False, False, False, False

        # Iterate over each element in the list
        for element in elements_list:
            try:
                # Extract company name
                company_name_element = element.select_one("h4.venture-title")
                companyName = company_name_element.text.strip() if company_name_element else ""

                # Extract affiliated institution
                affiliated_institution_element = element.select_one("div.sub-category-text")
                affiliatedInstitution = (
                    affiliated_institution_element.text.strip()
                    if
                    affiliated_institution_element
                    else
                    ""
                )

                # Extract company solution
                company_solution_element = element.select_one("p.paragraph-4")
                companySolution = company_solution_element.text.strip() if company_solution_element else ""

                # Extract company website
                website_img_elements = element.select('img[src*=Homepage]')
                if website_img_elements:
                    parent_anchor = website_img_elements[0].find_parent('a')
                    companyWebsite = parent_anchor['href'] if parent_anchor else ""
                else:
                    companyWebsite = ""

                # Extract other link
                venture_wrapper_element = element.select_one("a.venture-wrapper")
                otherLink = urljoin(BASE_URL, venture_wrapper_element['href']) if venture_wrapper_element else ""

                # Print the extracted information
                Actor.log.info(f"Company Name: {companyName}, Affiliated Institution: {affiliatedInstitution}, "
                    f"Company Solution: {companySolution[:20]}..., "
                    f"Company Website: {companyWebsite}, Other Link: {otherLink}")
                
                await Actor.push_data(
                    {
                        "companyName": companyName,
                        "affiliatedInstitution": affiliatedInstitution,
                        "companySolution": companySolution,
                        "companyWebsite": companyWebsite,
                        "otherLink": otherLink,
                    }
                )

                Names = True if companyName else Names
                Solutions = True if companySolution else Solutions
                Websites = True if companyWebsite else Websites
                Institutions = True if affiliatedInstitution else Institutions

            except Exception as ex:
                # Handle exceptions and print an error message
                Actor.log.exception(f'Error {str(ex)}.\n{traceback.format_exc()}')

                
        if not (Names and Solutions and Websites and Institutions):
            e = Exception("The website is changed!")
            await Actor.fail(exit_code=ActorExitCodes.ERROR_USER_FUNCTION_THREW, exception=e)
