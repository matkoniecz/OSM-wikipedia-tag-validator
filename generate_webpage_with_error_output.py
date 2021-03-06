import argparse
import yaml
import os.path
import common
import datetime

def main():
    args = parsed_args()
    generate_html_file(args, "", for_review(), "Remember to check whatever edit makes sense! All reports are at this page because this tasks require human judgment to verify whatever proposed edit makes sense.")
    generate_html_file(args, " - boring", for_review_boring(), "Remember to check whatever edit makes sense! All reports are at this page because this tasks require human judgment to verify whatever proposed edit makes sense.")
    generate_html_file(args, " - obvious", obvious_fixes(), "Proposed edits at this page are so obvious that automatic edit makes sense.")
    generate_html_file(args, " - test", for_tests(), "This page contains reports that are tested or are known to produce false positives. Be careful with using this data.")
    note_unused_errors(args)

def generate_html_file(args, name_suffix, types, information_header):
    #print(args.out + name_suffix + '.html')
    with open(args.out + name_suffix + '.html', 'w') as file:
        file.write(object_list_header())
        file.write(table_row( '==========' ))
        file.write(table_row( information_header ))
        file.write(table_row( '==========' ))
        #print("LOADING ERRORS START")
        reported_errors = sorted(get_errors(args), key=lambda error: error['osm_object_url'])
        #print("LOADING ERRORS END")
        for error_type_id in types:
            #print(error_type_id)
            error_count = 0
            for e in reported_errors:
                if e['error_id'] == error_type_id:
                    if error_count == 0:
                        file.write(table_row( '<h2>' + error_type_id + '</h2>'))
                    error_count += 1
                    file.write(error_description(e))
            if error_count != 0:
                file.write(table_row( 'overpass query usable in JOSM that will load all objects with this error type:' ))
                query = common.get_query_for_loading_errors_by_category(filename = args.file, printed_error_ids = [error_type_id], format = "josm")
                file.write(table_row(common.escape_from_internal_python_string_to_html_ascii(query)))
                file.write(table_row( '==========' ))

        file.write("</table>")
        file.write("</body>")
        file.write("</html>")
        
def contact_url():
    return "https://www.openstreetmap.org/message/new/Mateusz%20Konieczny"

def contact_html_prefix():
    return "<a href=\"" + contact_url() + "\">"

def contact_html_suffix():
    return "</a>"

def send_me_a_message_html():
    return contact_html_prefix() + "send me a message" + contact_html_suffix()

def feedback_header():
    return "Feedback? Ideas? Complaints? Suggestions? Request for report about other area? " + send_me_a_message_html() + "!"

def timestamp():
    return "This page was generated on " + str(datetime.date.today()) + ". Please, " + send_me_a_message_html() + " if you want it updated!" 

def feedback_request():
    returned = ""
    returned += feedback_header()
    returned += "<br />\n"
    returned += timestamp()
    returned += "<br />\n"
    return returned

def object_list_header():
    returned = ""
    returned += "<html>\n"
    returned += "<body>\n"
    returned += feedback_request()
    returned += "<br />\n"
    returned += "---------------\n"
    returned += "<br />\n"
    returned +=  "<table>\n"
    return returned

def link_to_osm_object(url):
    return '<a href="' + url + '" target="_new">Affected OSM element that may be improved</a>'

def article_name_from_wikipedia_string(string):
    return string[string.find(":")+1:]

def language_code_from_wikipedia_string(string):
    return string[0:string.find(":")]

def format_wikipedia_link(string):
    if string == None:
        return "?"
    language_code = language_code_from_wikipedia_string(string)
    language_code = common.escape_from_internal_python_string_to_html_ascii(language_code)
    article_name = article_name_from_wikipedia_string(string)
    article_name = common.escape_from_internal_python_string_to_html_ascii(article_name)
    return '<a href="https://' + language_code + '.wikipedia.org/wiki/' + article_name + '" target="_new">' + language_code+":"+article_name + '</a>'

def table_row(text):
    returned = ""
    returned += "<tr>\n"
    returned += "   <td>\n"
    returned += "       " + text + "\n"
    returned += "   </td>\n"
    returned += "</tr>\n"
    return returned

def parsed_args():
    parser = argparse.ArgumentParser(description='Production of webpage about validation of wikipedia tag in osm data.')
    parser.add_argument('-file', '-f', dest='file', type=str, help='name of yaml file produced by validator, consumed by this generator')
    parser.add_argument('-out', '-o', dest='out', type=str, help='main name part of html file (parameter should be without html extension).')
    args = parser.parse_args()
    if not (args.file):
        parser.error('Provide yaml file generated by wikipedia validator')
    return args

def get_errors(args):
    filepath = common.get_file_storage_location()+"/"+args.file
    if not os.path.isfile(filepath):
        print(filepath + " is not a file, provide an existing file")
        return []
    return common.load_data(filepath)

def error_description(e):
    returned = ""
    returned += table_row(common.htmlify(e['error_message']))
    returned += table_row(link_to_osm_object(e['osm_object_url']))
    if e['desired_wikipedia_target'] != None:
        returned += describe_proposed_relinking(e)
    returned += table_row( '-------' )
    return returned

def describe_proposed_relinking(e):
    returned = ""
    current = format_wikipedia_link(e['current_wikipedia_target'])
    to = format_wikipedia_link(e['desired_wikipedia_target'])
    if to == current:
        to = "?"
    returned += table_row( current + " -> " + to)
    if to != "?":
        article_name = article_name_from_wikipedia_string(e['desired_wikipedia_target'])
        returned += table_row( common.escape_from_internal_python_string_to_html_ascii(article_name))
    return returned

def note_unused_errors(args):
    reported_errors = get_errors(args)
    for e in reported_errors:
        if e['error_id'] in for_review():
            continue
        if e['error_id'] in for_review_boring():
            continue
        if e['error_id'] in obvious_fixes():
            continue
        if e['error_id'] in for_tests():
            continue
        print('"' + e['error_id'] + '" is not appearing in any generated webpage')

def for_review():
    return [
        'wikipedia tag in outdated form and there is mismatch between links',
        'wikipedia tag links to 404',
        'wikidata tag links to 404',
        'link to an unlinkable article',
        'wikipedia wikidata mismatch',
        'tag may be added based on wikidata',
        'tag may be added based on wikidata - teryt',
        'invalid old-style wikipedia tag',
        'malformed wikidata tag',
        'malformed wikipedia tag',
        'should use a secondary wikipedia tag',
        'link to a list',
    ]

def for_review_boring():
    return [
        'tag may be added based on wikidata - website',
    ]

def obvious_fixes():
    return [
        'blacklisted connection with known replacement',
        'wikipedia tag unexpected language',
        'wikipedia tag from wikipedia tag in an outdated form',
        'wikipedia wikidata mismatch - follow wikipedia redirect',
        'wikipedia from wikidata tag',
        'wikipedia from wikidata tag, unexpected language',
        'wikidata from wikipedia tag',
        'wikipedia tag in an outdated form for removal',
        'wikipedia tag from wikipedia tag in an outdated form and wikidata',
    ]

def for_tests():
    return [
        'wikipedia wikidata mismatch - follow wikidata redirect',
        'no longer existing object',
        'tag conflict with wikidata value',
        'tag conflict with wikidata value - testing',
        'wikipedia tag unexpected language, article missing',
        'tag conflict with wikidata value - boring',
    ]

if __name__ == "__main__":
    main()
