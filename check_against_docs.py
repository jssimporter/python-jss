#!/usr/bin/env python
# Copyright (C) 2014-2017 Shea G Craig
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""check_against_docs

Scrape the JSS's API documentation page for useful data, and use to
validate python-jss
"""


from selenium import webdriver
from selenium.webdriver.common.action_chains import ActionChains

import jss


def main():
    # The API page is a Swagger UI, mostly Javascript, and so we need
    # to use selenium instead of just doing basic web requests.
    driver = webdriver.Chrome()
    # The page almost never immediately loads, so wait before trying
    # to access elements.
    driver.implicitly_wait(10)
    with open('.test_api_url') as handle:
        url = handle.read()
    driver.get(url)

    # Find the endpoint name elements
    h2s = driver.find_elements_by_css_selector("h2")

    # Convert API page names to a set of singular nouns.
    try:
        h2_names = {i.text.strip("/") for i in h2s}

    finally:
        driver.quit()

    # Get JSSObject names
    classes = (getattr(jss.jssobjects, cls) for cls in jss.jssobjects.__all__)
    jssobjects = {cls._endpoint_path for cls in classes}
    # Get "misc" names
    classes = (getattr(jss.misc_endpoints, cls) for cls in jss.misc_endpoints.__all__)
    jssobjects.update({cls._endpoint_path for cls in classes})
    # Since we cheat and split accounts into Account and AccountGroup
    jssobjects.add('accounts')

    missing = sorted(h2_names.difference(jssobjects))

    print '\n'.join('{:>2}: {}'.format(i, n) for i, n in  enumerate(missing))

    # TODO: Expand all operations so we can chew on the juicy data within.
    #expanders = [i for i in expands if i.text == "Expand Operations"]

    # actions = ActionChains(driver)
    # actions.click(expanders[0])
    # click = actions.click(expanders[0])
    # click.perform()
    # driver.save_screenshot("output.png")

    # TODO: Build tag list of reserved tags to look for collisions with
    # the Element interface or our API.
    # parser = ElementTree.iterparse("/Users/shcrai/Developer/CasperStuff/DA_Casper_Data/all-2.xml")
    # tags = {e.tag for e in parser}
    # tags.difference_update(set(jss.jssobjects.__all__))
    # jssobject_api = set(i for i in dir(getattr(jss.jssobjects, cls)) for cls in jss.jssobjects.__all__)
    # collisions = tags.intersection(jssobject_api)
    # From DA file:
    # set(['url', 'set', 'name', 'id'])

if __name__ == "__main__":
    main()
