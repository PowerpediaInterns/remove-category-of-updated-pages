import pywikibot
import requests
import datetime
import urllib3

# Template to append to pages
TEMPLATE = "{{Update Needed}}"
# Max time a page can be unedited before being tagged; timedelta object
# https://docs.python.org/3/library/datetime.html#timedelta-objects for details on working with timedelta objects
AGE_CAP = datetime.timedelta(days=30)

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

BATCH_SIZE = 2

def get_api_url() -> str:
	"""
	Retrieves the API URL of the wiki

	:return: String of the path to the API URL of the wiki
	"""

	site = pywikibot.Site()
	url = site.protocol() + "://" + site.hostname() + site.apipath()
	return url


def get_new_pages(url, continue_from="") -> "Page Generator":
	"""
	Retrieves a Page Generator with all old pages to be tagged

	:param url: String of the path to the API URL of the wiki
	:param continue_from: String of page title to continue from; defaults to beginning of wiki
	:return: returns a tuple with a Page Generator and the lowest page title based on alphabetical order
	"""

	# Retrieving the pages to sort
	params = {
		"action": "query",
		"format": "json",
		"prop": "revisions",
		"generator": "allpages",
		"rvprop": "timestamp",
		"gapcontinue": continue_from,
		"gaplimit": BATCH_SIZE
	}

	session = requests.Session()
	request = session.get(url=url, params=params, verify=False)
	pages_json = request.json()

	# Sorting through all the pages
	new_pages = []
	pages_to_sort = pages_json["query"]["pages"]
	print(pages_to_sort)

	current_time = datetime.datetime.utcnow().replace(microsecond=0)
	print("Current time:", current_time)
	print()

	lowest_title = " "

	for page in pages_json["query"]["pages"]:
		curr_title = pages_json["query"]["pages"][page]["title"]
		curr_timestamp = pages_json["query"]["pages"][page]["revisions"][0]["timestamp"]
		print("Evaluating '%s' - '%s' with last edit on '%s'" % (page, curr_title, curr_timestamp))

		timestamp_datetime = datetime.datetime.strptime(curr_timestamp, "%Y-%m-%dT%H:%M:%SZ")
		print("Timestamp of last edit:", timestamp_datetime)

		difference = current_time - timestamp_datetime
		print("Amount of time since last edit:", difference)

		if difference < AGE_CAP:
			print("'%s' will be untagged with '%s'" % (curr_title, strip(TEMPLATE)))
			new_pages.append(curr_title)

		# To get lowest title alphabetically
		if lowest_title < curr_title:
			lowest_title = curr_title

		print()
	print("Lowest title found:", lowest_title)

	return new_pages, lowest_title


def remove_template(pages) -> None:
	"""
	Removes the instance variable TEMPLATE to the parameter pages

	:param pages: pages to be modified; consists of titles
	:return: None
	"""

	site = pywikibot.Site()
	for title in pages:
		page = pywikibot.Page(site, title)
		page_text = page.text

		if page_text.find(TEMPLATE) == -1:
			print("'%s' is in '%s'... Removing" % (TEMPLATE, page))
			page_text = u'\n\n'.strip((TEMPLATE, page_text)) #removes TEMPLATE from page
			page.text = page_text
			page.save(u"Tag Removed: " + strip(TEMPLATE), botflag=True)
		else:
			print("'%s' already removed '%s'... Skipping." % (TEMPLATE, page))


def main() -> None:
	"""
	Driver. Retrieves old pages that haven't been updated in AGE_CAP time and then tags them with TEMPLATE
	"""

	url = get_api_url()
	print(url)

	new_pages_tuple = get_new_pages(url)
	pages = new_pages_tuple[0]
	continue_from = new_pages_tuple[1]

	while len(pages) > 1:
		print("Pages to be untagged:", pages)
		remove_template(pages)
		print("Continuing from:", continue_from)
		new_pages_tuple = get_new_pages(url, continue_from)
		pages = new_pages_tuple[0]
		continue_from = new_pages_tuple[1]

	print("No pages left to be untagged")


if __name__ == '__main__':
	main()

