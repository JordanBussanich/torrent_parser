# Torrent Parser
# Hacked together by Jordan Bussanich

# Copyright (C) 2023  Jordan Bussanich

# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.

import argparse
import sys
import re

from abc import ABC, abstractmethod
from fastbencode import bencode, bdecode

class Searcher(ABC):
    @abstractmethod
    def search(self, content: str) -> bool:
        return
    
    def __init__(self, search_term: str, case_sensitive: bool) -> None:
        self.search_term = search_term
        self.case_sensitive = case_sensitive


class TextSearcher(Searcher):
    def search(self, content: str) -> bool:
        if self.case_sensitive:
            if self.search_term in content:
                return True
        else:
            if self.search_term.casefold() in str(content).casefold():
                return True
        
        return False

    def __init__(self, search_term: str, case_sensitive: bool) -> None:
        super().__init__(search_term, case_sensitive)


class RegexSearcher(Searcher):
    def search(self, content: str) -> bool:
        return bool(self.regex.match(content))

    def __init__(self, search_term: str, case_sensitive: bool) -> None:
        super().__init__(search_term, case_sensitive)

        if case_sensitive:
            self.regex = re.compile(search_term)
        else:
            self.regex = re.compile(search_term, re.IGNORECASE)       


parser = argparse.ArgumentParser(prog='torrent_parser',
                                 description='This program decodes torrent files and can perform keyword searches against them.')

parser.add_argument('-i', '--input',
                    help='The input Torrent file.',
                    required=True,
                    dest='input_file')

parser.add_argument('-s', '--search-for',
                    help='The text you want to search for.',
                    dest='search_string')

parser.add_argument('-k', '--keyword-list',
                    help='A text file containing a single search term on each line. Do not use -s with -k.',
                    dest='keyword_list')

parser.add_argument( '--regex',
                    action='store_true',
                    help='Search using Regexs.')

parser.add_argument('--case-sensitive',
                    action='store_true',
                    help='Search for a case-sensitive string. Do not use this with --regex.')

parser.add_argument('--show-details',
                    action='store_true',
                    help='Show all of the decoded data, rather than just keyword matches.')