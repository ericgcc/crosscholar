# Python imports
import datetime
from html import unescape
from difflib import SequenceMatcher
from re import search, sub, findall
from time import strftime
from csv import reader
from typing import List, Tuple, Dict, BinaryIO
from time import sleep
from math import ceil
from os.path import basename, exists, getsize
import traceback
import smtplib

# Vendor imports
import requests
from habanero import Crossref
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import ElementClickInterceptedException
from urllib.parse import quote_plus

# Crosscholar modules imports
from urlman import URLFactory, ScholarURLType
from scholarbase import Work, User
from timer import Requestmeter
from config import Configuration

# Configuring app
config = Configuration('crosscholar.toml')

# region Adaptive Request Rate
requestmeter = Requestmeter(config.limits)
pause = False  # This flag will slow down the request speed


def s_adaptive_request_rate(compensation_time):
    global pause
    pause = True  # Wait 'till compensation time is elapsed
    print(f".:WAITING: {compensation_time} s:.")
    sleep(compensation_time)
    requestmeter.timer.elapsed_seconds += ceil(compensation_time)
    pause = False  # Continue requesting


def m_adaptive_request_rate(compensation_time):
    global pause
    print(f".:WAITING: {compensation_time} m:.")
    compensation_time *= 60
    pause = True  # Wait 'till compensation time is elapsed
    sleep(compensation_time)
    requestmeter.timer.elapsed_minutes += ceil(compensation_time / 60)
    pause = False  # Continue requesting


def h_adaptive_request_rate(compensation_time):
    global pause
    print(f".:WAITING: {compensation_time} h:.")
    compensation_time *= 3600
    pause = True  # Wait 'till compensation time is elapsed
    sleep(compensation_time)
    requestmeter.timer.elapsed_hours += ceil(compensation_time / 3600)
    pause = False  # Continue requesting


# Event subscriptions
requestmeter.events.s_speed_limit_exceeded = s_adaptive_request_rate
requestmeter.events.m_speed_limit_exceeded = m_adaptive_request_rate
requestmeter.events.h_speed_limit_exceeded = h_adaptive_request_rate


# endregion Adaptive Request Rate

# region Scraper functions
def gsc_users(soup: BeautifulSoup) -> List[User]:
    """Parses the Google Scholar citations view.

    This view shows a list of authors(users) related to a keyword search, i.e., if the keyword is "MIT", this page
    shows a list of authors(users) who are related to the term "MIT".

    The url is something like this:
    https://scholar.google.com.mx/citations?hl=en&view_op=search_authors&mauthors=<keywords>

    Parameters
    ----------
    soup : BeautifulSoup
        The HTML soup for the citations page (a list of users) related to a term that this function will parse.

    Returns
    -------
    list
        A list with users' (authors) data.

    """

    users = []

    if soup.find('div', id='gsc_sa_ccl'):
        users_soup = soup.find_all('div', class_='gsc_1usr gs_scl')
        for user in users_soup:
            u = User()
            u['avatar'] = ScholarURLType.BASE.value + user.find(class_='gsc_1usr_photo').img['src']

            u['page'] = URLFactory(type_=ScholarURLType.CITATIONS_USER,
                                   url=ScholarURLType.BASE.value +
                                       user.find(class_='gsc_oai').h3.a['href'])

            u['id'] = search(r"user=(.*)&hl", u['page'].url).group(1)

            try:
                u['name'] = user.find(class_='gsc_oai').h3.a.string.title()
            except AttributeError:
                markup = user.find(class_='gsc_oai_name')
                name_tag = None

                while markup.a.find(class_='gs_hlt') is not None:
                    name_tag = markup.a
                    name_tag.span.unwrap()
                u['name'] = name_tag.get_text()

            u['affiliation'] = ' '.join(
                user.find(class_='gsc_oai_aff').find_all(text=True))

            try:
                # Searching just fot the number in this string to get citations count
                u['citations_count'] = int(findall(r"\d+", user.find(class_='gsc_oai_cby').string)[0])
            except TypeError:
                u['citations_count'] = 0

            users.append(u)

        return users


