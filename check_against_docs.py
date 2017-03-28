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


import inflect
from selenium import webdriver
from selenium.webdriver.common.action_chains import ActionChains

import jss


def main():
    driver = webdriver.Chrome()
    driver.implicitly_wait(10)
    driver.get("https://casper.taomechworks.net:8443/api")

    # Find the endpoint name elements
    h2s = driver.find_elements_by_css_selector("h2")
    # from selenium.webdriver.common.by import By
    # from selenium.webdriver.support.ui import WebDriverWait
    # from selenium.webdriver.support import expected_conditions as EC

    # try:
    #     element = WebDriverWait(driver, 10).until(
    #         EC.presence_of_element_located((By.ID, 'accounts_endpoint_list')))
    # finally:
    #     driver.quit()

    # Convert API page names to a set of singular nouns.
    try:
        h2_names = {i.text.strip("/") for i in h2s}

    finally:
        driver.quit()

    # p = inflect.engine()
    # jssobjects = {p.plural_noun(i).lower() for i in jss.jssobjects.__all__}
    classes = (getattr(jss.jssobjects, cls) for cls in jss.jssobjects.__all__)
    jssobjects = {cls._endpoint_path for cls in classes}

    # jssobjects = set(jss.jssobjects.__all__)
    # Since we cheat and split accounts into Account and AccountGroup
    jssobjects.add('accounts')

    missing = h2_names.difference(jssobjects)

    print '\n'.join('{:>2}: {}'.format(i, n) for i, n in  enumerate(missing))

    # TODO:
    #expanders = [i for i in expands if i.text == "Expand Operations"]

    # actions = ActionChains(driver)
    # actions.click(expanders[0])
    # click = actions.click(expanders[0])
    # click.perform()
    # driver.save_screenshot("output.png")


if __name__ == "__main__":
    main()
