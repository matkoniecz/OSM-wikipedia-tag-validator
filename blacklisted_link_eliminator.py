import os
import osm_bot_abstraction_layer.osm_bot_abstraction_layer as osm_bot_abstraction_layer
import wikimedia_connection.wikimedia_connection as wikimedia_connection
import osm_handling_config.global_config as osm_handling_config
from osm_iterator.osm_iterator import Data
import wikimedia_link_issue_reporter
import common

def main():
    os.system('python3 generate_query_for_blacklisted_wikimedia_links.py > generated_query_for_blacklisted_entries.generated_query')
    os.system('ruby download.rb')

    wikimedia_connection.set_cache_location(osm_handling_config.get_wikimedia_connection_cache_location())

    offending_objects_storage_file = common.get_file_storage_location()+"/"+'objects_with_blacklisted_links.osm'
    print(offending_objects_storage_file)

    osm = Data(offending_objects_storage_file)
    osm.iterate_over_data(cache_data)
    osm.iterate_over_data(eliminate_blacklisted_links)

def blacklist():
    return wikimedia_link_issue_reporter.WikimediaLinkIssueDetector().wikidata_connection_blacklist()

def is_human_confirming():
    choice = input().lower()
    if choice == "y":
        return True
    return False

def try_prefixifying(data, tag, blacklist_entry):
    try:
        data['tag'][tag]
    except KeyError:
        return data
    else:
        data['tag'][blacklist_entry['prefix'] + tag] = data['tag'][tag]
        del data['tag'][tag]
        print("prefixified " + tag + " with " + blacklist_entry['prefix'])
    return data

def make_an_edit(data, link, blacklist_entry):
    data = try_prefixifying(data, 'wikidata', blacklist_entry)
    data = try_prefixifying(data, 'wikipedia', blacklist_entry)
    automatic_status = osm_bot_abstraction_layer.manually_reviewed_description()
    source = "general knowlege, checking link target"
    comment = "fixing a link to Wikipedia. In wikipedia/wikidata tags only entries about given feature should be linked. See https://wiki.openstreetmap.org/wiki/Key:wikipedia"
    discussion_url = None
    type = link.split("/")[3]
    print(data['tag'])
    osm_bot_abstraction_layer.make_edit(link, comment, automatic_status, discussion_url, type, data, source, 0)

def request_decision_from_human(data, link, blacklist_entry):
    wikidata_id = data['tag']['wikidata']
    print("relink to " + blacklist_entry['prefix'] + " ? [y/n]")
    if is_human_confirming():
        make_an_edit(data, link, blacklist_entry)

def initial_verification(element):
    global data_cache
    # TODO support entries without wikidata
    # TODO verify whatever wikipedia-wikidata matches
    # TODO verify whaver it is using old style wikipedia tags
    # TODO verify structural issues like this using validator
    # TODO package getting effective_wikidata into a function
    effective_wikidata = element.get_tag_value('wikidata')
    blacklist_entry = None
    try:
        blacklist_entry = blacklist()[effective_wikidata]
    except KeyError as e:
        return None

    prerequisites = {}
    for key in element.get_keys():
        prerequisites[key] = element.get_tag_value(key)
    if element.get_link() in data_cache:
        return data_cache[element.get_link()]
    data = osm_bot_abstraction_layer.get_and_verify_data(element.get_link(), prerequisites)
    if data == None:
        return None
    data_cache[element.get_link()] = data
    return data

def eliminate_blacklisted_links(element):
    data = initial_verification(element)
    if data == None:
        return

    effective_wikidata = element.get_tag_value('wikidata')
    blacklist_entry = blacklist()[effective_wikidata]

    print()
    print(element.get_link())
    for key, value in data['tag'].items():
        print(key, "=", value)

    for tag, expected_value in blacklist_entry['expected_tags'].items():
        if expected_value != data['tag'][tag]:
            print("for " + tag + " " + expected_value + " was expected, got " + data['tag'][tag])
            request_decision_from_human(data, element.get_link(), blacklist_entry)
            return

    request_decision_from_human(data, element.get_link(), blacklist_entry)


def cache_data(element):
    initial_verification(element)

data_cache = {}
main()