def gsc_user_citations_graph(soup: BeautifulSoup, user: User) -> None:
    """Parses the Google Scholar user citations graph.

    This view shows a list of the documents of a specific author (user) and the citations graph
    for that user.

    The url is something like this:
    https://scholar.google.com.mx/citations?hl=en&user=<id>

    Parameters
    ----------
    soup : BeautifulSoup
        The HTML soup for the user citations where is the graph that this function will parse.

    user : User
        The user for whom we want to obtain the graph.

    """

    citations_per_year = {}

    if soup.find('div', class_='gsc_md_hist_b'):
        years = soup.find_all('span', class_='gsc_g_t')
        counts = soup.find_all('a', class_='gsc_g_a')

        for (year, count) in zip(years, counts):
            citations_per_year[year.string] = count.span.string

        user.__setitem__('citations_per_year', citations_per_year)


def gsc_work_citations_graph(soup: BeautifulSoup) -> Dict:
    """Parses the Google Scholar user citations graph.

    This view shows a list of the documents of a specific author (user) and the citations graph
    for that user.

    The url is something like this:
    https://scholar.google.com.mx/citations?hl=en&user=<id>

    Parameters
    ----------
    soup : BeautifulSoup
        The HTML soup for the user citations where is the graph that this function will parse.

    """

    citations_per_year = {}

    if soup.find('div', id='gsc_vcd_graph_bars'):
        years = soup.find_all('span', class_='gsc_vcd_g_t')
        counts = soup.find_all('a', class_='gsc_vcd_g_a')

        for (year, count) in zip(years, counts):
            citations_per_year[year.string] = count.span.string

        return citations_per_year


def gsc_user_works(soup: BeautifulSoup, user: User, file: BinaryIO, browser: webdriver = None,
                   start_in_work: int = None) -> int:
    """Parses the Google Scholar citations per user page.

    This view shows a list of the documents of a specific author (user) and the citations graph
    for that user.

    The url is something like this:
    https://scholar.google.com.mx/citations?hl=en&user=<id>

    Parameters
    ----------
    soup : BeautifulSoup
        The HTML soup for the citations/user page (documents) for a particular user (author) that this function will
        parse.

    user : User
        The user related to these documents.

    file : object
        The file object where the program will write the results.

    browser : webdriver
        The browser that is used to extract the works.

    start_in_work : int
        When batch processing is used, this parameter indicates in which work start to parse.

    Returns
    -------
    int
        Total documents parsed.

    """

    if soup.find('tbody', id='gsc_a_b'):
        works_soup = soup.find_all('tr', class_='gsc_a_tr')
        counter = 1
        record = 1
        for work in works_soup:

            # Batch processing: Start to parse in the work (position) specified
            if start_in_work is not None and record < start_in_work:
                record += 1
                continue

            w = Work()
            w['user_id'] = user['id']
            w['gsc_title'] = sub(r"\s", ' ', sub(r"\s+", ' ', work.find(class_='gsc_a_t').a.text)).strip()

            href = quote_plus(work.find(class_='gsc_a_t').a['data-href'].replace("&pagesize=100", ""))
            w['url'] = f"{user['page'].url}#d=gs_md_cita-d&p=&u={href}%26tzom%3D360"

            extra_data = work.find_all(class_="gs_gray")
            w['authors'] = extra_data[0].string

            try:
                w['citations_count'] = int(work.find(class_='gsc_a_c').a.string)
            except Exception:
                w['citations_count'] = 0

            try:
                citations_url = (work.find(class_='gsc_a_c').a['href']).strip()
                w['citations_url'] = citations_url if citations_url else None
            except Exception:
                w['citations_url'] = None

            try:
                w['id'] = search(r"cites=(.*)$", w['citations_url']).group(1)
            except Exception:
                w['id'] = None

            try:
                # TODO: Check if this condition works
                w['gsc_publication'] = extra_data[1].text if not extra_data[1].text else None
            except Exception:
                w['gsc_publication'] = None

            try:
                w['year'] = work.find(class_='gsc_a_y').span.string
            except Exception:
                w['year'] = None
            gsc_work_details(work_details_request(browser, w['gsc_title']), w)

            if config.crossref:
                crf_work_details(w, user)

            gsc_work_wos_citations(browser, w)

            # Printing and saving to file
            print(f"In work: {record} >>> {w.as_csv()}\n")
            file.write((w.as_csv() + "\n").encode())
            counter += 1
            record += 1

        return counter


def gsc_work_wos_citations(browser: webdriver, work: Work) -> None:
    soup = work_wos_citations_request(browser, work['gsc_title'])  # send request and get the page source

    if soup.find('div', id='gs_res_ccl_mid') and soup.find('div', class_='gs_r gs_or gs_scl'):
        results = soup.find_all('div', class_='gs_r gs_or gs_scl')

        for result in results:
            h3 = result.find('h3', class_="gs_rt")

            if h3.find("a"):
                h3 = h3.a

            search_title = sub(r"\s", ' ', sub(r"\s+", ' ', h3.text))
            search_title = sub(r"\[.*\]", '', search_title).strip().lower()
            profile_title = work['gsc_title'].lower()

            if search_title is not None and SequenceMatcher(None, profile_title, search_title).ratio() >= 0.9:
                wos = result.find('a', class_='gs_nta gs_nph')
                work['wos_citations_count'] = wos.string.replace('Web of Science:', '').strip() if wos is not None else wos
                work['wos_citations_url'] = wos['href'] if wos is not None else wos
                print("WOS: ", work['wos_citations_count'], sep=" ")
                break
            else:
                logging_collector("INFO", "TITLE MISMATCH",
                                  [profile_title,  # Title in profile
                                   search_title,  # Title in search
                                   SequenceMatcher(None, profile_title, search_title).ratio()])  # Coincidence

    sleep(0.5)
    browser.close()  # close the tab
    sleep(0.5)
    browser.switch_to.window(browser.window_handles[0])  # return to the main tab


def crf_work_details(work: Work, user: User) -> None:
    """Completes the data of a document using crossref API.

    We do this to make less requests to Google Scholar and to get the DOI.

    Parameters
    ----------
    work : Work
        The work to get the data.

    user : User
        The user (author) of de document.

    """
    print(">>> Entering crf")
    print("Title:", work['gsc_title'])

    # Init habanero object
    crossref = Crossref(mailto=config.crossref_to)
    d = crossref.works(query_title=work['gsc_title'])

    try:
        items = d['message']['items']

        # Removing all unnecessary characters to make a title comparision
        regex = r"[^0-9a-zA-ZáàâäéèêëíìîïóòôöúùûüñçÿæœßÁÀÂÄÉÈËÊÍÎÌÏÓÒÔÖÚÙÛÜÑÇŸÆŒẞ]"
        gsc_title = sub(regex, '', unescape(work['gsc_title'].lower()))

        match_ratio = 1

        # Search first for a perfect match: this is a loop
        details = next((item for item in items if
                        sub(regex, '', unescape(item['title'][0].lower())) ==
                        gsc_title), None)

        # If there isn't a perfect match, search for an approximation
        if details is None:
            found = [False, False]

            for item in items:

                crf_title = sub(regex, '', unescape(item['title'][0].lower()))
                crf_title = sub(r"\s", ' ', sub(r"\s+", ' ', crf_title)).strip()
                match_ratio = SequenceMatcher(None, crf_title, gsc_title).ratio()

                if match_ratio >= 0.75:
                    details = item
                    found[0] = True

                    authors = details['author'] if 'author' in details else []
                    gsc_name = user['name'].lower()

                    for author in authors:

                        if {'given', 'family'} <= set(author):
                            crf_name = f"{author['given']} {author['family']}".lower()
                        elif 'given' in author:
                            crf_name = f"{author['given']}".lower()
                        elif 'family' in author:
                            crf_name = f"{author['family']}".lower()
                        else:
                            continue

                        name_ratio = SequenceMatcher(None, crf_name, gsc_name).ratio()

                        if name_ratio >= 0.69:
                            found[1] = True
                            break
                    break

            if not (found[0] and found[1]):
                print("<<< Leaving crf")
                return

    except IndexError:
        print("<<< Leaving crf")
        return

    work['match_ratio'] = match_ratio

    if work['match_ratio'] < 1:
        # Removing any extra unnecessary blanks and replacing any blank for a single space
        work['crf_title'] = sub(r"\s", ' ', sub(r"\s+", ' ', details['title'][0]))

    if work['volume'] is None:
        if 'volume' in details:
            work['volume'] = details['volume']

    if work['issue'] is None:
        if 'issue' in details:
            work['issue'] = details['issue']

    if work['pages'] is None:
        if 'page' in details:
            work['pages'] = details['page']

    if 'DOI' in details:
        work['doi'] = details['DOI']

    if 'container-title' in details:
        # Removing any extra unnecessary blanks and replacing any blank for a single space
        work['crf_publication'] = sub(r"\s", ' ', sub(r"\s+", ' ', details['container-title'][0]))

    if 'type' in details:
        work['crf_type'] = details['type']

    print("<<< Leaving crf")


def gsc_work_details(soup: BeautifulSoup, work: Work) -> None:
    """Gets a document details from Google Scholar ajax modal.

    Parameters
    ----------
    soup : BeautifulSoup
        The HTML soup for the details modal for a particular work that this function will
        parse.

    work : Work
        The url of the work from which we want to get the details.

    """

    if soup is None:
        return

    details = dict()

    if soup.find('div', id='gsc_vcd_table'):
        details_soup = soup.find_all('div', class_='gs_scl')

        for detail in details_soup:
            try:
                field = detail.find(class_='gsc_vcd_field').string
                if field in {'Publication date', 'Publisher', 'Description', 'Scholar articles'}:
                    continue

                details[field] = detail.find(class_='gsc_vcd_value').string if field != 'Total citations' else \
                    detail.find(class_='gsc_vcd_value')

            except AttributeError:
                pass

        # If a detail is the dictionary of details, add it to the work, and then remove the detail from the dict
        work['authors'] = details['Authors'] if 'Authors' in details else None
        details.pop('Authors', None)

        patent = False
        if 'Inventors' in details:
            work['authors'] = details['Inventors']
            patent = True
            details.pop('Inventors', None)

        work['pages'] = details['Pages'] if 'Pages' in details else None
        details.pop('Pages', None)

        work['volume'] = details['Volume'] if 'Volume' in details else None
        details.pop('Volume', None)

        work['issue'] = details['Issue'] if 'Issue' in details else None
        details.pop('Issue', None)

        if 'Total citations' in details:
            work['citations_per_year'] = gsc_work_citations_graph(details['Total citations'])
        details.pop('Total citations', None)

        # At this point, if the dict still has an element, this must be the work type with the publication title,
        # so get them. This way we don't restrict the types to a set of "predefined types", we take any string
        # that Google provides as type.
        if patent:
            work['gsc_type'] = 'Patent'  # This string represents the work type
            work['gsc_publication'] = None  # This one represents the publication title
        elif details.items():
            work['gsc_type'] = list(details.items())[0][0]  # This string represents the work type
            work['gsc_publication'] = list(details.items())[0][1]  # This one represents the publication title


# endregion

# region Request functions
def wait():
    while pause:
        continue


def beautifulsoup_request(target: str) -> BeautifulSoup:
    wait()  # Waiting for the adaptive request rate
    r = requests.get(target)  # requests.get(url)
    requestmeter.count()
    html_ = r.content
    return BeautifulSoup(html_, 'html.parser')


def display_user_page_request(browser: webdriver, target: str) -> None:
    wait()  # Waiting for the adaptive request rate
    browser.get(target)
    requestmeter.count()


def display_all_user_works_requests(browser: webdriver) -> None:
    is_enable = browser.find_element_by_id('gsc_bpf_more').is_enabled()
    while is_enable:
        wait()  # Waiting for the adaptive request rate
        browser.find_element_by_id('gsc_bpf_more').click()
        requestmeter.count()
        sleep(0.5)
        is_enable = browser.find_element_by_id('gsc_bpf_more').is_enabled()


def work_details_request(browser: webdriver, title: str) -> BeautifulSoup:
    wait()
    try:
        work = browser.find_element_by_link_text(title)

        # Waiting 'till link is clickable
        while True:
            try:
                work.click()
                break
            except ElementClickInterceptedException:
                continue

        requestmeter.count()
        sleep(0.5)  # This delay permits the html display entirely
        html_ = browser.page_source
        close_button = browser.find_element_by_id('gs_md_cita-d-x')
        close_button.click()
    except Exception as err:
        print("!!!>>>", title)
        print(err)

        logging_collector("ERROR", "NOT CLICKABLE LNK",
                          [browser.find_element_by_id('gsc_prf_in').text,  # Author
                           title,  # Title
                           err])  # Error
        return None

    return BeautifulSoup(html_, 'html.parser')


def work_wos_citations_request(browser: webdriver, title: str):
    url = ScholarURLType.BASE.value + ScholarURLType.SEARCH.value.replace('<title>', title).replace('"', '\\"')

    wait()
    browser.execute_script(f"""window.open("{url}","_blank");""")  # request
    WebDriverWait(browser, 10).until(EC.number_of_windows_to_be(2))
    requestmeter.count()

    browser.switch_to.window(browser.window_handles[1])  # changes to the new tab
    WebDriverWait(browser, 10).until(EC.presence_of_element_located((By.NAME, 'q')))
    search_box = browser.find_element_by_name('q')  # gets the search box
    search_box.send_keys(title)  # puts the query
    search_box.submit()  # send the request

    WebDriverWait(browser, 10).until(EC.presence_of_element_located((By.NAME, 'q')))

    return BeautifulSoup(browser.page_source, 'html.parser')


# endregion Request functions

def download_users(keywords: str) -> Tuple[str, int]:
    """Downloads a list of users based on some keywords sent to Google Scholar.

    Parameters
    ----------
    keywords : str
        Search criteria send to Google Scholar.

    Returns
    -------
    str
        The name of the file where the results were saved.

    int
        The number of users in the batch.

    """

    # Page counter
    page = 1

    # Page where is the list of authors
    citations_page = URLFactory(ScholarURLType.CITATIONS, keywords)
    print(citations_page.generate())

    # HTML of the list of authors
    users_soup = beautifulsoup_request(citations_page.generate())  # request(citations_page.generate())

    # All the authors
    users_list = []

    while True:
        print(f"--- PAGE {page} ---")
        users = gsc_users(users_soup)
        users_list.extend(users)

        for user in users:
            print(user.as_csv() + "\n")

        if users_soup.find('button', attrs={'aria-label': 'Next'}) is None or \
                users_soup.find('button', attrs={'aria-label': 'Next'}).has_attr('onclick') is not True:
            break

        users_soup = beautifulsoup_request(citations_page.next_url(users_soup))  # request(citations_page.next_url(users_soup))
        page += 1

    batch_name = config.download_dir + f"users_batch_{strftime('%y%m%d')}_{strftime('%I%M%S')}.csv"

    with open(batch_name, 'wb') as users_batch_file:
        # Writing header
        users_batch_file.write((User().keys() + "\n").encode())
        for user in users_list:
            print("*****************")

            citations_user_page = user['page']
            works_soup = beautifulsoup_request(citations_user_page.url)  # request(citations_user_page.url)

            gsc_user_citations_graph(works_soup, user)
            print(user.as_csv())
            users_batch_file.write((user.as_csv() + "\n").encode())

    print("Total users: ", len(users_list))

    return batch_name, len(users_list)


def download_works(users_batch_path: str, *slices, start_in_user: int = None, start_in_work: int = None) -> None:
    """Downloads works from Google Scholar for specific users.

    Downloads the works of the users indicated from the `start` to the `stop` positions in the `user_batch_file.

    Parameters
    ----------
    slices : object
    users_batch_path : str
        The URI to the `user_batch_file` generated by the `download_users` function.

    start_in_work : int
        Start processing in this specified line (user).

    start_in_user : int
        Propagate this value to start processing in this specified work.

    See Also
    --------
    download_users :  Downloads a list of users from Google Scholar.

    """
    # Configuring batch processing
    users = slice_users(users_batch_path, slices, start_in_user)

    # region Configuring batch file name
    # Converting tuple to suffix for name the file
    if not slices:
        suffix = "full"
    else:
        suffix = str(slices).replace(' ', '').replace('(', '', 1)
        suffix = suffix[:suffix.rfind(')')]
        suffix = suffix[:suffix.rfind(',')]

    parts = basename(users_batch_path).replace('.csv', '').split('_')
    batch_name = config.download_dir + f"works_batch_{parts[2]}_{parts[3]}_{suffix}.csv"
    append = True if exists(batch_name) else False
    # endregion

    with open(batch_name, 'ab') as works_batch_file:
        # If the file doesn't exist before or is empty, write the header
        if not append or not (getsize(batch_name) > 0):
            works_batch_file.write((Work().keys() + "\n").encode())

        total_works = 0
        for user in users:
            print(f"********** {user['name']} **********")
            # region Open Selenium browser
            browser = webdriver.Firefox(executable_path=config.driver)
            browser.maximize_window()

            # get user main page
            display_user_page_request(browser, user['page'].first_url())

            # list all works in the user main page
            display_all_user_works_requests(browser)
            # endregion

            works_soup = BeautifulSoup(browser.page_source, 'html.parser')
            total_works += gsc_user_works(works_soup, user, works_batch_file, browser, start_in_work)

            # The start_in_work applies just for the first user
            if start_in_work is not None:
                start_in_work = None

            browser.close()

    print("Total works: ", total_works)


def slice_users(users_batch_path: str, slices: Tuple, start_in_user: int) -> Tuple:
    users = []
    with open(users_batch_path, 'r', encoding='utf8') as file:
        records = len(file.readlines())
        file.seek(0)

        indexes = sliced_indexes(slices, records)

        if start_in_user is not None and start_in_user in indexes:
            indexes = indexes[indexes.index(start_in_user):]

        r = reader(file, delimiter='|')
        for index, row in enumerate(r):
            if index in indexes:
                users.append(User(row[0], row[1], URLFactory(type_=ScholarURLType.CITATIONS_USER, url=row[2]), row[3],
                                  row[4], row[5]))
            elif index > indexes[-1]:
                break

    return tuple(users)


def sliced_indexes(slices: Tuple, records: int) -> Tuple:
    # Initially it's a set to avoid duplicates
    indexes = set()
    if slices:  # If there are elements in the tuple
        for slice_ in slices:
            if type(slice_) is tuple and len(slice_) == 2:  # A tuple of two integers: (1,2)
                if type(slice_[0]) is int and type(slice_[1]) is int and slice_[0] < slice_[1]:
                    from_ = 1 if slice_[0] <= 0 else slice_[0]
                    to = slice_[1] + 1
                    indexes.update(list(range(from_, to)))
                elif type(slice_[0]) is int and type(slice_[1]) is str and slice_[1] == 'inf':
                    from_ = slice_[0]
                    indexes.update(list(range(from_, records)))
            elif type(slice_) is int:  # A single integer: 5
                indexes.add(slice_)

        # When finish, convert the set to a sorted tuple
        indexes = tuple(sorted(list(indexes)))
    else:  # If there aren't elements in the tuple
        indexes = tuple(range(1, records + 1))

    return indexes


def notify(subject: str, message: str) -> None:

    if not config.notify:
        print("--- Notify disabled ---", f"subject: {subject}", f"message: {message}", sep="\n")
        return

    to_address: str = config.notify_to
    password = config.notify_pass
    server = smtplib.SMTP(config.notify_host)
    from_address = config.notify_from
    server.ehlo()
    server.starttls()
    server.login(from_address, password)

    # Send the mail
    body = "\r\n".join([
        f"From: {from_address}",
        f"To: {to_address}",
        f"Subject: {subject}",
        "",
        str(message)
    ])

    server.sendmail(from_address, to_address, body)
    server.quit()


def logging_collector(type_: str, title: str, messages: List) -> None:
    log_name = config.download_dir + f"log_{strftime('%y%m%d')}.txt"

    with open(log_name, 'ab') as log:
        timestamp = datetime.datetime.now().isoformat()
        log.write(f"{timestamp}\t{type_}\t{title}".encode())
        for message in messages:
            log.write(f"\t{message}".encode())
        log.write("\n".encode())


if __name__ == "__main__":
    # Start request ratio counting
    requestmeter.start()
    try:
        # Search keywords
        # kw = '''universidad nacional autonoma de mexico "instituto de ingenieria"'''
        # download_users(kw)
        download_works(config.download_dir + "users_batch_181009_021134.csv", (21,40))
        notify("Batch finished", "The batch finished successfully!")
    except Exception as e:
        trace = traceback.format_exc()
        print(trace)
        notify("There was an error processing the batch", trace.encode('utf-8'))
    finally:
        requestmeter.finish()
        requestmeter.summary()